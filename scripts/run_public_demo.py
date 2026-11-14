"""Start a protected, Docker-free public demo using a Cloudflare Quick Tunnel.

Run with the project's virtual-environment Python interpreter:

    python scripts/run_public_demo.py
"""

from __future__ import annotations

import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
PORT = 8765
READY_TIMEOUT_SECONDS = 120
EMAIL_PATTERN = re.compile(r"^[^@\s,]+@[^@\s,]+\.[^@\s,]+$")
TUNNEL_URL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.I)


def read_env_file(path: Path) -> dict[str, str]:
    """Read the small KEY=VALUE subset used by the project's .env file."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value

    return values


def validate_prerequisites() -> tuple[str, str]:
    """Check local model, index, provider configuration and cloudflared."""
    env_path = ROOT / ".env"
    env_values = read_env_file(env_path)
    if not env_values.get("LLM_API_KEY") or not env_values.get("LLM_MODEL"):
        raise RuntimeError(
            "Configure LLM_API_KEY and LLM_MODEL in the project .env file first."
        )

    required_files = (
        ROOT / "data" / "index" / "vector_store.npz",
        ROOT / "data" / "index" / "vector_store.json",
        ROOT / "models" / "multilingual-e5-small" / "model.safetensors",
    )
    missing = [str(path.relative_to(ROOT)) for path in required_files if not path.is_file()]
    if missing:
        raise RuntimeError(
            "Required local RAG assets are missing: "
            + ", ".join(missing)
            + ". Build the vector index and download the E5 model first."
        )

    cloudflared = shutil.which("cloudflared") or shutil.which("cloudflared.exe")
    if not cloudflared:
        raise RuntimeError(
            "cloudflared was not found on PATH. Install it once from "
            "https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/"
            "downloads/ and open a new PowerShell window."
        )

    return cloudflared, env_values.get("LLM_BASE_URL", "")


def prompt_allowed_emails() -> list[str]:
    """Require an explicit email allow-list for the temporary public URL."""
    while True:
        raw_value = input(
            "Allowed visitor email(s), comma-separated (required): "
        ).strip()
        emails = [item.strip().lower() for item in raw_value.split(",") if item.strip()]
        if emails and all(EMAIL_PATTERN.fullmatch(email) for email in emails):
            return emails
        print(
            "Enter at least one valid email address. "
            "No public unauthenticated mode is offered."
        )


def ensure_port_is_free(host: str, port: int) -> None:
    """Fail clearly rather than accidentally tunnelling to another local service."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError as exc:
            raise RuntimeError(
                f"Local port {port} is already in use. Stop the other service and retry."
            ) from exc


def wait_for_api_ready(process: subprocess.Popen[bytes], port: int) -> None:
    """Wait for FastAPI and the local E5 model to finish their startup."""
    ready_url = f"http://127.0.0.1:{port}/ready"
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    print("Starting FastAPI and loading the local E5 model...")

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"FastAPI exited during startup with code {process.returncode}. "
                "Read the server log above."
            )
        try:
            with urlopen(ready_url, timeout=2) as response:
                if response.status == 200:
                    print("API is ready.")
                    return
        except (OSError, URLError):
            time.sleep(1)

    raise RuntimeError(
        f"FastAPI did not become ready within {READY_TIMEOUT_SECONDS} seconds."
    )


def forward_tunnel_output(process: subprocess.Popen[str], allowed_emails: list[str]) -> None:
    """Print Cloudflare logs and announce the generated URL when available."""
    if process.stdout is None:
        return

    for line in process.stdout:
        print("[cloudflared] " + line, end="", flush=True)
        match = TUNNEL_URL_PATTERN.search(line)
        if match:
            print("\n" + "=" * 68)
            print("PUBLIC DEMO IS READY")
            print(match.group(0))
            print("Email verification is required for: " + ", ".join(allowed_emails))
            print("Visitors receive a one-time PIN by email.")
            print("Keep this window open while the demo is being used.")
            print("Press Ctrl+C here to shut down the tunnel and local API.")
            print("=" * 68 + "\n", flush=True)


def stop_process(process: subprocess.Popen[object] | None) -> None:
    """Stop a child process and wait briefly for a clean shutdown."""
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def run() -> int:
    os.chdir(ROOT)
    cloudflared, llm_base_url = validate_prerequisites()
    allowed_emails = prompt_allowed_emails()
    ensure_port_is_free("127.0.0.1", PORT)

    environment = os.environ.copy()
    environment.update(
        {
            "APP_ENV": "public_demo",
            "PUBLIC_DEMO_MODE": "true",
            "PUBLIC_DEMO_RATE_LIMIT_PER_MINUTE": "12",
            "EMBEDDING_MODEL": str(ROOT / "models" / "multilingual-e5-small"),
            "EMBEDDING_DEVICE": "cpu",
        }
    )

    print("\nSecurity settings:")
    print("- FastAPI binds to 127.0.0.1 only; no inbound Windows firewall port is opened.")
    print("- Cloudflare email verification restricts the temporary public URL.")
    print("- Chat is limited to 12 requests per visitor per rolling minute.")
    print("- Interactive API documentation is disabled for this public session.")
    print("- The LLM API key stays in your local .env file.")
    if llm_base_url and ("localhost" in llm_base_url or "127.0.0.1" in llm_base_url):
        print("- Your configured LLM endpoint is local; keep that provider running on this PC.")

    api_command = [
        sys.executable,
        "-m",
        "uvicorn",
        "site_assistant.main:app",
        "--app-dir",
        str(ROOT / "src"),
        "--host",
        "127.0.0.1",
        "--port",
        str(PORT),
    ]
    api_process: subprocess.Popen[bytes] | None = None
    tunnel_process: subprocess.Popen[str] | None = None

    try:
        api_process = subprocess.Popen(api_command, cwd=ROOT, env=environment)
        wait_for_api_ready(api_process, PORT)

        tunnel_command = [
            cloudflared,
            "tunnel",
            "--no-autoupdate",
            "--url",
            f"http://127.0.0.1:{PORT}",
            "--allowed-mail",
            ",".join(allowed_emails),
        ]
        print("\nStarting the email-restricted Cloudflare Quick Tunnel...")
        tunnel_process = subprocess.Popen(
            tunnel_command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        threading.Thread(
            target=forward_tunnel_output,
            args=(tunnel_process, allowed_emails),
            daemon=True,
        ).start()

        while api_process.poll() is None and tunnel_process.poll() is None:
            time.sleep(0.5)

        if tunnel_process.poll() is not None:
            print(
                f"Cloudflare Tunnel exited with code {tunnel_process.returncode}.",
                file=sys.stderr,
            )
            return int(tunnel_process.returncode or 1)
        print("FastAPI stopped unexpectedly.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopping the public demo...")
        return 0
    finally:
        stop_process(tunnel_process)
        stop_process(api_process)


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except (OSError, RuntimeError) as exc:
        print(f"\nCannot start the public demo: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
