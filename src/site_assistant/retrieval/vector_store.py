"""In-memory NumPy vector search for a small demo index."""

from dataclasses import dataclass
from collections.abc import Sequence

import numpy as np

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

    def search(self, query_vector: np.ndarray, top_k: int = 4) -> list[SearchHit]:
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
