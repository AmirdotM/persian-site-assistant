from fastapi.testclient import TestClient

from site_assistant.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint_is_explicitly_unavailable_before_service_setup() -> None:
    response = client.post("/api/v1/chat", json={"message": "سلام"})
    assert response.status_code == 503
