"""Tests for FastAPI startup and shutdown."""

from fastapi.testclient import TestClient

import site_assistant.main as main


class FakeLLMClient:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


def test_lifespan_initializes_the_chat_service_and_closes_the_client(monkeypatch) -> None:
    """Keep the lifecycle test independent of the E5 model and provider API."""
    fake_llm = FakeLLMClient()

    class FakeVectorStore:
        @classmethod
        def load(cls, path):
            return object()

    monkeypatch.setattr(main, "NumpyVectorStore", FakeVectorStore)
    monkeypatch.setattr(main, "E5Embedder", lambda **kwargs: object())
    monkeypatch.setattr(main, "Retriever", lambda **kwargs: object())
    monkeypatch.setattr(main, "LLMClient", lambda: fake_llm)
    monkeypatch.setattr(main, "ChatService", lambda **kwargs: object())

    with TestClient(main.app) as client:
        assert main.app.state.chat_service is not None
        assert client.get("/ready").status_code == 200
        assert client.get("/health").status_code == 200

    assert main.app.state.chat_service is None
    assert fake_llm.closed is True
