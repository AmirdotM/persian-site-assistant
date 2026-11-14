"""Tests for the public API contract and operational error handling."""

import httpx
from fastapi.testclient import TestClient
from openai import APIConnectionError

from site_assistant.main import app
from site_assistant.schemas import ChatResponse

client = TestClient(app)


def test_health_endpoint_includes_request_id() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["x-request-id"]


def test_chat_endpoint_is_explicitly_unavailable_before_service_setup() -> None:
    response = client.post("/api/v1/chat", json={"message": "سلام"})

    assert response.status_code == 503


def test_chat_rejects_whitespace_only_messages() -> None:
    response = client.post("/api/v1/chat", json={"message": "   "})

    assert response.status_code == 422


def test_successful_chat_response_contains_request_id(monkeypatch) -> None:
    class FakeChatService:
        async def answer(self, question: str, session_id: str | None = None) -> ChatResponse:
            assert question == "سلام"
            assert session_id is None
            return ChatResponse(answer="درود")

    monkeypatch.setattr(app.state, "chat_service", FakeChatService(), raising=False)

    response = client.post("/api/v1/chat", json={"message": "  سلام  "})

    assert response.status_code == 200
    assert response.json()["answer"] == "درود"
    assert response.json()["request_id"] == response.headers["x-request-id"]


def test_llm_provider_failure_returns_safe_error(monkeypatch) -> None:
    class BrokenChatService:
        async def answer(self, question: str, session_id: str | None = None) -> ChatResponse:
            request = httpx.Request("POST", "https://provider.example.test/v1/chat")
            raise APIConnectionError(message="sensitive upstream details", request=request)

    monkeypatch.setattr(app.state, "chat_service", BrokenChatService(), raising=False)

    response = client.post("/api/v1/chat", json={"message": "سلام"})

    assert response.status_code == 502
    assert response.json()["request_id"] == response.headers["x-request-id"]
    assert "سرویس تولید پاسخ" in response.json()["detail"]
    assert "sensitive upstream details" not in response.text
