"""FastAPI application entry point."""

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
