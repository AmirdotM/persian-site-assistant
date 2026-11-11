"""Retrieval orchestration and low-confidence fallback."""

from site_assistant.config import settings
from site_assistant.retrieval.embeddings import E5Embedder
from site_assistant.retrieval.vector_store import NumpyVectorStore, SearchHit


class Retriever:
    def __init__(
        self,
        embedder: E5Embedder,
        vector_store: NumpyVectorStore,
        *,
        top_k: int | None = None,
        min_score: float | None = None,
    ) -> None:
        self.embedder = embedder
        self.vector_store = vector_store
        self.top_k = top_k if top_k is not None else settings.retrieval_top_k
        self.min_score = min_score if min_score is not None else settings.retrieval_min_score

    def search(self, question: str) -> list[SearchHit]:
        """Retrieve relevant passages."""
        query_vector = self.embedder.embed_query(question)
        hits = self.vector_store.search(query_vector, top_k=self.top_k)
        return [hit for hit in hits if hit.score >= self.min_score]
