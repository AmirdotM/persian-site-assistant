# Implementation Plan

Last reviewed: 2026-11-12
Demo target: Saturday, 2026-11-14

## Current repository state

- The document loader, Persian normalization, chunker, E5 embedder, NumPy retrieval, retriever, LLM client, chat service, and API route are present.
- The fictional knowledge base now includes expanded company, service, process, contact and FAQ material plus four clearly labelled illustrative project briefs.
- A four-page Persian RTL website (home, services, showcase, contact/FAQ) and a redesigned embeddable chat widget are in place. The widget continues to call the existing `POST /api/v1/chat` contract.
- Vector-store persistence has `save()`, class-based `load()`, format versioning, validation, and a basic round-trip test.
- `scripts/build_index.py` now orchestrates the existing chunking pipeline, E5 passage embedding, and vector-store persistence. It has deterministic tests using a fake embedder, so CI does not download model weights.
- `evals/run_evals.py` remains unimplemented.
- `main.py` does not initialize `app.state.chat_service`. The chat endpoint therefore remains unavailable (503).
- The widget already sends `POST /api/v1/chat` and renders answers and source links. It has not yet been verified against a live, initialized backend.
- The sample evaluation file currently has 7 cases.
- CI installs `.[dev,vector]` and keeps Sentence Transformers/PyTorch out of the test job. The latest confirmed run passed 16 tests and Ruff; website/content changes do not alter the backend test dependencies.

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

The orchestration script is now implemented and covered by model-free tests. The next step is to verify it in CI and run it locally with the actual E5 model.

- `build_index()` reuses `build_chunks()` from the ingestion pipeline.
- It passes raw chunk text to `E5Embedder.embed_passages()`; the embedder adds the `passage: ` prefix.
- It checks the embedding matrix and chunk count before constructing the store.
- `NumpyVectorStore.save()` writes `data/index/vector_store.npz` and `data/index/vector_store.json`.
- Unit tests mock the embedder and verify both files and the round-trip load.

**Done when:** CI passes the builder tests and `python scripts/build_index.py` writes an actual index locally that can be loaded in a separate process.

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

### 5. Verify the website and widget against the backend

The four-page Persian RTL site and shared widget are implemented. The remaining work here is browser verification against the live FastAPI service.

- Open `http://127.0.0.1:5500/website/` while serving the repository root and check all four pages and responsive navigation.
- Confirm the widget sends the expected request to the configured API base URL.
- Confirm Persian answers and source cards render correctly with the current response schema.
- Test loading, duplicate-submit prevention, empty input, non-JSON errors, server errors, and unavailable API behavior.
- Check mobile layout, keyboard/focus behavior, and RTL direction.
- Keep credentials server-side and use safe text insertion for generated content.

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
