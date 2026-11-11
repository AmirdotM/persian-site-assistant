"""In-memory NumPy vector search for a small demo index."""

from asyncio.log import logger
from collections.abc import Sequence
from dataclasses import dataclass

import os
import json
from typing import Dict, List, Union
import numpy as np
from pathlib import Path
import logging

from site_assistant.ingestion.chunker import TextChunk


@dataclass(frozen=True, slots=True)
class SearchHit:
    chunk: TextChunk
    score: float


class NumpyVectorStore:
    """Minimal vector store; vectors are expected to be L2-normalized."""

    def __init__(self, vectors: np.ndarray, chunks: Sequence[TextChunk]) -> None:
        if len(vectors) != len(chunks):
            raise ValueError("Each vector must map to exactly one chunk")
        if len(vectors) == 0:
            raise ValueError("The vector store cannot be empty")
        self.vectors = np.asarray(vectors, dtype=np.float32)
        self.chunks = list(chunks)

    def search(self, query_vector: np.ndarray, top_k: int = 4) -> List[SearchHit]:
        """Return the top-k chunks by cosine similarity (dot product if normalized)."""
        query = np.asarray(query_vector, dtype=np.float32).reshape(-1)
        if query.shape[0] != self.vectors.shape[1]:
            raise ValueError("Query vector dimension does not match indexed vectors")
        query_norm = np.linalg.norm(query)
        if query_norm == 0:
            raise ValueError("Query vector cannot be all zeros")
        query = query / query_norm
        scores = self.vectors @ query
        count = min(max(top_k, 0), len(self.chunks))
        indices = np.argsort(scores)[::-1][:count]
        return [SearchHit(self.chunks[int(i)], float(scores[int(i)])) for i in indices]

    # TODO: add index persistence.
    # ---------------------------------------------------------------------
    # Persistence helpers
    # ---------------------------------------------------------------------
    def save(self, path: Path) -> None:
        """Save the store to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save chunks and metadata as JSON
        data = {
            "chunks": self.chunks,
            "metadata": self.metadata,
        }

        json_path = path.with_suffix(".json")
        json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Save embeddings as numpy array
        np.savez_compressed(path, embeddings=self._get_matrix())

        logger.info(f"Saved vector store to {path}")

    def load(self, path: Path) -> None:
        """Load the store from disk."""
        try:
            # Load chunks and metadata
            json_path = path.with_suffix(".json")
            if json_path.exists():
                data = json.loads(json_path.read_text(encoding="utf-8"))
                self.chunks = data.get("chunks", [])
                self.metadata = data.get("metadata", [])

            # Load embeddings
            if path.exists():
                with np.load(path) as loaded:
                    # Convert back to list of lists for consistency
                    matrix = loaded["embeddings"]
                    self.embeddings = matrix.tolist()
                    self._matrix = matrix

            logger.info(f"Loaded vector store from {path} ({len(self.chunks)} items)")
        except Exception as e:
            logger.error(f"Failed to load vector store from {path}: {e}")
            # Reset on failure
            self.embeddings = []
            self.chunks = []
            self.metadata = []
            self._matrix = None

    def validate(self) -> None:
        """Validate vector/chunk counts and vector dimensions.

        Raises
        ------
        ValueError
            If validation fails.
        """
        if len(self.vectors) != len(self.chunks):
            raise ValueError("Vector and chunk counts must match")
        if self.vectors.ndim != 2 or self.vectors.shape[0] == 0:
            raise ValueError("Vectors must be a 2-D array with at least one vector")
