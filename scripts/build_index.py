"""Build the local retrieval index from the source knowledge base.

Run from the repository root after installing the `embeddings` extra:

    python scripts/build_index.py

This is an offline preparation step. The FastAPI application loads the
resulting files; it does not rebuild the index on every startup.
"""

import logging
import sys
from pathlib import Path

# This script is executed directly, so Python otherwise adds only the
# scripts/ directory to sys.path. Add src/ to support this repository's
# src-layout without requiring an editable package installation.
SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from site_assistant.config import settings
from site_assistant.ingestion.pipeline import build_chunks
from site_assistant.retrieval.embeddings import E5Embedder
from site_assistant.retrieval.vector_store import NumpyVectorStore

logger = logging.getLogger(__name__)

INDEX_FILENAME = "vector_store.npz"


def build_index() -> Path:
    """Create embeddings for the source chunks and persist the vector store."""
    # 1. Load source documents and split them into TextChunk objects.
    # build_chunks() already uses data/raw/demo_company/ and the configured
    # chunk size/overlap, so we should not introduce a second chunks.jsonl path.
    chunks = build_chunks()

    if not chunks:
        raise ValueError(
            "No text chunks were created. Check data/raw/demo_company/ "
            "and the document loader."
        )

    # 2. Embed the chunk text in exactly the same order as the chunks.
    # E5Embedder adds the required "passage: " prefix internally.
    embedder = E5Embedder(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
    )
    embeddings = embedder.embed_passages([chunk.text for chunk in chunks])

    # 3. Make sure every chunk has exactly one embedding row.
    if embeddings.ndim != 2:
        raise ValueError(
            f"Expected a 2-D embedding matrix, got {embeddings.ndim}-D."
        )

    if embeddings.shape[0] != len(chunks):
        raise ValueError(
            "Embedding/chunk count mismatch: "
            f"{embeddings.shape[0]} vectors for {len(chunks)} chunks."
        )

    # 4. Save both the vectors and their matching chunk metadata.
    # NumpyVectorStore.save(".../vector_store.npz") writes:
    #   vector_store.npz  -> NumPy embedding matrix
    #   vector_store.json -> serialized TextChunk records + format version
    index_path = settings.data_dir / "index" / INDEX_FILENAME
    vector_store = NumpyVectorStore(vectors=embeddings, chunks=chunks)
    vector_store.save(index_path)

    source_count = len({chunk.source_id for chunk in chunks})
    logger.info("Index created successfully.")
    logger.info("Source documents represented: %d", source_count)
    logger.info("Chunks: %d", len(chunks))
    logger.info("Embedding dimensions: %d", embeddings.shape[1])
    logger.info("Vector file: %s", index_path)
    logger.info("Chunk metadata: %s", index_path.with_suffix(".json"))

    return index_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_index()
