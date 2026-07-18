from fastapi.testclient import TestClient

import app.main as main


def test_health_endpoint_returns_ok(monkeypatch):
    async def fake_create_pool():
        return None

    async def fake_close_pool():
        return None

    monkeypatch.setattr(main, "create_pool", fake_create_pool)
    monkeypatch.setattr(main, "close_pool", fake_close_pool)

    with TestClient(main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint_returns_api_message(monkeypatch):
    async def fake_create_pool():
        return None

    async def fake_close_pool():
        return None

    monkeypatch.setattr(main, "create_pool", fake_create_pool)
    monkeypatch.setattr(main, "close_pool", fake_close_pool)

    with TestClient(main.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Server Management API" in response.json()["message"]
