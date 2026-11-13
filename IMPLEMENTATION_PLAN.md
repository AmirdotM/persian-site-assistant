# Implementation Plan

Last reviewed: 2026-11-13
Demo target: Saturday, 2026-11-14

## Current repository state

The core local demo path is implemented and has been exercised with a real local Ollama model.

- Persian Markdown knowledge base, ingestion pipeline, chunking, and offline index builder are implemented.
- The E5 embedding model is configured to load from a local model directory; generated model weights and vector index remain outside Git.
- NumPy vector-store persistence and loading are implemented and covered by tests.
- FastAPI lifespan loads the vector store, embedder, retriever, and LLM client; shutdown closes the LLM client.
- The API exposes `/health`, `/ready`, and `POST /api/v1/chat`.
- The Persian RTL website and embeddable widget are implemented. The widget displays assistant messages and source cards, uses safe text insertion, and has clear loading/error states.
- A local API smoke test has passed against Ollama: health and readiness returned 200, a supported Persian question returned a grounded response with sources, and an unsupported question received an abstention-style response.
- API hardening is in PR #1: blank-message validation, server-generated request IDs, sanitized upstream LLM errors, tests, and corrected runtime/deployment documentation.
- GitHub Actions tests and Ruff pass on the hardening branch.
- `evals/run_evals.py` is not implemented. Retrieval tuning and formal evaluation are intentionally deferred until after the demo.

## Remaining work before the demo

### 1. Review and merge the API hardening PR

- Review PR #1: request IDs, blank input validation, and upstream error handling.
- Merge only after confirming the CI checks are green.
- Pull the updated `main` branch into the local working copy.

**Done when:** the reviewed API hardening changes are part of `main`.

### 2. Verify the actual website in a browser

Run the backend and static website in separate terminals:

```powershell
uvicorn site_assistant.main:app --reload --app-dir src
python -m http.server 5500
```

Open `http://127.0.0.1:5500/website/` and verify:

- All four pages load and navigation works.
- The chat widget opens, closes, and stays usable at desktop and mobile widths.
- A supported question receives a Persian answer and source cards.
- A follow-up question can be sent after the first response.
- An unavailable API or provider produces a readable error, and the input becomes usable again.
- Keyboard focus, Escape-to-close, and RTL layout behave sensibly.

**Suggested live demo questions:**

1. `شرکت چه خدماتی ارائه می‌دهد؟`
2. `مراحل اجرای یک پروژه چگونه است؟`
3. `شماره حساب بانکی مدیرعامل چیست؟` (The assistant should not invent an answer.)

**Done when:** the complete browser → widget → API → retrieval → LLM → source-card path works at least twice in a row.

### 3. Make the local demo repeatable

Before presenting:

- Confirm the local embedding model path in `.env` and confirm both generated index files exist in `data/index/`.
- Start Ollama and verify the configured model tag with `ollama list`.
- Confirm `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_TIMEOUT_SECONDS` match the local provider.
- Check `/health` and `/ready`, then run `python scripts/smoke_test_api.py`.
- Keep the terminal running and avoid rebuilding the index immediately before the presentation unless the source documents changed.

Prepare a 60–90 second screen recording or a few screenshots showing the website, one supported answer, and its source cards. Keep the local live demo as the primary path and the recording as the backup.

**Done when:** the demo can be restarted from a short checklist without debugging or downloading model weights.

### 4. Optional hosted demo

Only deploy if the hosting route is reliable and does not consume time needed for the presentation.

A hosted setup must:

- Serve the API over HTTPS.
- Configure `CORS_ORIGINS` to the exact website origin(s).
- Set each widget script's `data-api-url` to the public API base URL.
- Provide the generated files under `data/index/` and the configured E5 model directory.
- Store the LLM key in server-side environment secrets.
- Configure platform-level rate limits or access controls before public exposure.

There is currently no Docker or hosting-provider deployment configuration. Do not expose the unauthenticated API as an unrestricted public endpoint.

**Done when:** a chat request succeeds from a separate browser/device and both health and readiness checks pass. Otherwise, use the local demo and recording backup.

### 5. Prepare the technical walkthrough

Keep the explanation to 3–5 minutes:

1. The problem: answer website questions from a controlled knowledge base.
2. Ingestion: load documents, normalize, chunk, and embed them offline.
3. Retrieval: embed a query and search the saved NumPy vector index.
4. Generation: pass retrieved passages to an OpenAI-compatible local or hosted LLM.
5. Trust and operations: show source references, honest abstention, readiness checks, request IDs, and safe provider errors.
6. Limitations: one demo knowledge base, no authentication, no distributed rate limiter, and retrieval evaluation not yet implemented.

Be explicit that the sample company and project briefs are fictional demonstration material.

**Done when:** the architecture can be explained without claiming capabilities that are not implemented.

## Deferred until after the demo

These are useful improvements, but they are not blockers for the current presentation:

- Implement the retrieval evaluation runner and expand the question set.
- Investigate similarity-score calibration and improve unsupported-question filtering.
- Add distributed rate limiting and authentication before any broader public release.
- Add Docker/Compose or a repeatable cloud deployment configuration if a hosted deployment is required.
- Explore a second hosted LLM provider after the local demo path is stable.

## Scope control

The demo is one fictional company, one Persian-first website/widget, one FastAPI backend, one local E5 embedding model, one OpenAI-compatible LLM endpoint, and source-grounded responses.

Do not add fine-tuning, agents, a database, multi-site crawling, or extra infrastructure before the presentation. A reliable complete path is more valuable than a larger feature list.
