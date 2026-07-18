import os

import pytest
from fastapi.testclient import TestClient

import app.main as main


def test_servers_endpoint_reads_from_postgres():
    if os.getenv("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Integration tests are disabled. Set RUN_INTEGRATION_TESTS=1 to enable.")

    with TestClient(main.app) as client:
        response = client.get("/servers/?limit=1")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "hostname" in data[0]
