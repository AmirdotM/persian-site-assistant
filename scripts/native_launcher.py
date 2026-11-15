"""Start the packaged API from its portable application folder."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def application_root() -> Path:
    """Return the folder containing the executable and portable assets."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def main() -> None:
    """Load the API after switching to the portable application folder."""
    root = application_root()
    os.chdir(root)

    os.environ.setdefault("APP_ENV", "production")
    os.environ.setdefault("DATA_DIR", str(root / "data"))
    os.environ.setdefault(
        "EMBEDDING_MODEL",
        str(root / "models" / "multilingual-e5-small"),
    )
    os.environ.setdefault("EMBEDDING_DEVICE", "cpu")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("LLM_TIMEOUT_SECONDS", "120")

    port = int(os.environ.get("APP_PORT", "8000"))

    import uvicorn

    from site_assistant.main import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
