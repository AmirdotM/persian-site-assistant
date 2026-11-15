"""Static checks for the portable Docker deployment contract."""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_index_builder_bootstraps_the_src_layout() -> None:
    script = read_project_file("scripts/build_index.py")

    assert 'Path(__file__).resolve().parents[1] / "src"' in script
    assert "sys.path.insert(0, str(SOURCE_ROOT))" in script


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
    assert "env_file:" not in compose
    assert "build:" not in compose
    assert '127.0.0.1:${WEB_PORT:-8080}:80' in compose
    assert '${LLM_API_KEY:?' in compose
    assert '${LLM_MODEL:?' in compose


def test_portable_packager_exports_images_but_not_local_env_file() -> None:
    script = read_project_file("scripts/package_portable.ps1")

    assert 'EMBEDDING_MODEL = "./models/multilingual-e5-small"' in script
    assert 'EMBEDDING_DEVICE = "cpu"' in script
    assert "docker image save" in script
    assert "images.tar" in script
    assert "tar -czf" in script
    assert 'Copy-Item ".env"' not in script
    assert 'Copy-Item "README_PORTABLE.md"' in script
    assert "start_portable.ps1" in script
    assert "docker compose @composeArgs up -d" in script
    assert '$env:LLM_API_KEY = "portable-preflight-placeholder"' in script
    assert "no provider key is needed" in script
    assert 'healthState -eq "healthy"' in script
    assert "wget -qO- http://127.0.0.1/ready" in script


def test_prefilled_assistant_question_handler_is_registered_once() -> None:
    widget = read_project_file("widget/widget.js")

    assert widget.count('window.addEventListener("psa:ask"') == 1


def test_product_catalog_page_lists_all_eight_recommendable_products() -> None:
    page = read_project_file("website/products.html")

    product_ids = (
        "RNA-WEB-01",
        "RNA-SHOP-02",
        "RNA-CRM-03",
        "RNA-FLOW-04",
        "RNA-STOCK-05",
        "RNA-INSIGHT-06",
        "RNA-KNOW-07",
        "RNA-BOOK-08",
    )

    assert page.count('class="product-card"') == 8
    assert all(product_id in page for product_id in product_ids)
    assert "data-product-search" in page
    assert "data-product-filter" in page


def test_portable_smoke_check_matches_the_complete_html_string() -> None:
    script = read_project_file("scripts/package_portable.ps1")

    assert "$productPageText = $productPage -join [Environment]::NewLine" in script
    assert '$productPageText.Contains("RNA-WEB-01")' in script
    assert '$productPage -notmatch "RNA-WEB-01"' not in script


def test_portable_compose_supports_a_custom_local_only_frontend_port() -> None:
    compose = read_project_file("deploy/compose.portable.yaml")
    assert '127.0.0.1:${WEB_PORT:-8080}:80' in compose
    assert '${LLM_API_KEY:?' in compose
    assert '${LLM_MODEL:?' in compose

    development_compose = read_project_file("compose.yaml")
    assert 'LLM_API_KEY: ${LLM_API_KEY:-local-demo-placeholder}' in development_compose
    assert 'LLM_MODEL: ${LLM_MODEL:-local-demo-placeholder}' in development_compose


def test_portable_launcher_is_one_command_and_does_not_store_the_api_key() -> None:
    script = read_project_file("scripts/start_portable.ps1")

    assert 'Read-Host "LLM API key" -AsSecureString' in script
    assert 'Read-Host "LLM model ID' in script
    assert 'docker info --format' in script
    assert 'docker load --input $imageArchive' in script
    assert 'Invoke-WebRequest -UseBasicParsing -Uri "$demoUrl/ready"' in script
    assert 'Start-Process $demoUrl' in script
    assert 'docker compose -p $projectName -f $composeFile down' in script
    assert '$env:LLM_API_KEY = $null' in script
    assert 'Set-Content' not in script

def test_widget_uses_the_current_origin_for_same_origin_deployments() -> None:
    widget = read_project_file("widget/widget.js")
    assert "configuredBaseIsLoopback && !pageIsLocal" in widget

