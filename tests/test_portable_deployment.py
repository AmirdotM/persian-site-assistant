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
    assert "env_file:" in compose
    assert "build:" not in compose
    assert '${WEB_PORT:-8080}:80' in compose


def test_portable_packager_exports_images_but_not_local_env_file() -> None:
    script = read_project_file("scripts/package_portable.ps1")

    assert 'EMBEDDING_MODEL = "./models/multilingual-e5-small"' in script
    assert 'EMBEDDING_DEVICE = "cpu"' in script
    assert "docker image save" in script
    assert "images.tar" in script
    assert "tar -czf" in script
    assert 'Copy-Item ".env.example"' in script
    assert 'Copy-Item ".env"' not in script
    assert "start_portable.ps1" in script
    assert "docker compose @composeArgs up -d" in script
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


def test_portable_compose_supports_a_custom_frontend_port() -> None:
    compose = read_project_file("deploy/compose.portable.yaml")
    assert '${WEB_PORT:-8080}:80' in compose


def test_portable_launcher_reports_the_configured_web_port() -> None:
    script = read_project_file("scripts/start_portable.ps1")

    assert 'Select-String -Path ".env" -Pattern "^\\s*WEB_PORT' in script
    assert 'Open http://localhost:$webPort' in script

def test_native_public_demo_uses_loopback_cloudflare_email_gate_and_rate_limit() -> None:
    runner = read_project_file("scripts/run_public_demo.py")
    main = read_project_file("src/site_assistant/main.py")
    routes = read_project_file("src/site_assistant/api/routes.py")
    widget = read_project_file("widget/widget.js")

    assert '"127.0.0.1"' in runner
    assert '"--allowed-mail"' in runner
    assert '"PUBLIC_DEMO_MODE": "true"' in runner
    assert '"PUBLIC_DEMO_RATE_LIMIT_PER_MINUTE": "12"' in runner
    assert 'docs_url=None if settings.public_demo_mode else "/docs"' in main
    assert "settings.public_demo_mode" in routes
    assert "status.HTTP_429_TOO_MANY_REQUESTS" in routes
    assert "configuredBaseIsLoopback && !pageIsLocal" in widget

