$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env" -PathType Leaf)) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env. Add your LLM_API_KEY, LLM_BASE_URL and LLM_MODEL, then run this script again."
    exit 1
}

$requiredNames = @("LLM_API_KEY", "LLM_MODEL")
foreach ($name in $requiredNames) {
    $line = Select-String -Path ".env" -Pattern ("^\s*" + $name + "\s*=\s*.+$")
    if (-not $line) {
        throw "Configure $name in .env before starting the application."
    }
}

docker load --input "images.tar"
if ($LASTEXITCODE -ne 0) {
    throw "Could not load the application images."
}

docker compose up -d
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose could not start the application."
}

Write-Host ""
Write-Host "Persian Site Assistant is starting."
Write-Host "Open http://localhost:8080 in your browser."
Write-Host "Use 'docker compose logs -f api' to watch the backend."
