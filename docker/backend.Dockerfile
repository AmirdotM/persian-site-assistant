FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

WORKDIR /app

# Install the CPU-only PyTorch build first. The app does not need CUDA in this portable demo.
RUN python -m pip install --upgrade pip \
    && python -m pip install torch --index-url https://download.pytorch.org/whl/cpu

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install ".[embeddings]"

# Ship the complete fictional knowledge base, generated index and local E5 model in the image.
COPY data/raw ./data/raw
COPY data/index ./data/index
COPY models/multilingual-e5-small ./models/multilingual-e5-small

RUN test -s /app/data/index/vector_store.npz \
    && test -s /app/data/index/vector_store.json \
    && test -s /app/models/multilingual-e5-small/model.safetensors

ENV APP_ENV=production \
    DATA_DIR=/app/data \
    EMBEDDING_MODEL=/app/models/multilingual-e5-small \
    EMBEDDING_DEVICE=cpu

EXPOSE 8000

CMD ["uvicorn", "site_assistant.main:app", "--host", "0.0.0.0", "--port", "8000"]
