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
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from site_assistant import __version__
from site_assistant.api.routes import router
from site_assistant.config import settings
from site_assistant.generation.client import LLMClient
from site_assistant.generation.service import ChatService
from site_assistant.retrieval.embeddings import E5Embedder
from site_assistant.retrieval.retriever import Retriever
from site_assistant.retrieval.vector_store import NumpyVectorStore


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # initialize the vector store
    vector_store = NumpyVectorStore.load(settings.data_dir / "index" / "vector_store.npz")

    # initialize the embedder
    embedder = E5Embedder(model_name=settings.embedding_model, device=settings.embedding_device)

    # initialize the retriever  
    retriever = Retriever(vector_store=vector_store, embedder=embedder)

    # initialize the LLM client
    llm_client = LLMClient()
        
    
    #connect the chat service
    chat_service = ChatService(retriever=retriever, llm=llm_client)

    # attach the chat service to the app state
    app.state.chat_service = chat_service




    yield


    #colse the LLM client cleanly
    await llm_client.close()
    




    







app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Persian-first website assistant API. The chat pipeline is under development.",
    lifespan=lifespan
)






app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(router, prefix=settings.api_prefix)

#health endpoint for local checks and deployment probes
@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Simple health endpoint for local checks and deployment probes."""
    return {"status": "ok", "version": __version__}

#readiness endpoint for external checks of the chat service
@app.get("/ready", tags=["health"])
async def ready() -> dict[str, str]:
    """Simple readiness endpoint for external checks of the chat service."""
    chat_service = getattr(app.state, "chat_service", None)
    if chat_service is None:
        return {"status": "not ready", "version": __version__} 
    elif not chat_service.is_ready():
        return {"status": "not ready", "version": __version__}
    else:
        return {"status": "ok", "version": __version__}
