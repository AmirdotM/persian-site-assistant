"""FastAPI application entry point and runtime lifecycle."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from openai import APIError

from site_assistant import __version__
from site_assistant.api.rate_limit import SlidingWindowRateLimiter
from site_assistant.api.routes import router
from site_assistant.config import settings
from site_assistant.generation.client import LLMClient
from site_assistant.generation.service import ChatService
from site_assistant.retrieval.embeddings import E5Embedder
from site_assistant.retrieval.retriever import Retriever
from site_assistant.retrieval.vector_store import NumpyVectorStore

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEBSITE_DIR = PROJECT_ROOT / "website"
WIDGET_DIR = PROJECT_ROOT / "widget"


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
    docs_url=None if settings.public_demo_mode else "/docs",
    redoc_url=None if settings.public_demo_mode else "/redoc",
    openapi_url=None if settings.public_demo_mode else "/openapi.json",
)
app.state.chat_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.public_demo_rate_limit_per_minute
)


@app.middleware("http")
async def add_request_id_and_security_headers(request: Request, call_next):
    """Attach a request ID and conservative browser security headers."""
    request_id = uuid4().hex
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
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


# In native mode, serve the static site and widget from this same origin as
# /api/v1. The container deployment keeps serving these assets from Nginx.
if WEBSITE_DIR.is_dir() and WIDGET_DIR.is_dir():
    app.mount(
        "/website",
        StaticFiles(directory=WEBSITE_DIR, html=True),
        name="website",
    )
    app.mount(
        "/widget",
        StaticFiles(directory=WIDGET_DIR),
        name="widget",
    )

    @app.get("/", include_in_schema=False)
    async def website_home() -> RedirectResponse:
        """Send browsers to the Persian demo website."""
        return RedirectResponse(url="/website/", status_code=307)
