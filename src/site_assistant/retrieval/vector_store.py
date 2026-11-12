"""In-memory NumPy vector search with disk persistence."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from site_assistant.ingestion.chunker import TextChunk


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SearchHit:
    chunk: TextChunk
    score: float


class NumpyVectorStore:
    """Minimal vector store; vectors are expected to be L2-normalized."""

    FORMAT_VERSION = 1

    def __init__(
        self,
        vectors: np.ndarray,
        chunks: Sequence[TextChunk],
    ) -> None:
        self.vectors = np.asarray(vectors, dtype=np.float32)
        self.chunks = list(chunks)

        self.validate()

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 4,
    ) -> list[SearchHit]:
        """Return the top-k chunks by cosine similarity."""

        query = np.asarray(query_vector, dtype=np.float32).reshape(-1)

        if query.shape[0] != self.vectors.shape[1]:
            raise ValueError(
                "Query vector dimension does not match indexed vectors"
            )

        if not np.isfinite(query).all():
            raise ValueError("Query vector contains invalid values")

        query_norm = np.linalg.norm(query)

        if query_norm == 0:
            raise ValueError("Query vector cannot be all zeros")

        query = query / query_norm

        scores = self.vectors @ query

        count = min(max(top_k, 0), len(self.chunks))
        indices = np.argsort(scores)[::-1][:count]

        return [
            SearchHit(self.chunks[int(i)], float(scores[int(i)]))
            for i in indices
        ]

    @staticmethod
    def _normalize_path(path: Path) -> Path:
        """Ensure the index file has an .npz extension."""

        path = Path(path)

        if path.suffix != ".npz":
            path = path.with_suffix(".npz")

        return path

    def save(self, path: Path) -> None:
        """Save vectors and chunk information to disk."""

        path = self._normalize_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self.validate()

        # Convert TextChunk dataclasses to plain dictionaries before JSON encoding.
        chunk_data = [asdict(chunk) for chunk in self.chunks]

        data = {
            "format_version": self.FORMAT_VERSION,
            "chunks": chunk_data,
        }

        json_path = path.with_suffix(".json")

        json_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        np.savez_compressed(path, embeddings=self.vectors)

        logger.info("Saved vector store to %s", path)

    @classmethod
    def load(cls, path: Path) -> NumpyVectorStore:
        """Load a vector store and return a new instance."""

        path = cls._normalize_path(path)
        json_path = path.with_suffix(".json")

        if not path.is_file():
            raise FileNotFoundError(f"Vector index not found: {path}")

        if not json_path.is_file():
            raise FileNotFoundError(f"Chunk metadata not found: {json_path}")

        data = json.loads(json_path.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            raise ValueError("Invalid index metadata format")

        if data.get("format_version") != cls.FORMAT_VERSION:
            raise ValueError("Unsupported index format version")

        chunk_data = data.get("chunks")

        if not isinstance(chunk_data, list):
            raise ValueError("Index metadata must contain a chunks list")

        chunks: list[TextChunk] = []

        for item in chunk_data:
            if not isinstance(item, dict):
                raise ValueError("Invalid chunk metadata entry")

            chunks.append(TextChunk(**item))

        with np.load(path, allow_pickle=False) as loaded:
            if "embeddings" not in loaded.files:
                raise ValueError("Index file does not contain embeddings")

            vectors = loaded["embeddings"]

        # TODO: Add round-trip tests before using persisted indexes in the API:
        # - all TextChunk fields and vector values survive save/load;
        # - search results and similarity scores match before and after reload;
        # - missing/corrupt files and vector/chunk mismatches fail clearly.

        store = cls(vectors=vectors, chunks=chunks)

        logger.info(
            "Loaded vector store from %s (%s chunks)",
            path,
            len(store.chunks),
        )

        return store

    def validate(self) -> None:
        """Validate vector shape, values, and chunk alignment."""

        if self.vectors.ndim != 2:
            raise ValueError("Vectors must be a 2-D array")

        if self.vectors.shape[0] == 0 or self.vectors.shape[1] == 0:
            raise ValueError("Vector matrix cannot be empty")

        if self.vectors.shape[0] != len(self.chunks):
            raise ValueError("Vector and chunk counts must match")

        if not np.isfinite(self.vectors).all():
            raise ValueError("Vector matrix contains invalid values")
