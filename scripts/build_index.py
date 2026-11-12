"""Build the local retrieval index.

TODO: Implement this as a thin orchestration script. See IMPLEMENTATION_PLAN.md.

Implementation checklist:
1. Read corpus/output paths and embedding settings from application settings.
2. Call the existing build_chunks() pipeline for data/raw/demo_company.
3. Report a clear error and stop if the corpus produces no chunks.
4. Extract chunk text in its existing order and pass it to E5Embedder.embed_passages().
   The embedder adds the required "passage: " prefix; do not add it here.
5. Verify that the embedding matrix is 2-D and has one row per chunk.
6. Construct NumpyVectorStore with the aligned matrix and chunk list, then save it
   beneath data/index/ using one consistent .npz path.
7. Print source-document count, chunk count, embedding dimension, and saved path.

Keep the script offline: it should not call the hosted LLM provider.
"""
from src.site_assistant.ingestion.chunker import TextChunk 
from src.site_assistant.retrieval.vector_store import NumpyVectorStore
from src.site_assistant.config import settings
from src.site_assistant.retrieval.embeddings import E5Embedder
import logging
from pathlib import Path
from typing import Sequence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_index():
    """Build the local retrieval index."""
    data_dir = settings.data_dir
    chunks_path = data_dir / "chunks" / "chunks.jsonl"
    index_path = data_dir / "index" / "vector_store.npz"

    # Load chunks from the existing JSONL file
    if not chunks_path.exists():
        logger.error(f"Chunks file not found: {chunks_path}")
        return

    chunks: Sequence[TextChunk] = TextChunk.load_chunks(chunks_path)
    if not chunks:
        logger.error("No chunks found in the corpus.")
        return

    # Extract chunk texts for embedding
    chunk_texts = [chunk.text for chunk in chunks]

    # Embed the chunk texts using E5Embedder
    embedder = E5Embedder(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        timeout_seconds=settings.llm_timeout_seconds,
    )
    embeddings = embedder.embed_passages(chunk_texts)

    # Validate embedding matrix dimensions
    if embeddings.ndim != 2 or embeddings.shape[0] != len(chunks):
        logger.error("Embedding matrix dimensions do not match the number of chunks.")
        return

    # Create and save the vector store
    vector_store = NumpyVectorStore(vectors=embeddings, chunks=chunks)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    vector_store.save(index_path)

    logger.info(f"Index built successfully: {index_path}")
    logger.info(f"Source documents: {len(set(chunk.source for chunk in chunks))}")
    logger.info(f"Chunks: {len(chunks)}")
    logger.info(f"Embedding dimension: {embeddings.shape[1]}")




