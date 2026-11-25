# grid-robot-web

巡逻机器人二维仿真 · 基础版（Web + Flask）。

- 地图 12×9，障碍格见 `game.py` 的 `WALLS`
- 方向键 / WASD / 屏幕按钮手动移动；点击地图任意格子让机器人**自动前往**
- 前往途中手动控制会被锁定（异常处理守卫，具身智能方向任务）
- 目标不可达（被障碍围死）时给出明确提示（异常处理守卫）
- 状态条 500ms 轮询刷新；pytest 全覆盖；GitHub Actions 自动跑测试；Docker 一键部署

## 本地运行

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows（Linux/Mac: source .venv/bin/activate）
pip install -r requirements.txt
python app.py                     # 打开 http://127.0.0.1:5000
```

## 测试

```bash
python -m pytest tests/ -v
```

`test_guard.py` 是具身智能方向任务的验收测试——按 `EMBODIED-TASK.md` 完成两处补丁后删除文件首行的 skip 标记，测试即转绿。

## Docker

```bash
docker build -t grid-robot-web .
docker run -d --name robot -p 5000:5000 grid-robot-web
# 打开 http://localhost:5000 ；停止：docker rm -f robot
```

## 提交的镜像地址

<!-- 结业前填写：docker push 后把这行下面的占位替换成真实地址 -->
`ghcr.io/<你的用户名>/grid-robot-web:latest`

## 验收对照（基础版 7 项）

| 验收项 | 位置 |
| --- | --- |
| Web 界面与二维地图 | 打开页面即见 12×9 网格与障碍 |
| 后端 API | `GET /api/map`、`GET /api/robot`、`POST /api/robot/move` |
| 手动控制 | 方向键 / WASD / 按钮，越界保持原地 |
| 状态反馈 | 状态条与 API 返回一致（500ms 轮询）|
| Git 版本管理 | 本仓库提交历史 |
| 基础 CI | GitHub Actions：push 自动跑 pytest |
| Docker 部署 | 上面的 build/run 命令与镜像地址 |
