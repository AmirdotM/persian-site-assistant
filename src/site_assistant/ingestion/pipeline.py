"""Orchestrate document loading and chunk creation."""

from pathlib import Path

from site_assistant.config import settings
from site_assistant.ingestion.chunker import TextChunk, chunk_text
from site_assistant.ingestion.loader import load_local_documents


def build_chunks(source_dir: Path | None = None) -> list[TextChunk]:
    """Load the source corpus and create chunks using central configuration."""
    directory = source_dir or settings.data_dir / "raw" / "demo_company"
    documents = load_local_documents(directory)
    chunks: list[TextChunk] = []
    for document in documents:
        chunks.extend(
            chunk_text(
                document.text,
                source_id=document.source_id,
                title=document.title,
                url=document.url,
                max_chars=settings.chunk_size_chars,
                overlap_chars=settings.chunk_overlap_chars,
            )
        )
    return chunks
