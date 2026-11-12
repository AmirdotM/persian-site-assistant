# Implementation Plan

Last reviewed: 2026-11-12
Demo target: Saturday, 2026-11-14

## Current repository state

- The document loader, Persian normalization, chunker, E5 embedder, NumPy retrieval, retriever, LLM client, chat service, API route, and basic RTL widget are present.
- Vector-store persistence now has `save()`, class-based `load()`, format versioning, and validation. It still needs dedicated round-trip tests before the rest of the app relies on it.
- `scripts/build_index.py` and `evals/run_evals.py` are still `NotImplementedError` stubs.
- `main.py` does not initialize `app.state.chat_service`. The chat endpoint therefore remains unavailable (503).
- The widget already sends `POST /api/v1/chat` and renders answers and source links. It has not yet been verified against a live, initialized backend.
- The sample evaluation file currently has 7 cases.
- The latest GitHub Actions run passed all 10 existing tests but failed Ruff with one `I001` import-order finding in `vector_store.py`. The workflow currently installs `.[dev]`, not the optional `[rag]` extra needed by NumPy/vector-store tests.

## Work order

### 1. Stabilize vector-store persistence and CI

I need to make persistence a reliable contract before using it in the API.

- Fix the Ruff import-order finding in `vector_store.py`.
- Add `tests/test_vector_store.py`.
- Test save/load round-tripping: vector values and shape, all `TextChunk` fields, and search results/scores must match before and after loading.
- Test clear failure behavior for a missing file, missing/corrupt metadata, invalid matrix shape, non-finite values, and vector/chunk count mismatch.
- Ensure CI installs the RAG dependencies required by tests, without downloading the embedding model during ordinary unit tests.
- Run `python -m pytest` and `ruff check .`; both must pass locally and in GitHub Actions.

**Done when:** a fresh store loaded from disk behaves exactly like the original, and CI is green.

### 2. Build the local index

I need to finish `scripts/build_index.py` as a thin orchestration script, reusing the existing helpers.

- Read the source and output paths, embedding model, device, and chunk settings from application settings.
- Call `build_chunks()`; do not duplicate the loader or chunking logic.
- Stop with a useful message if no chunks are produced.
- Pass raw chunk texts to `E5Embedder.embed_passages()`; that method already adds the `passage: ` prefix.
- Keep embedding row order aligned with chunk order.
- Validate the matrix shape and row count before constructing and saving the store.
- Print source-document count, chunk count, embedding dimensions, and output path.

**Done when:** `python scripts/build_index.py` writes the index and metadata under `data/index/`, and a separate process can load the saved index.

### 3. Initialize the backend during FastAPI startup

I need to wire the existing services together once when the application starts.

- Use FastAPI's lifespan mechanism for startup and shutdown.
- Load the persisted vector store and initialize the same configured E5 model used to build it.
- Construct `Retriever`, `LLMClient`, and `ChatService`.
- Make the service available to the existing route through `app.state.chat_service` (or a consistent dependency provider).
- Make startup failures visible. Distinguish process liveness from chat readiness so `/health` does not imply the RAG service is ready when its index or provider configuration is missing.
- Close the async LLM client during shutdown when appropriate.

**Done when:** with a valid index and provider configuration, the API becomes ready and the chat route reaches `ChatService.answer()`.

### 4. Verify the backend end to end

- Test the real request path: request validation → query embedding → retrieval → grounded prompt → LLM response → answer and source references.
- Cover unsupported questions, empty/oversized input, missing index, and provider timeout/error.
- Keep unit tests deterministic by mocking the embedder/provider where appropriate; perform one separate real-provider smoke test.
- Confirm source IDs, titles, excerpts, and URLs are preserved correctly.
- Run tests and Ruff again after integration.

**Done when:** a real Persian API request returns an answer with sources, while unsupported or unavailable cases fail safely.

### 5. Verify and polish the widget

The initial frontend request/rendering code is already present, so this is an integration and quality pass.

- Verify the demo page sends the expected request to the configured API base URL.
- Confirm Persian answers and sources render correctly with the current response schema.
- Test loading, duplicate-submit prevention, empty input, non-JSON error responses, server errors, and unavailable API behavior.
- Check mobile dimensions, keyboard use, focus behavior, and RTL layout.
- Keep all provider credentials server-side and use safe text insertion for generated content.

**Done when:** the local demo supports one successful conversation and one clear failure scenario.

### 6. Add minimal operational safeguards

- Enforce the existing request-size constraints consistently between the widget and API.
- Keep provider timeouts bounded and error responses stable.
- Log request duration and failure type without logging API keys, full prompts, or private user messages.
- Avoid adding a database, Redis, authentication, or complex rate-limiting infrastructure for this demo.

**Done when:** normal provider failures and invalid requests are understandable without exposing secrets or sensitive content.

### 7. Implement retrieval evaluation

- Expand `evals/questions.jsonl` from 7 to around 10–15 cases.
- Cover direct facts, paraphrases, Persian/Arabic character variants, multi-source questions, and unsupported questions.
- Read the expected source IDs and compare them with retrieved top-k source IDs.
- Report per-question results and a simple aggregate source-hit metric.
- Review answer quality and abstention behavior manually; do not claim automated answer-quality scoring unless it is actually implemented.

**Done when:** one command produces a repeatable retrieval report and the README explains exactly what it measures.

### 8. Deploy or prepare a dependable fallback

- Try one simple free deployment route, with a hard 45-minute investigation limit.
- Configure the LLM credential as a server-side secret and set the production CORS origin.
- Verify health/readiness and a real chat request from a separate browser or device.
- If free-tier limits, cold starts, access, or networking make deployment unreliable, stop and record a 60–90 second local walkthrough.
- Keep a tested local run command and sample questions ready.

**Done when:** either the public demo works from another device or the recording and local backup are ready.

### 9. Final documentation and presentation

- Update the README to match what is actually implemented, with setup, configuration, run commands, sample questions, evaluation method/results, and known limitations.
- Rehearse a 3–5 minute explanation: problem, RAG architecture, retrieval, evidence/citations, evaluation, limitations, and next improvements.
- Prepare one answerable question and one unsupported question for the demo.
- Run a final smoke test before the presentation.

**Done when:** a fresh setup is documented and I can explain each implemented part accurately.

## Scope control

The demo is one fictional company, one Persian-first widget, one FastAPI backend, one embedding model, one hosted LLM provider, citations, an honest fallback, and a small retrieval evaluation.

I am deliberately leaving fine-tuning, agents, authentication, multi-site crawling, databases, and additional infrastructure out of this sprint. Reliability of the complete path matters more than extra features.
