# Persian Site Assistant

Persian-first website support assistant using retrieval-augmented generation (RAG).

**Status:** Working demo MVP with a portable Docker deployment path. The offline index build, FastAPI RAG API, Persian RTL website/widget, product catalogue, health/readiness probes, and automated tests are implemented. A hosted LLM API is configured at runtime; Ollama is optional for local development.

## Overview

The repository contains a Persian RTL company website, an embeddable assistant widget, a fictional eight-product catalogue, and a FastAPI backend. The assistant retrieves relevant passages from the local knowledge base, sends that context to a local or hosted OpenAI-compatible LLM, and returns an answer with related-document cards.

The sample company, its content, and every showcased project are fictional demonstration material. The showcase examples are illustrative concepts, not claims of completed client work.

## Demo website

The website has six pages:

- Home: introduction and summary of the company's capabilities.
- Services: scope and details for each service.
- Products: eight searchable fictional software products with demo-only price ranges.
- Solutions: four customer scenarios showing how product recommendations are made.
- Showcase: illustrative corporate website, online store, operations dashboard, and knowledge assistant scenarios.
- Contact and FAQ: sample contact details, working hours, and common questions.

All pages load the same chat widget from `widget/widget.js`. Product and solution pages can send prefilled questions directly to the assistant. The widget displays related source-document cards; these are retrieval context, not sentence-level citations.

## Architecture

```text
Knowledge preparation (run when source documents change)
Markdown / HTML / TXT → loader → normalization → chunks
    → E5 passage embeddings → NumPy vector store
    → data/index/vector_store.npz + vector_store.json

Application serving (run for website visitors)
Browser widget → Nginx reverse proxy → FastAPI → query embedding → retrieval
    → grounded prompt → configured LLM API → answer + related documents
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
├── data/raw/demo_company/       # Fictional company and product knowledge base
│   ├── products/                 # Eight product sheets and selection guide
│   └── projects/                 # Showcase scenario documents
├── data/index/                  # Generated index (not committed)
├── website/                     # Four-page Persian RTL company site
│   └── assets/
├── widget/                      # Embeddable chat widget and isolated demo
├── docker/                      # API, Nginx and frontend Dockerfiles/config
├── deploy/                      # Compose file for prebuilt portable images
├── compose.yaml                 # Build and run both containers
├── README_PORTABLE.md           # Destination-system handover guide
├── scripts/build_index.py       # Offline index-building entry point
├── scripts/download_embedding_model.py
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
.\\.venv\\Scripts\\Activate.ps1
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

Download the large model weights manually first. Use a download manager with this direct Hugging Face link:

[Download model.safetensors (471 MB)](https://huggingface.co/intfloat/multilingual-e5-small/resolve/97e13e802c05f5dbe5a86832df6d6f68b252e885/model.safetensors)

Save the file as:

```text
models/multilingual-e5-small/model.safetensors
```

Then run the project downloader:

```powershell
python scripts/download_embedding_model.py
```

The script verifies the large file using its SHA-256 checksum, then downloads only the remaining configuration and tokenizer files. It will not attempt to download the model weights again. If a smaller-file download fails, run the script again after reconnecting.

Set the local model path in `.env`:

```ini
EMBEDDING_MODEL=./models/multilingual-e5-small
```

The `models/` directory is ignored by Git; do not commit model weights.

### Build the local index

Run from the repository root after installing the embedding dependencies and downloading the model:

```powershell
python scripts/build_index.py
```

This reads all supported documents recursively from `data/raw/demo_company/`, creates embeddings, then saves:

- `data/index/vector_store.npz`: embedding matrix.
- `data/index/vector_store.json`: chunk metadata and format version.

Rebuild the index whenever the source knowledge-base documents change. Do not run index generation on every API startup.

### Configure the LLM

For local development with Ollama's OpenAI-compatible endpoint, set these values in `.env` (use the exact model tag shown by `ollama list`):

```ini
LLM_API_KEY=ollama
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=your-local-model-tag
LLM_TIMEOUT_SECONDS=120
```

For a hosted OpenAI-compatible provider, set its API key and model, plus its base URL when required. For example, a Groq configuration uses `LLM_BASE_URL=https://api.groq.com/openai/v1`. Use the exact model ID available to your account. Keep provider credentials in the backend environment; never place them in website or widget JavaScript. For Docker, use a hosted endpoint rather than a host-local Ollama URL.

