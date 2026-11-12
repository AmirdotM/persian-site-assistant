"""Run the retrieval and answer evaluation suite.

TODO: Implement a deterministic retrieval evaluation first. See IMPLEMENTATION_PLAN.md.

Implementation checklist:
1. Read evals/questions.jsonl one JSON object per line and validate each case.
2. Load the persisted vector store and create the configured E5 embedder/retriever.
3. Run each question through retrieval without calling the LLM.
4. Compare retrieved chunk source IDs with expected_source_ids at the configured top-k.
5. Report per-question hits/misses and an aggregate source-hit metric.
6. Treat should_abstain cases separately; report whether retrieval returned no
   sufficiently relevant results, but do not claim this proves answer quality.
7. Expand the test set to 10–15 cases and document the metric and known limitations.
"""


def main() -> None:
    raise NotImplementedError("Retrieval evaluation is not implemented yet")


if __name__ == "__main__":
    main()
