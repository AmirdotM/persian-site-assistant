# Persian Site Assistant

Persian-first website support assistant using retrieval-augmented generation (RAG).

**Status:** MVP under active development.

## Overview

The application provides an embeddable right-to-left chat widget backed by a FastAPI service. The service retrieves relevant passages from a knowledge base, generates answers through a hosted LLM provider, and returns source references.

```text
Website widget → FastAPI → Persian normalization → E5 embeddings
                                      ↓
                              NumPy retrieval
                                      ↓
                              Grounded LLM
                                      ↓
                              Answer + sources
```

## Stack

- Python 3.12, FastAPI, Pydantic
- OpenAI-compatible LLM API
- `intfloat/multilingual-e5-small` embeddings
- NumPy similarity search
- Vanilla JavaScript and CSS
- pytest and Ruff

## Repository

```text
.
├── .github/workflows/ci.yml
├── data/
│   ├── raw/demo_company/
│   ├── processed/
│   └── index/
├── evals/
│   ├── questions.jsonl
│   └── run_evals.py
├── scripts/build_index.py
├── src/site_assistant/
│   ├── api/
│   ├── generation/
│   ├── ingestion/
│   ├── retrieval/
│   ├── config.py
│   ├── main.py
│   └── schemas.py
├── tests/
├── widget/
├── .env.example
└── pyproject.toml
```

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,rag]"
Copy-Item .env.example .env
```

Configure the provider credentials and model in `.env`, then start the API:

```powershell
uvicorn site_assistant.main:app --reload --app-dir src
```

API documentation: `http://127.0.0.1:8000/docs`

Health check: `http://127.0.0.1:8000/health`

Serve the demo widget from the repository root in a second terminal:

```powershell
python -m http.server 5500
```

Demo page: `http://127.0.0.1:5500/widget/demo.html`

## Configuration

| Variable | Description |
|---|---|
| `LLM_API_KEY` | Provider API key |
| `LLM_BASE_URL` | OpenAI-compatible API base URL |
| `LLM_MODEL` | Provider model identifier |
| `EMBEDDING_MODEL` | Embedding model |
| `EMBEDDING_DEVICE` | Embedding device (`cpu` by default) |
| `RETRIEVAL_TOP_K` | Number of retrieved passages |
| `RETRIEVAL_MIN_SCORE` | Minimum retrieval score |
| `CHUNK_SIZE_CHARS` | Maximum chunk length |
| `CHUNK_OVERLAP_CHARS` | Chunk overlap |

Keep credentials in `.env` or deployment secrets. Do not commit secrets, private source documents, model files, or generated indexes.

## Development

```powershell
python -m pytest
ruff check .
```

The current MVP includes the API shell, Persian normalization, document loading and chunking, E5 embedding and retrieval components, a Persian prompt, sample content, and the widget interface. Index persistence, end-to-end service initialization, API integration, and evaluation execution are in progress.
