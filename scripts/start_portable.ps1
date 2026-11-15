$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$composeFile = Join-Path $PSScriptRoot "compose.yaml"
$imageArchive = Join-Path $PSScriptRoot "images.tar"
$projectName = "persian-site-assistant-demo"
$composeStarted = $false
$apiKey = $null

function Read-LocalPort {
    while ($true) {
        $answer = Read-Host "Local web port [8080]"
        if ([string]::IsNullOrWhiteSpace($answer)) {
            $answer = "8080"
        }

        $port = 0
        if (-not [int]::TryParse($answer, [ref]$port) -or $port -lt 1024 -or $port -gt 65535) {
            Write-Host "Enter a port between 1024 and 65535."
            continue
        }

        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
        try {
            $listener.Start()
            return $port
        }
        catch {
            Write-Host "Port $port is already in use. Choose another one."
        }
        finally {
            $listener.Stop()
        }
    }
}

function ConvertFrom-SecureInput([System.Security.SecureString]$Value) {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Value)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
}

try {
    if (-not (Test-Path -LiteralPath $imageArchive -PathType Leaf)) {
        throw "images.tar is missing. Keep START-HERE.ps1, compose.yaml and images.tar in the same folder."
    }
    if (-not (Test-Path -LiteralPath $composeFile -PathType Leaf)) {
        throw "compose.yaml is missing. Re-copy the complete portable-demo folder."
    }
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker Desktop is required on this computer. Install and start Docker Desktop, then run this script again."
    }

    $dockerOs = docker info --format '{{.OSType}}' 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running. Start Docker Desktop and wait until it says it is running."
    }
    if ($dockerOs -ne "linux") {
        throw "Docker Desktop must be using Linux containers. Switch to Linux containers and try again."
    }

    docker compose version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose is not available. Update Docker Desktop and try again."
    }

    Write-Host ""
    Write-Host "Persian Site Assistant - demo setup"
    Write-Host "The website and RAG model run locally. Only LLM generation uses the provider API."
    Write-Host "The API key is requested for this run and is not written to the USB folder."
    Write-Host ""

    $secureKey = Read-Host "LLM API key" -AsSecureString
    $apiKey = ConvertFrom-SecureInput $secureKey
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        throw "An LLM API key is required."
    }

    $env:LLM_MODEL = (Read-Host "LLM model ID (the exact name from your provider)").Trim()
    if ([string]::IsNullOrWhiteSpace($env:LLM_MODEL)) {
        throw "An LLM model ID is required."
    }

    $env:LLM_BASE_URL = (Read-Host "LLM base URL (leave blank for the default OpenAI endpoint)").Trim()
    $env:LLM_API_KEY = $apiKey
    $env:WEB_PORT = [string](Read-LocalPort)

    Write-Host ""
    Write-Host "Loading the prebuilt application images. This can take a little while..."
    docker load --input $imageArchive
    if ($LASTEXITCODE -ne 0) {
        throw "Docker could not load images.tar. Check that Docker Desktop is healthy and that there is enough disk space."
    }

    Write-Host "Starting the website and API..."
    $composeStarted = $true
    docker compose -p $projectName -f $composeFile up -d
    if ($LASTEXITCODE -ne 0) {
        throw "The application containers could not be started. The logs will be shown below."
    }

    $demoUrl = "http://127.0.0.1:$env:WEB_PORT"
    $deadline = (Get-Date).AddMinutes(5)
    $ready = $false

    Write-Host "Waiting for the API and E5 model to become ready..."
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri "$demoUrl/ready" -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
            Start-Sleep -Seconds 3
        }
    }

    if (-not $ready) {
        docker compose -p $projectName -f $composeFile logs --tail=100 api
        throw "The demo did not become ready within five minutes. Check the API log above."
    }

    Write-Host ""
    Write-Host "The demo is ready: $demoUrl"
    Write-Host "The browser will open now. Keep this window open during the presentation."
    Write-Host "Press Enter (or Ctrl+C) here when you want to stop the demo."
    Start-Process $demoUrl
    [void](Read-Host "Press Enter to stop")

}
catch {
    Write-Host ""
    Write-Host "Could not start the demo: $($_.Exception.Message)" -ForegroundColor Red
    if ($composeStarted) {
        docker compose -p $projectName -f $composeFile logs --tail=100 api
    }
    exit 1
}
finally {
    if ($composeStarted) {
        Write-Host ""
        Write-Host "Stopping the demo containers..."
        docker compose -p $projectName -f $composeFile down
    }

    $env:LLM_API_KEY = $null
    $env:LLM_MODEL = $null
    $env:LLM_BASE_URL = $null
    $env:WEB_PORT = $null
    $apiKey = $null
}
