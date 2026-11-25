"""游戏核心：地图、机器人、前往（go-to）执行层。

设计坐标点（演示和修改时用得上）：
- 地图 12×9，障碍格 WALLS —— 演示者可自行修改这几个格子
- 朝向用字符 N/E/S/W，转向直接换字符，全程无角度计算
- go-to：指定目标格 → 广度优先找最短路线 → 后台线程逐步走，到达即停
- 全部共享状态由一把锁（LOCK）保护，Flask 的每个请求入口都走这把锁

异常处理现状（具身智能方向任务的起点，完成步骤见 EMBODIED-TASK.md）：
本版本有两处异常处理未完成——
  ① go-to 进行中，手动移动不会被拦截（会让机器人行为异常）
  ② go_to 遇到不可达目标时，只返回通用错误 CANNOT_GO，没有明确告知原因
完成这两处异常处理 = 具身智能方向任务。
"""
import threading
import time

# ---------------- 地图 ----------------
COLS, ROWS = 12, 9
WALLS = {(3, 2), (3, 3), (7, 5), (8, 5)}   # ← 演示者可修改

DIRS = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
TURN_LEFT = {"N": "W", "W": "S", "S": "E", "E": "N"}
TURN_RIGHT = {"N": "E", "E": "S", "S": "W", "W": "N"}
CHAR_OF_STEP = {(0, -1): "N", (1, 0): "E", (0, 1): "S", (-1, 0): "W"}

# ---------------- 错误码（本项目自创命名） ----------------
E_BAD_ACTION = "BAD_ACTION"
E_BAD_TARGET = "BAD_TARGET"
E_OUT_OF_RANGE = "OUT_OF_RANGE"
E_HIT_WALL = "HIT_WALL"
E_GO_BUSY = "GO_BUSY"                # ← 补丁一启用
E_ROUTE_BROKEN = "ROUTE_BROKEN"      # ← 补丁二启用
CANNOT_GO = "CANNOT_GO"              # 源库的通用占位错误（补丁二替换它）
E_NOT_GOING = "NOT_GOING"

STEP_SECONDS = 0.6                   # go-to 每步间隔


def inside(x, y):
    return 0 <= x < COLS and 0 <= y < ROWS


class Robot:
    """机器人：位置、朝向、模式。所有修改都在持锁状态下发生。"""

    def __init__(self):
        self.x, self.y = 1, 1
        self.facing = "E"
        self.mode = "free"           # free（可手动控制）/ going（前往中）/ blocked（受阻）

    def snapshot(self):
        return {"x": self.x, "y": self.y, "facing": self.facing, "mode": self.mode}


class World:
    """单机器人世界：持有机器人、go-to 线程与全部共享状态。"""

    def __init__(self):
        self.robot = Robot()
        self.LOCK = threading.Lock()
        self.go_thread = None
        self.go_state = None         # {"route": [...], "step": n, "target": [x,y]}

    # ---- 手动控制 ----
    def do(self, action):
        """执行手动指令。返回 (成功?, 错误码或 None)。"""
        with self.LOCK:
            r = self.robot
            if action not in ("forward", "back", "turnL", "turnR"):
                return False, E_BAD_ACTION
            # ★ 补丁一（EMBODIED-TASK.md 第 2 步）在这行注释之后插入 ★
            if action == "turnL":
                r.facing = TURN_LEFT[r.facing]
                r.mode = "free"
                return True, None
            if action == "turnR":
                r.facing = TURN_RIGHT[r.facing]
                r.mode = "free"
                return True, None
            dx, dy = DIRS[r.facing]
            nx, ny = (r.x - dx, r.y - dy) if action == "back" else (r.x + dx, r.y + dy)
            if not inside(nx, ny):
                r.mode = "blocked"
                return False, E_OUT_OF_RANGE
            if (nx, ny) in WALLS:
                r.mode = "blocked"
                return False, E_HIT_WALL
            r.x, r.y = nx, ny
            r.mode = "free"
            return True, None

    def blocked_note(self):
        """受阻时给前端的中文提示；下一次成功动作会自动恢复 free。"""
        if self.robot.mode == "blocked":
            return "撞上了，机器人原地停留"
        return ""

    # ---- 寻路 ----
    def find_route(self, start, goal):
        """广度优先最短路线（含两端）；不通返回 None。目标本身是墙或出界也算不通。"""
        if goal in WALLS or not inside(*goal):
            return None
        frontier = [start]
        parent = {start: None}
        while frontier:
            cur = frontier.pop(0)                 # 先进先出 → 广度优先
            if cur == goal:
                route = []
                while cur:
                    route.append(cur)
                    cur = parent[cur]
                return route[::-1]
            x, y = cur
            for dx, dy in DIRS.values():
                nxt = (x + dx, y + dy)
                if inside(*nxt) and nxt not in WALLS and nxt not in parent:
                    parent[nxt] = cur
                    frontier.append(nxt)
        return None

    # ---- 前往（go-to） ----
    def go_to(self, target):
        """规划到 target 的路线并启动后台线程。返回 (成功?, 错误码或 None)。"""
        with self.LOCK:
            route = self.find_route((self.robot.x, self.robot.y), target)
            if route is None:
                # ★ 补丁二（EMBODIED-TASK.md 第 3 步）：把下面这行的 CANNOT_GO 换成 E_ROUTE_BROKEN ★
                return False, CANNOT_GO
            self.robot.mode = "going"
            self.go_state = {"route": route, "step": 0, "target": list(target)}

        def run():
            t = threading.current_thread()
            while getattr(t, "keep", True):
                time.sleep(STEP_SECONDS)
                with self.LOCK:
                    st = self.go_state
                    if st is None or not getattr(t, "keep", True):
                        return
                    st["step"] += 1
                    r = self.robot
                    nxt = tuple(st["route"][st["step"]])
                    r.facing = CHAR_OF_STEP[(nxt[0] - r.x, nxt[1] - r.y)]
                    r.x, r.y = nxt
                    r.mode = "going"
                    if st["step"] >= len(st["route"]) - 1:
                        r.mode = "free"
                        self.go_state = None
                        return

        t = threading.Thread(target=run, daemon=True)
        t.keep = True
        self.go_thread = t
        t.start()
        return True, None

    def stop_go(self):
        """手动取消前往任务。返回是否真的取消了什么。"""
        with self.LOCK:
            if self.go_state is None:
                return False
            if self.go_thread is not None:
                self.go_thread.keep = False
            self.robot.mode = "free"
            self.go_state = None
            return True

    def go_snapshot(self):
        with self.LOCK:
            st = self.go_state
            if st is None:
                return {"active": False, "step": 0, "total": 0, "target": None}
            return {"active": True, "step": st["step"], "total": len(st["route"]),
                    "target": st["target"]}

    def reset(self):
        with self.LOCK:
            if self.go_thread is not None:
                self.go_thread.keep = False
            self.go_thread = None
            self.go_state = None
            self.robot = Robot()


# 全局唯一世界（Flask 每个请求都在独立线程里处理，所有入口都走 World.LOCK）
world = World()
