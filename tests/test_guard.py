"""具身智能方向任务 · 验收测试。

按 EMBODIED-TASK.md 完成两处补丁后，删除下面这一行 skip 标记，
然后运行 pytest——本文件的两个用例应当变绿。
"""
import pytest

from game import World, E_GO_BUSY, E_ROUTE_BROKEN
import game as g

pytestmark = pytest.mark.skip(reason="具身方向任务未完成：按 EMBODIED-TASK.md 打完两处补丁后删除本行")


def test_go_busy_blocks_manual(monkeypatch):
    """补丁一：前往途中，手动移动必须被 GO_BUSY 拦截。"""
    monkeypatch.setattr(g, "STEP_SECONDS", 0.01)
    monkeypatch.setattr(g, "WALLS", set())
    w = World()
    ok, _ = w.go_to((11, 8))             # 远目标，短时间内走不完
    assert ok is True
    ok2, err2 = w.do("forward")          # 前往途中手动移动
    assert ok2 is False
    assert err2 == E_GO_BUSY
    w.stop_go()


def test_unreachable_reports_route_broken(monkeypatch):
    """补丁二：目标被围死时，必须返回 ROUTE_BROKEN（不是 CANNOT_GO）。"""
    w = World()
    monkeypatch.setattr(g, "WALLS", {(2, 0), (4, 0), (3, 1)})   # (3,0) 三面被围 + 顶边界
    ok, err = w.go_to((3, 0))
    assert ok is False
    assert err == E_ROUTE_BROKEN
