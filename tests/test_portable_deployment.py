"""Static checks for the portable Docker deployment contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_backend_image_bundles_model_and_generated_index() -> None:
    dockerfile = read_project_file("docker/backend.Dockerfile")

    assert "HF_HUB_OFFLINE=1" in dockerfile
    assert "TRANSFORMERS_OFFLINE=1" in dockerfile
    assert "COPY data/index ./data/index" in dockerfile
    assert "COPY data/raw ./data/raw" in dockerfile
    assert "COPY models/multilingual-e5-small" in dockerfile
    assert "EMBEDDING_MODEL=/app/models/multilingual-e5-small" in dockerfile


def test_nginx_routes_chat_and_health_to_api_container() -> None:
    nginx = read_project_file("docker/nginx.conf")
    widget = read_project_file("widget/widget.js")
    frontend = read_project_file("docker/frontend.Dockerfile")

    assert "proxy_pass http://api:8000;" in nginx
    assert "location /api/" in nginx
    assert "location = /ready" in nginx
    assert "window.location.origin" in widget
    assert 'data-api-url=""' in frontend


def test_portable_compose_uses_prebuilt_images_without_build_context() -> None:
    compose = read_project_file("deploy/compose.portable.yaml")

    assert "persian-site-assistant-api:portable" in compose
    assert "persian-site-assistant-web:portable" in compose
    assert "env_file:" in compose
    assert "build:" not in compose
    assert '"8080:80"' in compose


def test_portable_packager_exports_images_but_not_local_env_file() -> None:
    script = read_project_file("scripts/package_portable.ps1")

    assert "docker image save" in script
    assert "images.tar" in script
    assert "tar -czf" in script
    assert 'Copy-Item ".env.example"' in script
    assert 'Copy-Item ".env"' not in script
    assert "start_portable.ps1" in script
