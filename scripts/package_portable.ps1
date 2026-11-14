$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$modelWeights = Join-Path $repoRoot "models\multilingual-e5-small\model.safetensors"
$indexVectors = Join-Path $repoRoot "data\index\vector_store.npz"
$indexMetadata = Join-Path $repoRoot "data\index\vector_store.json"

foreach ($requiredFile in @($modelWeights, $indexVectors, $indexMetadata)) {
    if (-not (Test-Path $requiredFile -PathType Leaf)) {
        throw "Required portable asset is missing: $requiredFile. Download the E5 model and rebuild the index first."
    }
}

if (-not (Test-Path ".env" -PathType Leaf)) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Configure your hosted LLM API key before starting the application."
}

$dockerOs = docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) {
    throw "Docker is not running. Start Docker Desktop and try again."
}
if ($dockerOs -ne "linux") {
    throw "Switch Docker Desktop to Linux containers before building this package."
}

Write-Host "Rebuilding the vector index from the current knowledge base..."
python "scripts/build_index.py"
if ($LASTEXITCODE -ne 0) {
    throw "Index build failed. Fix the error before packaging."
}

Write-Host "Building the API and website images..."
docker compose -f "compose.yaml" build
if ($LASTEXITCODE -ne 0) {
    throw "Docker image build failed."
}

$releaseRoot = Join-Path $repoRoot "release"
$bundleDir = Join-Path $releaseRoot "portable-demo"
$zipPath = Join-Path $releaseRoot "persian-site-assistant-portable.zip"

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

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}
Compress-Archive -Path (Join-Path $bundleDir "*") -DestinationPath $zipPath -CompressionLevel Optimal

Write-Host ""
Write-Host "Portable package created:"
Write-Host $zipPath
Write-Host "The archive contains the app images, website, E5 model, knowledge base and vector index."
Write-Host "It does not contain your .env or API key. Configure a separate .env on the destination system."
