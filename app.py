"""HTTP 壳层（Flask）。

本地运行：python app.py   →   http://127.0.0.1:5000
"""
from flask import Flask, jsonify, request, send_from_directory

from game import (world, E_BAD_ACTION, E_BAD_TARGET, E_OUT_OF_RANGE, E_HIT_WALL,
                  E_GO_BUSY, E_ROUTE_BROKEN, CANNOT_GO, E_NOT_GOING,
                  COLS, ROWS, WALLS, inside)

app = Flask(__name__, static_folder="static")

# 错误码 → 中文提示。CANNOT_GO / GO_BUSY / ROUTE_BROKEN 三个键
# 与 EMBODIED-TASK.md 的补丁一一对应：补丁打上后它们才会真正被触发。
MSG = {
    E_BAD_ACTION: "不认识的指令",
    E_OUT_OF_RANGE: "已经到边界啦，机器人停在原地",
    E_HIT_WALL: "前方是障碍物，机器人保持原位",
    CANNOT_GO: "无法前往该点",
    E_GO_BUSY: "前往途中，手动控制暂时锁定",
    E_ROUTE_BROKEN: "目标不可达（被障碍围死），本次前往已取消",
    E_NOT_GOING: "当前没有前往任务",
    E_BAD_TARGET: "目标格子不合法",
}


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/map")
def api_map():
    return jsonify(cols=COLS, rows=ROWS, walls=sorted(list(w) for w in WALLS))


@app.get("/api/robot")
def api_robot():
    s = world.robot.snapshot()
    s["note"] = world.blocked_note()
    return jsonify(s)


@app.get("/api/state")
def api_state():
    """前端轮询用：机器人状态 + go-to 进度一次拿全。"""
    s = world.robot.snapshot()
    s["note"] = world.blocked_note()
    return jsonify(robot=s, go=world.go_snapshot())


@app.post("/api/robot/move")
def api_move():
    body = request.get_json(silent=True) or {}
    ok, err = world.do(body.get("action", ""))
    if not ok:
        code = err if err in MSG else E_BAD_ACTION
        status = 400 if code == E_BAD_ACTION else 409
        return jsonify(error=code, message=MSG[code]), status
    s = world.robot.snapshot()
    s["note"] = world.blocked_note()
    return jsonify(s)


@app.post("/api/go")
def api_go():
    body = request.get_json(silent=True) or {}
    target = body.get("target")
    if (not isinstance(target, list) or len(target) != 2
            or not all(isinstance(v, int) for v in target)
            or not inside(target[0], target[1])):
        return jsonify(error=E_BAD_TARGET, message=MSG[E_BAD_TARGET]), 400
    ok, err = world.go_to(tuple(target))
    if not ok:
        code = err if err in MSG else CANNOT_GO
        return jsonify(error=code, message=MSG[code]), 409
    return jsonify(world.go_snapshot())


@app.post("/api/stop")
def api_stop():
    if not world.stop_go():
        return jsonify(error=E_NOT_GOING, message=MSG[E_NOT_GOING]), 409
    return jsonify(world.robot.snapshot())


@app.post("/api/reset")
def api_reset():
    world.reset()
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
