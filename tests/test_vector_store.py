'''
test_vector_store.py 
for save/load round-trip (all TextChunk fields, vector values/shape, and identical search results), missing files, corrupt metadata, invalid dimensions, non-finite values, and vector/chunk count mismatch.
Keep embedding-model downloads out of unit tests. 
Update CI to install the [rag] extra when NumPy tests are included.

'''
from math import e

import numpy as np
import pytest
from site_assistant.retrieval.vector_store import TextChunk, VectorStore

def test_vector_store_round_trip(tmp_path) -> None:
    # Create a simple vector store with one chunk and a 2-D vector array
    chunk = TextChunk(
        text="Sample text",
        source_id="test_source",
        title="Test Title",
        metadata={"key": "value"},
    )
    vectors = np.array([[0.1, 0.2, 0.3]], dtype=np.float32)
    store = VectorStore(vectors=vectors, chunks=[chunk])

    # Save the vector store to a temporary path
    try:
        save_path = tmp_path / "vector_store.npz"
        store.save(save_path)
    except Exception as e:
        pytest.fail(f"Saving vector store failed: {e}")
    
    # Load the vector store back from the saved file
    try:
        loaded_store = VectorStore.load(save_path)
    except Exception as e:
        pytest.fail(f"Loading vector store failed: {e}")

    # Validate that the loaded store matches the original
    assert np.array_equal(store.vectors, loaded_store.vectors)
    assert len(store.chunks) == len(loaded_store.chunks)
    assert store.chunks[0].text == loaded_store.chunks[0].text
    assert store.chunks[0].source_id == loaded_store.chunks[0].source_id
    assert store.chunks[0].title == loaded_store.chunks[0].title
    assert store.chunks[0].metadata == loaded_store.chunks[0].metadata