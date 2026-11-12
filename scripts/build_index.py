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


def main() -> None:
    raise NotImplementedError("Index-building workflow is not implemented yet")


if __name__ == "__main__":
    main()
