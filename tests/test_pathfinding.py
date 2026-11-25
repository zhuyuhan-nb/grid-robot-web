import game as g
from game import World


def test_empty_map_shortest_is_manhattan(monkeypatch):
    monkeypatch.setattr(g, "WALLS", set())
    w = World()
    p = w.find_route((0, 0), (3, 2))
    assert p is not None
    assert p[0] == (0, 0) and p[-1] == (3, 2)
    assert len(p) == 3 + 2 + 1           # 空地图 BFS 首达即最短 = 曼哈顿距离 + 1


def test_detours_around_wall(monkeypatch):
    monkeypatch.setattr(g, "WALLS", {(1, 0)})
    w = World()
    p = w.find_route((0, 0), (2, 0))
    assert p is not None
    assert (1, 0) not in p               # 必须绕开
    assert len(p) == 5                   # 直达 2 步被堵，绕行多走 2 步 = 4 步 = 5 格
    for a, b in zip(p, p[1:]):           # 相邻两步都是一格移动
        assert abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


def test_goal_is_wall_returns_none(monkeypatch):
    monkeypatch.setattr(g, "WALLS", {(2, 2)})
    w = World()
    assert w.find_route((0, 0), (2, 2)) is None


def test_walled_off_returns_none(monkeypatch):
    monkeypatch.setattr(g, "WALLS", {(1, y) for y in range(g.ROWS)})   # 整列墙
    w = World()
    assert w.find_route((0, 0), (3, 0)) is None


def test_start_equals_goal(monkeypatch):
    monkeypatch.setattr(g, "WALLS", set())
    w = World()
    assert w.find_route((2, 2), (2, 2)) == [(2, 2)]
