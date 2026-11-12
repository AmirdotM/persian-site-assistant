"""Tests for NumPy vector-store persistence."""

import numpy as np

from site_assistant.ingestion.chunker import TextChunk
from site_assistant.retrieval.vector_store import NumpyVectorStore


def test_vector_store_round_trip(tmp_path) -> None:
    chunk = TextChunk(
        chunk_id="test_source:0",
        source_id="test_source",
        title="Test Title",
        text="Sample text",
        url="https://example.test",
        chunk_index=0,
    )
    # The store expects normalized passage vectors; this unit vector keeps
    # the expected cosine-similarity result straightforward.
    vectors = np.array([[1.0, 0.0, 0.0]], dtype=np.float32)
    store = NumpyVectorStore(vectors=vectors, chunks=[chunk])
    query = np.array([1.0, 0.0, 0.0], dtype=np.float32)

    original_hits = store.search(query, top_k=1)

    save_path = tmp_path / "vector_store.npz"
    store.save(save_path)
    loaded_store = NumpyVectorStore.load(save_path)
    loaded_hits = loaded_store.search(query, top_k=1)

    assert np.array_equal(store.vectors, loaded_store.vectors)
    assert loaded_store.chunks == store.chunks
    assert loaded_hits == original_hits
