from fastapi.testclient import TestClient
from web_server.main import app

client = TestClient(app)


def test_get_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "ok"}


def test_post_hello() -> None:
    response = client.post("/hello", json={"name": "alice"})
    assert response.status_code == 200
    assert response.json() == {"msg": "hello alice"}


def test_post_hello_rejects_extra_fields() -> None:
    response = client.post("/hello", json={"name": "alice", "extra": "x"})
    assert response.status_code == 422
