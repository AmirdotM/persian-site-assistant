"""Tests for the index-building orchestration."""

from types import SimpleNamespace

import numpy as np
import pytest

import scripts.build_index as build_index_module
from site_assistant.ingestion.chunker import TextChunk
from site_assistant.retrieval.vector_store import NumpyVectorStore


def _sample_chunks() -> list[TextChunk]:
    return [
        TextChunk(
            chunk_id="about:0",
            source_id="about",
            title="About",
            text="متن معرفی شرکت",
            chunk_index=0,
        ),
        TextChunk(
            chunk_id="faq:0",
            source_id="faq",
            title="FAQ",
            text="ساعات کاری شرکت",
            chunk_index=0,
        ),
    ]


def test_build_index_embeds_chunks_and_saves_store(tmp_path, monkeypatch) -> None:
    chunks = _sample_chunks()
    vectors = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ],
        dtype=np.float32,
    )

    class FakeEmbedder:
        def __init__(self, *, model_name: str, device: str) -> None:
            assert model_name == "test-model"
            assert device == "cpu"

        def embed_passages(self, texts: list[str]) -> np.ndarray:
            assert texts == [chunk.text for chunk in chunks]
            return vectors

    monkeypatch.setattr(build_index_module, "build_chunks", lambda: chunks)
    monkeypatch.setattr(build_index_module, "E5Embedder", FakeEmbedder)
    monkeypatch.setattr(
        build_index_module,
        "settings",
        SimpleNamespace(
            data_dir=tmp_path,
            embedding_model="test-model",
            embedding_device="cpu",
        ),
    )

    saved_path = build_index_module.build_index()

    assert saved_path == tmp_path / "index" / "vector_store.npz"
    assert saved_path.is_file()
    assert saved_path.with_suffix(".json").is_file()

    loaded_store = NumpyVectorStore.load(saved_path)
    assert np.array_equal(loaded_store.vectors, vectors)
    assert loaded_store.chunks == chunks


def test_build_index_rejects_an_empty_corpus(monkeypatch) -> None:
    class UnexpectedEmbedder:
        def __init__(self, **kwargs) -> None:
            pytest.fail("The embedder should not initialize for an empty corpus.")

    monkeypatch.setattr(build_index_module, "build_chunks", lambda: [])
    monkeypatch.setattr(build_index_module, "E5Embedder", UnexpectedEmbedder)

    with pytest.raises(ValueError, match="No text chunks"):
        build_index_module.build_index()


def test_build_index_rejects_a_mismatched_embedding_count(monkeypatch, tmp_path) -> None:
    chunks = _sample_chunks()

    class WrongShapeEmbedder:
        def __init__(self, **kwargs) -> None:
            pass

        def embed_passages(self, texts: list[str]) -> np.ndarray:
            return np.ones((1, 3), dtype=np.float32)

    monkeypatch.setattr(build_index_module, "build_chunks", lambda: chunks)
    monkeypatch.setattr(build_index_module, "E5Embedder", WrongShapeEmbedder)
    monkeypatch.setattr(
        build_index_module,
        "settings",
        SimpleNamespace(
            data_dir=tmp_path,
            embedding_model="test-model",
            embedding_device="cpu",
        ),
    )

    with pytest.raises(ValueError, match="Embedding/chunk count mismatch"):
        build_index_module.build_index()
