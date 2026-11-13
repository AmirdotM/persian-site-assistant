
from fastapi.testclient import TestClient

import site_assistant.main as main


class FakeLLMClient:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


def test_lifespan(monkeypatch):
    """Test startup and shutdown without loading real models."""

    fake_llm = FakeLLMClient()

    class FakeVectorStore:
        @classmethod
        def load(cls, path):
            return object()

    # Replace expensive components with lightweight test doubles.
    monkeypatch.setattr(main, "NumpyVectorStore", FakeVectorStore)
    monkeypatch.setattr(main, "E5Embedder", lambda **kwargs: object())
    monkeypatch.setattr(main, "Retriever", lambda **kwargs: object())
    monkeypatch.setattr(main, "LLMClient", lambda: fake_llm)
    monkeypatch.setattr(main, "ChatService", lambda **kwargs: object())

    with TestClient(main.app) as client:

        # Startup should have initialized the service.
        assert main.app.state.chat_service is not None

        # Readiness should now report success.
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

        # Health should also work.
        response = client.get("/health")
        assert response.status_code == 200

    # Shutdown should clean up the application state.
    
    assert main.app.state.chat_service is None
    

    # The underlying LLM client should have been closed.
    assert fake_llm.closed is True
