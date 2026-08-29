from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_session():
    response = client.post("/api/v1/sessions")

    assert response.status_code == 200

    data = response.json()

    assert "session_token" in data
    assert data["status"] == "active"