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
- NumPy similarity search and persistence
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

The second command installs Sentence Transformers. Pip should keep the already-installed CPU PyTorch version because it satisfies the package requirement. Check the installed build with:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

For a CPU installation, `torch.cuda.is_available()` should be `False`. For NVIDIA GPU inference, use the matching command from the official [PyTorch installation selector](https://pytorch.org/get-started/locally/) instead of the CPU index.

The embedding model weights are downloaded when the embedder first loads the configured model, not by the project setup command itself.

### Run the API

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

## Dependency groups

| Extra | Includes | Use |
|---|---|---|
| `dev` | pytest, pytest-cov, Ruff | Tests and linting |
| `vector` | NumPy | Vector search and index persistence |
| `embeddings` | Sentence Transformers | E5 model inference |

The GitHub Actions test job installs `.[dev,vector]`. It does not install Sentence Transformers, PyTorch, CUDA libraries, or model weights. Unit tests should mock the embedder and test vector behavior independently.

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

The current MVP includes the API shell, Persian normalization, document loading and chunking, E5 embedding and retrieval components, a Persian prompt, sample content, and the widget interface. Index generation, end-to-end service initialization, and evaluation execution are in progress.
