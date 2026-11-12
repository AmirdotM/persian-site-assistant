# Project Notes

Last reviewed: 2026-11-12

## Goal

I'm building a Persian-first website support assistant that can be embedded as a small RTL chat widget. It should answer questions from a site's own content, use a hosted LLM for generation, and show the sources behind its answers.

## Stack and dependencies

- Python 3.11+; FastAPI, base Uvicorn (HTTP-only demo), and Pydantic
- NumPy for vector search and persistence (`vector` extra)
- `intfloat/multilingual-e5-small` using Sentence Transformers (`embeddings` extra)
- OpenAI-compatible API for hosted LLM generation
- Vanilla JavaScript and CSS for the embeddable widget
- pytest and Ruff (`dev` extra)

CI installs `.[dev,vector]`: it needs NumPy for vector-store tests but should not install Sentence Transformers, PyTorch, CUDA runtimes, or model weights. For local CPU embeddings, install CPU-only PyTorch from the official PyTorch CPU index first, then install `.[embeddings]`. See README setup instructions.

Current defaults: CPU embeddings, top-k 4, minimum retrieval score 0.35, 900-character chunks, and 120-character overlap. These are centralized in `src/site_assistant/config.py`.

## Structure

- `data/raw/demo_company/`: sample company knowledge base
- `src/site_assistant/ingestion/`: Persian normalization, document loading, and chunking
- `src/site_assistant/retrieval/`: E5 embeddings, NumPy vector store, and retriever
- `src/site_assistant/generation/`: LLM client, prompts, and chat service
- `src/site_assistant/api/`: FastAPI chat route
- `widget/`: standalone demo page and chat widget
- `evals/`: evaluation questions and runner
- `scripts/build_index.py`: index-building entry point
- `PROJECT_CONTEXT.md`: compact project handoff notes
- `IMPLEMENTATION_PLAN.md`: ordered implementation checklist and acceptance criteria

## Implemented

- Local Markdown, text, and HTML document loading.
- Persian text normalization and paragraph-aware chunking.
- E5 passage and query embedding support.
- NumPy cosine-similarity search and a retriever with a minimum-score threshold.
- Vector-store `save()`, class-based `load()`, format versioning, and matrix/chunk validation.
- `scripts/build_index.py` now calls the existing `build_chunks()` pipeline, embeds chunk text, validates vector/chunk alignment, and saves `data/index/vector_store.npz` plus `data/index/vector_store.json`.
- Model-free tests verify that the index builder writes both files, that the saved store reloads correctly, and that empty corpora or mismatched embedding counts fail clearly.
- Persian generation prompt, hosted LLM client, and a chat service that returns source references.
- FastAPI health and chat routes.
- Basic RTL widget. The current JavaScript already sends `POST /api/v1/chat` and renders answers/source links; live end-to-end verification remains.
- Sample company content, starter evaluation cases, baseline tests, and a GitHub Actions workflow.

## Important implementation details

- `build_chunks()` already loads `data/raw/demo_company/` and applies configured chunk size and overlap. Reuse it rather than duplicating ingestion logic.
- `E5Embedder.embed_passages()` adds `passage: ` internally. Pass raw chunk text. Queries use `query: ` internally.
- Keep the embedding rows and chunk records in exactly the same order.
- Generated index files belong under `data/index/` and should stay out of version control.
- The chat route expects `request.app.state.chat_service`. The current `main.py` does not initialize it yet, so the chat endpoint returns 503.
- The latest CI run has a collection error in `tests/test_vector_store.py`: it imports `VectorStore`, but the implementation exports `NumpyVectorStore`. Fix the test interface before treating CI as green.

## Current priority

1. Run the corrected index-builder tests and Ruff in CI; then generate a real local index using the configured E5 model.
2. Initialize the embedder, saved vector store, retriever, LLM client, and chat service during FastAPI startup.
3. Verify the complete API path, then test the already-wired widget against it.
5. Add retrieval evaluation, minimal safeguards, deployment or a recorded fallback, and final documentation/demo rehearsal.

See `IMPLEMENTATION_PLAN.md` for detailed tasks and acceptance criteria.

## Development checks

Run `python -m pytest` and `ruff check .`. Keep credentials in `.env` or deployment secrets. Do not commit secrets, private source documents, model files, or generated indexes.
