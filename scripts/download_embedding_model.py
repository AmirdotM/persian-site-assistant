"""Complete a local multilingual E5 model download.

Download model.safetensors manually first; this script verifies it and fetches
the remaining small Sentence Transformers configuration/tokenizer files.
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

MODEL_REPO = "intfloat/multilingual-e5-small"
MODEL_REVISION = "97e13e802c05f5dbe5a86832df6d6f68b252e885"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "models" / "multilingual-e5-small"
WEIGHTS_PATH = MODEL_DIR / "model.safetensors"
WEIGHTS_SHA256 = "1a55775f53449dac10a2bcbc312469fac40b96d53198c407081a831f81c98477"

# Slow connections may need longer than Hugging Face's 10-second default.
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "60")
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "30")

# The large model weights are deliberately excluded: they must be provided
# manually so a failed metadata download never starts another 471 MB transfer.
MODEL_FILES = [
    "config.json",
    "modules.json",
    "sentence_bert_config.json",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "1_Pooling/config.json",
]


def sha256_file(path: Path) -> str:
    """Calculate a file's SHA-256 without loading it all into memory."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(4 * 1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def main() -> int:
    """Verify manual model weights and download the remaining model files."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if not WEIGHTS_PATH.is_file():
        print("The model weights have not been downloaded yet.", file=sys.stderr)
        print("Download this file:", file=sys.stderr)
        print(
            "https://huggingface.co/intfloat/multilingual-e5-small/"
            f"resolve/{MODEL_REVISION}/model.safetensors",
            file=sys.stderr,
        )
        print(f"Save it exactly here: {WEIGHTS_PATH}", file=sys.stderr)
        return 1

    print(f"Verifying model weights: {WEIGHTS_PATH}")
    actual_sha256 = sha256_file(WEIGHTS_PATH)

    if actual_sha256 != WEIGHTS_SHA256:
        print("The model weights checksum does not match.", file=sys.stderr)
        print(f"Expected: {WEIGHTS_SHA256}", file=sys.stderr)
        print(f"Actual:   {actual_sha256}", file=sys.stderr)
        print(
            "The file may be incomplete or corrupted. Re-download it before "
            "running this script again.",
            file=sys.stderr,
        )
        return 1

    print("Model weights verified.")
    print(f"Downloading the remaining files from {MODEL_REPO}...")

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print(
            'Missing download dependency. Install it with: '
            'python -m pip install -e ".[embeddings]"',
            file=sys.stderr,
        )
        return 1

    try:
        snapshot_download(
            repo_id=MODEL_REPO,
            revision=MODEL_REVISION,
            local_dir=MODEL_DIR,
            allow_patterns=MODEL_FILES,
            max_workers=2,
        )
    except Exception as exc:
        print(
            f"Download failed: {exc}\n"
            "Fix the connection and run this script again; the verified "
            "weights will not be downloaded again.",
            file=sys.stderr,
        )
        return 1

    required_files = [*MODEL_FILES, "model.safetensors"]
    missing_files = [
        file_name
        for file_name in required_files
        if not (MODEL_DIR / file_name).is_file()
    ]
    if missing_files:
        print(
            "Some required files are missing:\n"
            + "\n".join(f"  - {name}" for name in missing_files),
            file=sys.stderr,
        )
        return 1

    print("\nModel files are ready.")
    print("Set this in your .env file:")
    print("EMBEDDING_MODEL=./models/multilingual-e5-small")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
