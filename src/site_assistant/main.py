"""FastAPI application entry point.

TODO: Initialize and release the RAG services through the FastAPI lifespan.
See IMPLEMENTATION_PLAN.md for the full acceptance criteria.

Startup checklist:
- Load and validate the persisted vector store from the configured index path.
- Initialize E5Embedder with the same model/device used to build the index.
- Construct Retriever, LLMClient, and ChatService.
- Attach the ready service to app.state.chat_service (the chat route reads this).
- Expose readiness separately from process liveness; a healthy process without an
  index or provider configuration must not appear chat-ready.

Shutdown checklist:
- Close the async LLM client cleanly when the application stops.
- Keep startup failures explicit and actionable; do not silently swallow them.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from site_assistant import __version__
from site_assistant.api.routes import router
from site_assistant.config import settings

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Persian-first website assistant API. The chat pipeline is under development.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Simple health endpoint for local checks and deployment probes."""
    return {"status": "ok", "version": __version__}
