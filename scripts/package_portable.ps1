$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$modelDir = Join-Path $repoRoot "models\multilingual-e5-small"
$indexVectors = Join-Path $repoRoot "data\index\vector_store.npz"
$indexMetadata = Join-Path $repoRoot "data\index\vector_store.json"

$requiredModelFiles = @(
    "model.safetensors",
    "config.json",
    "modules.json",
    "sentence_bert_config.json",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "1_Pooling\config.json"
)

foreach ($relativePath in $requiredModelFiles) {
    $requiredFile = Join-Path $modelDir $relativePath
    if (-not (Test-Path $requiredFile -PathType Leaf)) {
        throw "Required E5 model file is missing: $requiredFile. Run scripts/download_embedding_model.py first."
    }
}

foreach ($requiredFile in @($indexVectors, $indexMetadata)) {
    if (-not (Test-Path $requiredFile -PathType Leaf)) {
        throw "Required vector-index file is missing: $requiredFile. Build the index first."
    }
}

if (-not (Test-Path ".env" -PathType Leaf)) {
    Copy-Item ".env.example" ".env"
    throw "Created .env from .env.example. Configure LLM_API_KEY and LLM_MODEL, then run packaging again."
}

foreach ($name in @("LLM_API_KEY", "LLM_MODEL")) {
    $line = Select-String -Path ".env" -Pattern ("^\s*" + $name + "\s*=\s*.+$")
    if (-not $line) {
        throw "Configure $name in .env before building and testing the portable package."
    }
}

$dockerOs = docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) {
    throw "Docker is not running. Start Docker Desktop and try again."
}
if ($dockerOs -ne "linux") {
    throw "Switch Docker Desktop to Linux containers before building this package."
}

Write-Host "Rebuilding the vector index from the current knowledge base using the bundled local E5 model..."
$previousEmbeddingModel = $env:EMBEDDING_MODEL
$previousEmbeddingDevice = $env:EMBEDDING_DEVICE
try {
    $env:EMBEDDING_MODEL = "./models/multilingual-e5-small"
    $env:EMBEDDING_DEVICE = "cpu"
    python "scripts/build_index.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Index build failed. Fix the error before packaging."
    }
}
finally {
    if ($null -eq $previousEmbeddingModel) {
        Remove-Item Env:EMBEDDING_MODEL -ErrorAction SilentlyContinue
    }
    else {
        $env:EMBEDDING_MODEL = $previousEmbeddingModel
    }
    if ($null -eq $previousEmbeddingDevice) {
        Remove-Item Env:EMBEDDING_DEVICE -ErrorAction SilentlyContinue
    }
    else {
        $env:EMBEDDING_DEVICE = $previousEmbeddingDevice
    }
}

Write-Host "Validating Docker Compose configuration..."
docker compose -f "compose.yaml" config --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose configuration is invalid."
}

Write-Host "Building the API and website images..."
docker compose -f "compose.yaml" build
if ($LASTEXITCODE -ne 0) {
    throw "Docker image build failed."
}

# Run an isolated preflight project so packaging does not interfere with a
# normal development Compose project. Use a dedicated port to avoid collisions.
$previousWebPort = $env:WEB_PORT
$env:WEB_PORT = "18080"
$composeArgs = @("-p", "psa-package-check", "-f", "compose.yaml")
try {
    Write-Host "Starting the built images for an isolated readiness and frontend check..."
    docker compose @composeArgs up -d
    if ($LASTEXITCODE -ne 0) {
        throw "The portable images could not start."
    }

    $deadline = (Get-Date).AddMinutes(8)
    $apiHealthy = $false
    while ((Get-Date) -lt $deadline) {
        $apiContainer = docker compose @composeArgs ps -q api
        if ($LASTEXITCODE -ne 0 -or -not $apiContainer) {
            Start-Sleep -Seconds 5
            continue
        }

        $containerState = docker inspect --format '{{.State.Status}}' $apiContainer
        $healthState = docker inspect --format '{{.State.Health.Status}}' $apiContainer
        if ($containerState -eq "exited" -or $healthState -eq "unhealthy") {
            docker compose @composeArgs logs --tail=100 api
            throw "The API container failed its startup health check."
        }
        if ($healthState -eq "healthy") {
            $apiHealthy = $true
            break
        }
        Start-Sleep -Seconds 10
    }

    if (-not $apiHealthy) {
        docker compose @composeArgs logs --tail=100 api
        throw "The API did not become ready within eight minutes."
    }

    docker compose @composeArgs exec -T web wget -qO- http://127.0.0.1/ready | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Nginx could not proxy the readiness endpoint to FastAPI."
    }

    $productPage = docker compose @composeArgs exec -T web wget -qO- http://127.0.0.1/products.html
    $productPageText = $productPage -join [Environment]::NewLine
    if ($LASTEXITCODE -ne 0 -or -not $productPageText.Contains("RNA-WEB-01")) {
        throw "The product catalogue page did not pass its frontend check."
    }

    Write-Host "Preflight passed: API ready, Nginx proxy ready, and product catalogue served."
}
finally {
    docker compose @composeArgs down
    if ($null -eq $previousWebPort) {
        Remove-Item Env:WEB_PORT -ErrorAction SilentlyContinue
    }
    else {
        $env:WEB_PORT = $previousWebPort
    }
}

$releaseRoot = Join-Path $repoRoot "release"
$bundleDir = Join-Path $releaseRoot "portable-demo"
$archivePath = Join-Path $releaseRoot "persian-site-assistant-portable.tar.gz"

if (Test-Path $bundleDir) {
    Remove-Item $bundleDir -Recurse -Force
}
New-Item -ItemType Directory -Path $bundleDir -Force | Out-Null

Write-Host "Exporting Docker images..."
docker image save --output (Join-Path $bundleDir "images.tar") "persian-site-assistant-api:portable" "persian-site-assistant-web:portable"
if ($LASTEXITCODE -ne 0) {
    throw "Could not export Docker images."
}

Copy-Item "deploy\compose.portable.yaml" (Join-Path $bundleDir "compose.yaml")
Copy-Item ".env.example" (Join-Path $bundleDir ".env.example")
Copy-Item "README_PORTABLE.md" (Join-Path $bundleDir "README.md")
Copy-Item "scripts\start_portable.ps1" (Join-Path $bundleDir "START-HERE.ps1")

if (Test-Path $archivePath) {
    Remove-Item $archivePath -Force
}
if (-not (Get-Command tar -ErrorAction SilentlyContinue)) {
    throw "The tar command was not found. Use an up-to-date Windows 10/11 system or install bsdtar."
}
tar -czf $archivePath -C $bundleDir .
if ($LASTEXITCODE -ne 0) {
    throw "Could not create the portable tar.gz archive."
}

Write-Host ""
Write-Host "Portable package created:"
Write-Host $archivePath
Write-Host "The archive contains prebuilt API and web images, the local E5 model, the knowledge base, and the vector index."
Write-Host "It does not contain your .env or API key. Configure a separate .env on the destination system."
