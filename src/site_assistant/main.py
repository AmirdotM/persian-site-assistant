"""FastAPI application entry point and runtime lifecycle."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import APIError

from site_assistant import __version__
from site_assistant.api.routes import router
from site_assistant.config import settings
from site_assistant.generation.client import LLMClient
from site_assistant.generation.service import ChatService
from site_assistant.retrieval.embeddings import E5Embedder
from site_assistant.retrieval.retriever import Retriever
from site_assistant.retrieval.vector_store import NumpyVectorStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load RAG components at startup and release the LLM client at shutdown."""
    llm_client: LLMClient | None = None
    app.state.chat_service = None

    try:
        vector_store = NumpyVectorStore.load(
            settings.data_dir / "index" / "vector_store.npz"
        )
        embedder = E5Embedder(
            model_name=settings.embedding_model,
            device=settings.embedding_device,
        )
        retriever = Retriever(
            vector_store=vector_store,
            embedder=embedder,
        )
        llm_client = LLMClient()
        app.state.chat_service = ChatService(
            retriever=retriever,
            llm=llm_client,
        )
        yield
    finally:
        app.state.chat_service = None
        if llm_client is not None:
            await llm_client.close()


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Persian-first website assistant API powered by retrieval-augmented generation.",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Attach a server-generated ID to each request for support and log correlation."""
    request_id = uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(APIError)
async def handle_llm_provider_error(request: Request, exc: APIError) -> JSONResponse:
    """Return a safe, consistent response when the upstream LLM provider fails."""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "LLM provider request failed (request_id=%s, error_type=%s)",
        request_id,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=502,
        content={
            "detail": "سرویس تولید پاسخ موقتاً در دسترس نیست. لطفاً کمی بعد دوباره تلاش کنید.",
            "request_id": request_id,
        },
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
    """Report that the API process is alive."""
    return {"status": "ok", "version": __version__}


@app.get("/ready", tags=["health"])
async def ready(request: Request) -> dict[str, str]:
    """Report whether the RAG chat service completed startup."""
    if getattr(request.app.state, "chat_service", None) is None:
        raise HTTPException(
            status_code=503,
            detail="Chat service is unavailable",
        )
    return {"status": "ready", "version": __version__}
