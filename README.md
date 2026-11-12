# Persian Site Assistant

Persian-first website support assistant using retrieval-augmented generation (RAG).

**Status:** MVP under active development. The fictional company website and sample knowledge base are ready; FastAPI service initialization and end-to-end chat verification are the remaining backend integration work.

## Overview

The repository contains a small Persian RTL company website, an embeddable assistant widget, and a FastAPI backend. The assistant retrieves relevant passages from the company's local knowledge base, sends that context to an OpenAI-compatible LLM, and returns an answer with source references.

The sample company, its content, and every showcased project are fictional demonstration material. The showcase examples are illustrative concepts, not claims of completed client work.

## Demo website

The website has four pages:

- Home: introduction and summary of the company's capabilities.
- Services: scope and details for each service.
- Showcase: illustrative corporate website, online store, operations dashboard, and knowledge assistant scenarios.
- Contact and FAQ: sample contact details, working hours, and common questions.

All pages load the same chat widget from `widget/widget.js`. The widget uses the existing `POST /api/v1/chat` API contract and displays answer source cards when the API returns them.

## Architecture

```text
Knowledge preparation (run when source documents change)
Markdown / HTML / TXT → loader → normalization → chunks
    → E5 passage embeddings → NumPy vector store
    → data/index/vector_store.npz + vector_store.json

Application serving (run for website visitors)
Browser widget → FastAPI → query embedding → retrieval
    → grounded prompt → hosted LLM → answer + sources
```

## Stack

- Python 3.11+, FastAPI, Uvicorn, Pydantic
- OpenAI-compatible LLM API
- `intfloat/multilingual-e5-small` embeddings
- NumPy similarity search and persistence
- Static HTML, CSS, and vanilla JavaScript
- pytest and Ruff

## Repository

```text
.
├── data/raw/demo_company/       # Fictional company knowledge base
│   └── projects/                # Showcase scenario documents
├── data/index/                  # Generated index (not committed)
├── website/                     # Four-page Persian RTL company site
│   └── assets/
├── widget/                      # Embeddable chat widget and isolated demo
├── scripts/build_index.py       # Offline index-building entry point
├── src/site_assistant/
│   ├── api/
│   ├── generation/
│   ├── ingestion/
│   ├── retrieval/
│   ├── config.py
│   ├── main.py
│   └── schemas.py
├── evals/
├── tests/
├── .github/workflows/ci.yml
└── pyproject.toml
```

## Setup

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
Copy-Item .env.example .env
```

Install the lightweight development and vector dependencies:

```powershell
python -m pip install -e ".[dev,vector]"
```

### Enable local E5 embeddings (CPU)

The embedding extra installs Sentence Transformers and its model-inference dependencies. To avoid pulling a CUDA-enabled PyTorch build on a CPU-only machine, install the CPU wheel first from the official PyTorch CPU index:

```powershell
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e ".[embeddings]"
```

Check the installed build:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

For a CPU installation, `torch.cuda.is_available()` should be `False`. For NVIDIA GPU inference, use the matching command from the official [PyTorch installation selector](https://pytorch.org/get-started/locally/) instead of the CPU index.

The embedding model weights are downloaded the first time the embedder loads the configured model.

### Build the local index

Run from the repository root after installing the embedding dependencies:

```powershell
python scripts/build_index.py
```

This reads all supported documents recursively from `data/raw/demo_company/`, creates embeddings, then saves:

- `data/index/vector_store.npz`: embedding matrix.
- `data/index/vector_store.json`: chunk metadata and format version.

Rebuild the index whenever the source knowledge-base documents change. Do not run index generation on every API startup.

### Run the API

Configure `LLM_API_KEY`, `LLM_MODEL`, and optionally `LLM_BASE_URL` in `.env`, then start:

```powershell
uvicorn site_assistant.main:app --reload --app-dir src
```

API documentation: `http://127.0.0.1:8000/docs`

Health check: `http://127.0.0.1:8000/health`

**Backend status:** the chat route expects `app.state.chat_service`; FastAPI lifespan initialization is still being implemented. The widget can be viewed before that work is complete, but chat requests will not work until the service is initialized and the index/provider configuration is available.

### Run the website

From the repository root, in a second terminal:

```powershell
python -m http.server 5500
```

Open the full company website:

`http://127.0.0.1:5500/website/`

An isolated widget-only smoke-test page is also available at:

`http://127.0.0.1:5500/widget/demo.html`

Uvicorn is installed without its optional `standard` extras. The current widget uses HTTP requests only and has no WebSocket endpoints, so the extra WebSocket server dependency is unnecessary.

## Dependency groups

| Extra | Includes | Use |
|---|---|---|
| `dev` | pytest, pytest-cov, Ruff | Tests and linting |
| `vector` | NumPy | Vector search and index persistence |
| `embeddings` | NumPy, Sentence Transformers | E5 model inference |

The GitHub Actions test job installs `.[dev,vector]`. It does not install Sentence Transformers, PyTorch, CUDA libraries, or model weights. Index-builder tests use a fake embedder.

## Sample questions

- شرکت چه خدماتی ارائه می‌دهد؟
- مراحل اجرای یک پروژه چگونه است؟
- آیا نمونه‌کارها پروژه واقعی هستند؟
- برای ساخت فروشگاه اینترنتی چه قابلیت‌هایی در نظر گرفته شده است؟
- دستیار دانش و پشتیبانی چگونه پاسخ تولید می‌کند؟
- ساعات کاری شرکت چیست؟
- آیا شرکت تعمیر لپ‌تاپ انجام می‌دهد؟ (The assistant should not claim this service.)
- شماره تلفن یا نشانی دفتر چیست؟ (The assistant should say this information is not defined.)

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

## Development checks

```powershell
python -m pytest
ruff check .
```

The current CI job tests API route behavior, document chunking and normalization, vector-store persistence, and the model-free index-building orchestration.
