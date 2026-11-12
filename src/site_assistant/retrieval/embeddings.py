"""Multilingual E5 embedding adapter.

E5 expects `passage: ` prefixes for indexed documents and `query: ` for user questions.
"""

from collections.abc import Sequence

import numpy as np

from site_assistant.config import settings


class E5Embedder:
    def __init__(self, model_name: str | None = None, device: str | None = None) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                'Install the embedding dependencies: pip install -e ".[embeddings]"'
            ) from exc

        self.model = SentenceTransformer(
            model_name or settings.embedding_model,
            device=device or settings.embedding_device,
        )

    def embed_passages(self, texts: Sequence[str]) -> np.ndarray:
        """Embed document chunks. E5 models expect the passage instruction prefix."""
        prepared = [f"passage: {text}" for text in texts]
        return self.model.encode(
            prepared,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)

    def embed_query(self, question: str) -> np.ndarray:
        """Embed one user question with the E5 query instruction prefix."""
        vector = self.model.encode(
            [f"query: {question}"],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vector[0].astype(np.float32)
