# Project Notes

Last reviewed: 2026-11-12

## Goal

I'm building a Persian-first website support assistant that can be embedded as a small RTL chat widget. It should answer questions from a site's own content, use a hosted LLM for generation, and show the sources behind its answers.

## Stack

- Python 3.11+; FastAPI and Pydantic
- `intfloat/multilingual-e5-small` for multilingual embeddings
- NumPy for the initial vector search implementation
- OpenAI-compatible API for hosted LLM generation
- Vanilla JavaScript and CSS for the embeddable widget
- pytest and Ruff for testing and linting

The current configuration uses CPU embeddings, top-k 4, minimum retrieval score 0.35, 900-character chunks, and 120-character overlap. These values are centralized in `src/site_assistant/config.py`.

## Current structure

- `data/raw/demo_company/`: sample company knowledge base
- `src/site_assistant/ingestion/`: Persian normalization, document loading, and chunking
- `src/site_assistant/retrieval/`: E5 embeddings, NumPy vector store, and retriever
- `src/site_assistant/generation/`: LLM client, prompts, and chat service
- `src/site_assistant/api/`: FastAPI chat route
- `widget/`: standalone demo page and chat widget
- `evals/`: evaluation questions and runner
- `scripts/build_index.py`: index-building entry point

## Implemented so far

- Local Markdown, text, and HTML document loading.
- Persian text normalization and paragraph-aware chunking.
- E5 passage and query embedding support.
- NumPy cosine-similarity search and a retriever with a minimum-score threshold.
- Persian generation prompt, hosted LLM client, and a chat service that returns source references.
- FastAPI health and chat routes, plus the basic RTL widget.
- Sample company content, starter evaluation questions, tests, and a GitHub Actions workflow.

## Important implementation details

- `build_chunks()` already loads `data/raw/demo_company/` and applies the configured chunk size and overlap. Prefer using this pipeline rather than repeating loading and chunking logic in scripts.
- `E5Embedder.embed_passages()` adds the required `passage: ` prefix internally. Pass it raw chunk text; adding the prefix again would duplicate it. Queries use `query: ` internally.
- Keep the embedding rows and chunk records in exactly the same order. Each vector must continue to map to its corresponding chunk.
- Generated index files belong under `data/index/` and should stay out of version control.
- The API route expects `request.app.state.chat_service`. The current `main.py` does not initialize that service yet, so the chat endpoint will return 503 until startup wiring is added.

## Current status and next steps

1. **Review and correct vector-store persistence.** The latest `vector_store.py` has `save()`, `load()`, and `validate()`, but they are not yet consistent with the constructor and search implementation. In particular, JSON serialization currently receives `TextChunk` dataclass objects directly; `self.metadata` and `_get_matrix()` are referenced but not defined; and `load()` is written as an instance mutator even though the constructor requires a non-empty matrix and matching chunks. Settle a clean save/load interface and add tests before relying on it.
2. **Complete `scripts/build_index.py`.** Use the configured data paths and model, call `build_chunks()`, embed the chunk texts, construct the vector store, save it under `data/index/`, and print document count, chunk count, embedding dimensions, and output path. Handle an empty corpus clearly. The script is currently a `NotImplementedError` stub.
3. **Add API startup wiring.** Load the saved index, initialize the embedder, retriever, LLM client, and `ChatService`, then attach the service to application state.
4. **Add end-to-end and retrieval evaluation.** The current tests cover the API shell, chunking, and normalization; persistence/index-building tests and a working evaluation runner are still needed. Check CI dependencies when adding tests that require the optional RAG extra.

## Development checks

Run tests with `python -m pytest` and lint with `ruff check .`. The README documents the local setup and demo commands. Keep credentials in `.env` or deployment secrets; do not commit secrets, private source documents, model files, or generated indexes.
