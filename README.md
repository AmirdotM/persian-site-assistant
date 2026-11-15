# Persian Site Assistant

A Persian-first website demo with a support assistant that answers from a small, controlled knowledge base.

The website, company, products, project examples, and prices are fictional. They are there to make the demo realistic; they are not claims about real clients or commercial products.

## What is included

- A responsive Persian RTL company website.
- An embeddable chat widget with suggested questions, loading states, and related-source cards.
- Eight fictional products and four example customer scenarios.
- A FastAPI backend with health and readiness checks.
- A local E5 embedding model and a saved NumPy vector index.
- An OpenAI-compatible LLM client. The LLM can be hosted; the embedding model and retrieval index run locally.

## How the assistant works

The knowledge base lives under `data/raw/demo_company/`. The index is built before the demo starts:

```text
Markdown / HTML / TXT
        |
        v
load -> normalize Persian text -> split into chunks
        |
        v
E5 passage embeddings -> NumPy vector index
        |
        v
data/index/vector_store.npz + vector_store.json
```

When a visitor asks a question, the API embeds the question, retrieves the closest passages, and sends those passages to the configured LLM. The widget displays the answer and a short list of related documents.

The source cards show which documents were retrieved. They are useful context, but they are not sentence-level citations.

## Local development

Use Python 3.12 for the same version used by the packaged API image.

Create a virtual environment and install the project:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install -e ".[dev,embeddings]"
Copy-Item .env.example .env
```

Download the 471 MB [E5 model weights](https://huggingface.co/intfloat/multilingual-e5-small/resolve/97e13e802c05f5dbe5a86832df6d6f68b252e885/model.safetensors) and save them as `models/multilingual-e5-small/model.safetensors`. Then run `python scripts/download_embedding_model.py`; it verifies the weights and downloads the remaining configuration and tokenizer files.

Build the index after the model is ready:

```powershell
python scripts/build_index.py
```

Configure `.env` with an LLM provider:

```ini
LLM_API_KEY=your-provider-key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=your-provider-model-id
LLM_TIMEOUT_SECONDS=120
EMBEDDING_MODEL=./models/multilingual-e5-small
EMBEDDING_DEVICE=cpu
```

Use the exact model ID enabled for your provider. Leave `LLM_BASE_URL` empty when using the default OpenAI endpoint. Keep the API key in the backend environment; it must never go into website or widget JavaScript.

Start the complete local website and API from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn site_assistant.main:app --app-dir src --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The root address redirects to the website. The API checks are available at `/health` and `/ready`; interactive API documentation is at `/docs`.

Run the automated checks with:

```powershell
python -m pytest
ruff check .
```


## Configuration

The main settings are read from environment variables or `.env`:

| Setting | Purpose |
|---|---|
| `LLM_API_KEY` | Provider API key |
| `LLM_BASE_URL` | Optional OpenAI-compatible API base URL |
| `LLM_MODEL` | Provider model ID |
| `LLM_TIMEOUT_SECONDS` | Upstream request timeout |
| `EMBEDDING_MODEL` | E5 model ID or local directory |
| `EMBEDDING_DEVICE` | Embedding device; `cpu` is the default |
| `RETRIEVAL_TOP_K` | Number of passages to retrieve |
| `RETRIEVAL_MIN_SCORE` | Minimum similarity score for a passage |
| `CHUNK_SIZE_CHARS` | Maximum chunk length |
| `CHUNK_OVERLAP_CHARS` | Overlap between neighbouring chunks |

Do not commit `.env`, model weights, generated indexes, or private documents.