### Run the API

Start the backend from the repository root:

```powershell
uvicorn site_assistant.main:app --reload --app-dir src
```

API documentation: `http://127.0.0.1:8000/docs`

### Smoke-test the running API

With your configured local or hosted LLM provider and FastAPI running, execute this in a separate terminal:

```powershell
python scripts/smoke_test_api.py
```

The script checks `/health` and `/ready`, then sends a supported Persian company question and an unsupported question to `POST /api/v1/chat`. It checks a known company question, a product-recommendation scenario, and an unsupported question. The script validates the HTTP response structure and saves the full answers as UTF-8 JSON to `data/test_output/chat_smoke_test.json`. Review the recommendation and abstention answers manually; the script does not score semantic quality. Open that report in VS Code to inspect Persian text without relying on terminal font/encoding behavior. Review the unsupported-question answer manually; the script does not claim to score semantic correctness.

You can override the API URL or timeout:

```powershell
python scripts/smoke_test_api.py --base-url http://127.0.0.1:8000 --timeout 240
# When using Docker Compose, the same API is available through Nginx:
python scripts/smoke_test_api.py --base-url http://127.0.0.1:8080 --timeout 240
```


Health check: `http://127.0.0.1:8000/health`  
Readiness check: `http://127.0.0.1:8000/ready`

### Runtime behavior

- `/health` reports that the API process is alive; `/ready` returns success only after the RAG chat service has initialized.
- Every response includes an `X-Request-ID` header. Successful chat responses and upstream-provider error responses also include this ID in the JSON body.
- LLM-provider API failures are returned as a generic `502` response. The backend logs the request ID and error type without returning provider internals to the browser.
- The API accepts questions up to 4,000 characters and rejects empty or whitespace-only messages.

### Run both containers with Docker Compose

After the embedding model is downloaded and the local vector index has been built, configure a hosted LLM provider in `.env`. Then run:

```powershell
docker compose up --build -d
```

Open `http://localhost:8080`. Nginx serves the website and proxies `/api/v1/chat`, health checks and `/docs` to FastAPI. The API image includes the E5 model, source documents and vector index. The destination system does not need Python, Sentence Transformers, PyTorch, or Ollama installed—only Docker and internet access for the LLM API.

### Build a portable handover bundle

On Windows with Docker Desktop using Linux containers, run:

```powershell
.\\scripts\\package_portable.ps1
```

The script checks the E5 model assets and API configuration, rebuilds the vector index from the current knowledge base, validates Compose, builds both images, starts an isolated preflight stack, verifies API readiness plus Nginx proxy and product-page delivery, then exports the images and creates:

`release/persian-site-assistant-portable.tar.gz`

The archive contains prebuilt API and web images plus Compose configuration and setup instructions. It includes the E5 model and vector index inside the API image. It deliberately excludes `.env` and API credentials; configure a separate key on the destination system. See `README_PORTABLE.md` for the handover steps.

This is an employer-demo MVP, not an unrestricted public service. It has no user authentication or distributed rate limiter. Do not expose the API to the public internet without additional access controls and rate limits.

### Run the website

From the repository root, in a second terminal:

```powershell
python -m http.server 5500
```

Open the full company website (including the new products and solutions pages):

`http://127.0.0.1:5500/website/`

An isolated widget-only smoke-test page is also available at:

`http://127.0.0.1:5500/widget/demo.html`

Uvicorn is installed without its optional `standard` extras. The current widget uses HTTP requests only and has no WebSocket endpoints, so the extra WebSocket server dependency is unnecessary.

## Dependency groups

| Extra | Includes | Use |
|---|---|---|
| `dev` | pytest, pytest-cov, Ruff | Tests and linting |
| `vector` | NumPy | Vector search and index persistence |
| `embeddings` | NumPy, Sentence Transformers, Hugging Face Hub | E5 model download and inference |

The GitHub Actions test job installs `.[dev,vector]`. It does not install Sentence Transformers, PyTorch, CUDA libraries, or model weights. Index-builder tests use a fake embedder.

## Sample questions

These questions exercise the expanded fictional knowledge base. The company, examples, and policies are demonstration content only.

