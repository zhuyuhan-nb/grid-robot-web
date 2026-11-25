import time

import game as g
import pytest

from game import World


@pytest.fixture
def fast_step(monkeypatch):
    monkeypatch.setattr(g, "STEP_SECONDS", 0.01)


def test_go_to_starts_and_arrives(fast_step, monkeypatch):
    monkeypatch.setattr(g, "WALLS", set())
    w = World()
    ok, err = w.go_to((2, 1))            # (1,1) → (2,1)，一步
    assert ok is True and err is None
    assert w.robot.mode == "going"
    snap = w.go_snapshot()
    assert snap["active"] is True and snap["total"] == 2
    time.sleep(0.15)                     # 步进间隔 0.01s，足够走完
    assert w.robot.mode == "free"
    assert (w.robot.x, w.robot.y) == (2, 1)
    assert w.go_snapshot()["active"] is False


def test_stop_go_cancels(fast_step, monkeypatch):
    monkeypatch.setattr(g, "WALLS", set())
    w = World()
    w.go_to((11, 8))                     # 远目标，短时间内走不完
    assert w.stop_go() is True
    assert w.robot.mode == "free"
    assert w.go_snapshot()["active"] is False
    assert w.stop_go() is False          # 已经没有任务可取消


def test_go_to_wall_target():
    w = World()
    ok, err = w.go_to((3, 2))            # 默认障碍之一
    assert ok is False
    # 兼容两种状态：源库占位码 CANNOT_GO；具身补丁后是 ROUTE_BROKEN
    assert err in ("CANNOT_GO", "ROUTE_BROKEN")


def test_go_to_out_of_map():
    w = World()
    ok, err = w.go_to((12, 0))
    assert ok is False
    assert err in ("CANNOT_GO", "ROUTE_BROKEN")


def test_reset_clears_everything(fast_step, monkeypatch):
    monkeypatch.setattr(g, "WALLS", set())
    w = World()
    w.go_to((5, 5))
    w.reset()
    assert w.robot.mode == "free"
    assert w.go_snapshot()["active"] is False
