import pytest

from flask import Flask

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.test_client().post("/api/reset")
    return app.test_client()


def test_map(client):
    r = client.get("/api/map")
    assert r.status_code == 200
    body = r.get_json()
    assert body["cols"] == 12 and body["rows"] == 9
    assert len(body["walls"]) == 4


def test_robot_fields(client):
    r = client.get("/api/robot")
    assert r.status_code == 200
    assert set(r.get_json()) == {"x", "y", "facing", "mode", "note"}


def test_move_bad_action(client):
    r = client.post("/api/robot/move", json={"action": "dance"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "BAD_ACTION"


def test_move_turn_right(client):
    client.post("/api/reset")
    r = client.post("/api/robot/move", json={"action": "turnR"})
    assert r.status_code == 200
    assert r.get_json()["facing"] == "S"     # E 右转 → S


def test_move_forward_ok(client):
    client.post("/api/reset")
    r = client.post("/api/robot/move", json={"action": "forward"})
    assert r.status_code == 200
    assert r.get_json()["x"] == 2


def test_state_shape(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    body = r.get_json()
    assert set(body) == {"robot", "go"}
    assert set(body["go"]) == {"active", "step", "total", "target"}


def test_go_wall_target(client):
    client.post("/api/reset")
    r = client.post("/api/go", json={"target": [3, 2]})   # 默认障碍之一
    assert r.status_code == 409
    # 兼容两种状态：源库返回占位码 CANNOT_GO，打完具身补丁后是 ROUTE_BROKEN
    assert r.get_json()["error"] in ("CANNOT_GO", "ROUTE_BROKEN")


def test_go_bad_target(client):
    r = client.post("/api/go", json={"target": [12, 0]})
    assert r.status_code == 400
    assert r.get_json()["error"] == "BAD_TARGET"


def test_go_malformed(client):
    r = client.post("/api/go", json={"target": "abc"})
    assert r.status_code == 400


def test_stop_when_not_going(client):
    client.post("/api/reset")
    r = client.post("/api/stop")
    assert r.status_code == 409
    assert r.get_json()["error"] == "NOT_GOING"


def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["Content-Type"]
