# 具身智能方向任务 · 补丁粘贴单

> 你的方向任务 = **简单异常处理**。本仓库已经能跑，但有两处异常没有处理——
> 你的工作是把下面两段代码按位置粘贴进去，让验收测试转绿。全程约 8 分钟。

## 开始前（1 分钟）

```bash
# clone 你的 fork 之后：
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

你会看到：**大部分绿，`test_guard.py` 的 2 个用例是 skip（被跳过）**。
这就是你的任务——打完两处补丁、删掉 skip 标记后，它们要变绿。

---

## 补丁一 · 前往途中锁定手动控制（约 5 行）

**问题**：机器人正在自动前往目标点时，你仍然可以手动移动它——它会先被线程
拉回路线，又被你挪走，行为错乱。这是缺少异常处理：**前往途中必须拒绝手动移动**。

**位置**：打开 `game.py`，找到 `do` 方法里的这一行注释（约第 60 行）：

```python
            # ★ 补丁一（EMBODIED-TASK.md 第 2 步）在这行注释之后插入 ★
```

**在这行注释的下面粘贴**：

```python
            if r.mode == "going":
                return False, E_GO_BUSY
```

保存。粘贴后的样子（核对缩进，与上下行对齐，12 个空格）：

```python
            if action not in ("forward", "back", "turnL", "turnR"):
                return False, E_BAD_ACTION
            # ★ 补丁一（EMBODIED-TASK.md 第 2 步）在这行注释之后插入 ★
            if r.mode == "going":
                return False, E_GO_BUSY
            if action == "turnL":
```

---

## 补丁二 · 目标不可达要明确告知（改 1 个词）

**问题**：点击一个被障碍围死的格子，机器人只返回笼统的 `CANNOT_GO`——
用户不知道为什么去不了。异常处理要求**把原因说清楚**。

**位置**：`game.py` 的 `go_to` 方法里找到这一行（约第 128 行，上面有 ★ 注释）：

```python
                return False, CANNOT_GO
```

**把它改成**：

```python
                return False, E_ROUTE_BROKEN
```

（只改这一个词。改完 `game.py` 里就没有任何地方引用 `CANNOT_GO` 了。）

---

## 补丁三 · 解除验收测试的封印（删 1 行）

打开 `tests/test_guard.py`，把文件里的这一行**整行删掉**：

```python
pytestmark = pytest.mark.skip(reason="具身方向任务未完成：按 EMBODIED-TASK.md 打完两处补丁后删除本行")
```

---

## 验证（2 分钟）

```bash
python -m pytest tests/ -v
```

**预期**：没有任何 skip，全部通过（PASSED）。特别是：

- `test_guard.py::test_go_busy_blocks_manual` ✅
- `test_guard.py::test_unreachable_reports_route_broken` ✅

不绿再核对：补丁一的缩进是否 12 个空格、补丁二是否只改了一个词、skip 行是否删干净。
仍不行就贴报错原文给学长。

---

## 收尾（剩下的提交与部署动作）

1. **个性化**（可选但推荐）：`game.py` 顶部的 `WALLS` 换成你自己的 4 个格子
   （别贴边、别相连），`README.md` 第一行加一句你自己写的项目简介
2. **提交**：
   ```bash
   git add -A
   git commit -m "feat: 具身方向任务——异常处理守卫（前往锁定 + 不可达反馈）"
   git push
   ```
   （以后每次改动单独提交，前缀用 feat / fix / docs）
3. **Docker 镜像**（老师要的交付形态）：
   ```bash
   docker login ghcr.io -u <你的GitHub用户名>
   # 密码粘贴你的 PAT（必须勾选 write:packages 权限）
   docker build -t ghcr.io/<你的GitHub用户名>/grid-robot-web:latest .
   docker push ghcr.io/<你的GitHub用户名>/grid-robot-web:latest
   ```
4. **自证**（学长教的：验证远端不是本地）：
   ```bash
   docker rmi ghcr.io/<你的GitHub用户名>/grid-robot-web:latest
   docker pull ghcr.io/<你的GitHub用户名>/grid-robot-web:latest
   ```
   pull 成功 = 任何人都能拉到你的镜像。把镜像地址写进 `README.md` 的「提交的镜像地址」一节，再 commit 一次。

## 演示口径（老师问起就这么说）

「基础实现由 AI 辅助生成，异常处理守卫和地图是我完成的，测试和部署我自己跑通的。
前往途中手动锁定、不可达明确反馈，这两处异常处理就是我的方向任务。」