### Company and collaboration
- راهکار نوین آریا چه نوع مجموعه‌ای است و برای چه کسب‌وکارهایی مناسب است؟
- برای شروع یک پروژه چه اطلاعاتی باید آماده کنم؟
- خروجی مرحله شناخت مسئله چیست؟
- معیار پذیرش هر قابلیت چگونه مشخص می‌شود؟
- چه عواملی روی برآورد هزینه و زمان پروژه اثر دارند؟

### Services
- برای طراحی یک وب‌سایت شرکتی چه صفحه‌ها و قابلیت‌هایی پیشنهاد می‌شود؟
- در یک فروشگاه اینترنتی چه امکاناتی برای مدیریت سفارش وجود دارد؟
- آیا می‌توان داشبورد را به نرم‌افزار حسابداری متصل کرد؟
- برای اتوماسیون یک فرایند داخلی چه چیزهایی باید بررسی شود؟
- آیا اتصال به درگاه پرداخت و سرویس پیامک تضمین‌شده است؟

### Security and operations
- چه اقداماتی برای محافظت از اطلاعات کاربران باید در نظر گرفته شود؟
- آیا شرکت گواهی امنیتی یا استاندارد مشخصی دارد؟
- پس از تحویل پروژه چه مستنداتی ارائه می‌شود؟
- پشتیبانی و نگهداری شامل چه مواردی است؟

### Knowledge assistant
- دستیار دانش این دمو از چه اجزایی تشکیل شده است؟
- وقتی سند جدیدی اضافه می‌شود، چطور وارد جست‌وجو می‌شود؟
- چرا ممکن است دستیار پاسخ یک پرسش را نداند؟
- آیا گفت‌وگوها در پایگاه داده ذخیره می‌شوند؟

### Product recommendation and comparison
- برای فروشگاه اینترنتی با حدود ۱۵۰ محصول و بودجه ۵۰ تا ۶۵ میلیون تومان چه محصولی مناسب است؟
- فروشگاه فعلی داریم و فقط مدیریت موجودی و ورود و خروج کالا لازم داریم؛ چه پیشنهادی دارید؟
- تفاوت پیگیر و جریان‌کار چیست؟
- برای پاسخ‌گویی از روی صدها فایل PDF چه محصولی مناسب است؟
- برای آموزشگاهی با چند مدرس و رزرو نوبت چه راهکاری پیشنهاد می‌کنید؟
- هشت محصول نمایشی را بر اساس کاربرد و بازه قیمت مقایسه کن.

### Questions that should not produce invented facts
- نام مدیرعامل شرکت چیست؟
- شماره تلفن و نشانی دفتر کجاست؟
- قیمت دقیق طراحی یک فروشگاه اینترنتی چقدر است؟
- کدام شرکت‌ها مشتری واقعی راهکار نوین آریا هستند؟
- شماره حساب بانکی مدیرعامل چیست؟
- آیا شرکت تعمیر لپ‌تاپ انجام می‌دهد؟


## Configuration

| Variable | Description |
|---|---|
| `APP_ENV` | Environment label, such as `development` or `production` |
| `CORS_ORIGINS` | Comma-separated allowed website origins; use exact origins when hosted |
| `LLM_API_KEY` | Provider API key |
| `LLM_BASE_URL` | OpenAI-compatible API base URL |
| `LLM_MODEL` | Provider model identifier |
| `LLM_TIMEOUT_SECONDS` | Timeout for a provider generation request |
| `EMBEDDING_MODEL` | Embedding model or local model directory |
| `EMBEDDING_DEVICE` | Embedding device (`cpu` by default) |
| `RETRIEVAL_TOP_K` | Number of retrieved passages |
| `RETRIEVAL_MIN_SCORE` | Minimum retrieval score |
| `CHUNK_SIZE_CHARS` | Maximum chunk length |
| `CHUNK_OVERLAP_CHARS` | Chunk overlap |

Keep credentials in `.env` or the hosting provider's secret store. Do not commit secrets, private source documents, model files, or generated indexes.

## Development checks

```powershell
python -m pytest
ruff check .
```

The current CI job tests API route behavior, document chunking and normalization, vector-store persistence, and the model-free index-building orchestration.
