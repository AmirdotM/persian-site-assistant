"""Download the project's multilingual E5 embedding model."""

from __future__ import annotations

import sys
from pathlib import Path

MODEL_REPO = "intfloat/multilingual-e5-small"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "models" / "multilingual-e5-small"

# Only the PyTorch/Sentence Transformers files needed by this project.
# In particular, do not download the duplicate pytorch_model.bin or ONNX exports.
MODEL_FILES = [
    "config.json",
    "model.safetensors",
    "modules.json",
    "sentence_bert_config.json",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "1_Pooling/config.json",
]


def main() -> int:
    """Download the selected model files into the local project directory."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print(
            'Missing download dependency. Install it with: '
            'python -m pip install -e ".[embeddings]"',
            file=sys.stderr,
        )
        return 1

    print(f"Model: {MODEL_REPO}")
    print(f"Destination: {MODEL_DIR}")
    print("Downloading required files only...")

    try:
        snapshot_download(
            repo_id=MODEL_REPO,
            local_dir=MODEL_DIR,
            allow_patterns=MODEL_FILES,
            max_workers=2,
        )
    except Exception as exc:
        print(
            f"Download failed: {exc}\n"
            "You can run this script again after fixing the connection; "
            "the Hugging Face downloader will reuse its local download metadata.",
            file=sys.stderr,
        )
        return 1

    missing_files = [
        file_name
        for file_name in MODEL_FILES
        if not (MODEL_DIR / file_name).is_file()
    ]
    if missing_files:
        print(
            "Download finished, but some required files are missing:\n"
            + "\n".join(f"  - {name}" for name in missing_files),
            file=sys.stderr,
        )
        return 1

    print("\nModel downloaded successfully.")
    print("Set this in your .env file:")
    print("EMBEDDING_MODEL=./models/multilingual-e5-small")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
