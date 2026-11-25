import pytest

from game import World, E_OUT_OF_RANGE, E_HIT_WALL


def make_world(walls=None):
    import game as g
    w = World()
    if walls is not None:
        pytest_monkeypatch_walls(w, walls)
    return w


def pytest_monkeypatch_walls(w, walls):
    # World.do / find_route 都读模块级 WALLS；这里直接改模块变量
    import game as g
    g.WALLS = set(walls)


def test_forward_moves_one_cell():
    import game as g
    saved = g.WALLS
    g.WALLS = set()
    try:
        w = World()
        ok, err = w.do("forward")        # (1,1) 朝 E → (2,1)
        assert ok is True and err is None
        assert (w.robot.x, w.robot.y) == (2, 1)
        assert w.robot.mode == "free"
    finally:
        g.WALLS = saved


def test_turn_left_from_east_faces_north():
    w = World()
    ok, _ = w.do("turnL")                # E 左转 → N
    assert ok is True
    assert w.robot.facing == "N"
    assert (w.robot.x, w.robot.y) == (1, 1)   # 转向不位移


def test_back_moves_opposite_and_keeps_facing():
    import game as g
    saved = g.WALLS
    g.WALLS = set()
    try:
        w = World()
        w.robot.x = 3
        ok, err = w.do("back")           # 朝 E，后退向 W → (2,1)
        assert ok is True and err is None
        assert (w.robot.x, w.robot.y) == (2, 1)
        assert w.robot.facing == "E"
    finally:
        g.WALLS = saved


def test_out_of_range_blocks(monkeypatch):
    import game as g
    monkeypatch.setattr(g, "WALLS", set())
    w = World()
    w.robot.x = 11                       # 最右一列
    ok, err = w.do("forward")
    assert ok is False and err == E_OUT_OF_RANGE
    assert (w.robot.x, w.robot.y) == (11, 1)
    assert w.robot.mode == "blocked"


def test_hit_wall_blocks(monkeypatch):
    import game as g
    monkeypatch.setattr(g, "WALLS", {(2, 1)})
    w = World()
    ok, err = w.do("forward")            # (1,1) 朝 E，(2,1) 是墙
    assert ok is False and err == E_HIT_WALL
    assert (w.robot.x, w.robot.y) == (1, 1)
    assert w.robot.mode == "blocked"


def test_turn_clears_blocked():
    w = World()
    w.robot.mode = "blocked"
    w.do("turnL")
    assert w.robot.mode == "free"        # 成功动作恢复 free


def test_bad_action():
    w = World()
    ok, err = w.do("dance")
    assert ok is False and err == "BAD_ACTION"
