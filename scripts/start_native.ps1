$ErrorActionPreference = "Stop"
$nativeDir = Join-Path $PSScriptRoot "native"
$executable = Join-Path $nativeDir "PersianSiteAssistant.exe"
$process = $null
$apiKey = $null

$environmentNames = @(
    "APP_ENV",
    "APP_PORT",
    "DATA_DIR",
    "EMBEDDING_MODEL",
    "EMBEDDING_DEVICE",
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "LLM_TIMEOUT_SECONDS"
)
$previousEnvironment = @{}
foreach ($name in $environmentNames) {
    $previousEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
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

function Read-LocalPort {
    while ($true) {
        $answer = Read-Host "Local web port [8000]"
        if ([string]::IsNullOrWhiteSpace($answer)) {
            $answer = "8000"
        }

        $port = 0
        if (-not [int]::TryParse($answer, [ref]$port) -or $port -lt 1024 -or $port -gt 65535) {
            Write-Host "Enter a port between 1024 and 65535."
            continue
        }

        $listener = [System.Net.Sockets.TcpListener]::new(
            [System.Net.IPAddress]::Loopback,
            $port
        )
        $started = $false
        try {
            $listener.Start()
            $started = $true
            return $port
        }
        catch {
            Write-Host "Port $port is already in use. Choose another one."
        }
        finally {
            if ($started) {
                $listener.Stop()
            }
        }
    }
}

try {
    if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
        throw "The native application is missing. Re-copy the complete demo folder."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $nativeDir "data\index\vector_store.npz") -PathType Leaf)) {
        throw "The vector index is missing from the native folder."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $nativeDir "models\multilingual-e5-small\model.safetensors") -PathType Leaf)) {
        throw "The E5 model is missing from the native folder."
    }

    Write-Host ""
    Write-Host "Persian Site Assistant - native Windows mode"
    Write-Host "The API, website, E5 embeddings and retrieval run locally."
    Write-Host "Only answer generation uses the configured LLM provider."
    Write-Host "Your API key is requested for this run and is not saved to the demo folder."
    Write-Host ""

    $secureKey = Read-Host "LLM API key" -AsSecureString
    $apiKey = ConvertFrom-SecureInput $secureKey
    $secureKey = $null
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        throw "An LLM API key is required."
    }

    $model = (Read-Host "LLM model ID (the exact name from your provider)").Trim()
    if ([string]::IsNullOrWhiteSpace($model)) {
        throw "An LLM model ID is required."
    }

    $baseUrl = (Read-Host "LLM base URL (leave blank for the default OpenAI endpoint)").Trim()
    $port = Read-LocalPort

    $env:APP_ENV = "production"
    $env:APP_PORT = [string]$port
    $env:DATA_DIR = Join-Path $nativeDir "data"
    $env:EMBEDDING_MODEL = Join-Path $nativeDir "models\multilingual-e5-small"
    $env:EMBEDDING_DEVICE = "cpu"
    $env:LLM_API_KEY = $apiKey
    $env:LLM_BASE_URL = $baseUrl
    $env:LLM_MODEL = $model
    $env:LLM_TIMEOUT_SECONDS = "120"

    Write-Host ""
    Write-Host "Starting the local API and loading the E5 model..."
    Write-Host "The first startup can take a few minutes. Keep this window open."

    $process = Start-Process -FilePath $executable -WorkingDirectory $nativeDir -NoNewWindow -PassThru

    $demoUrl = "http://127.0.0.1:$port"
    $deadline = (Get-Date).AddMinutes(8)
    $ready = $false

    while ((Get-Date) -lt $deadline) {
        if ($process.HasExited) {
            throw "The native application stopped before becoming ready. Review its log output above."
        }

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
        throw "The API did not become ready within eight minutes. Review the application log output above."
    }

    Write-Host ""
    Write-Host "The demo is ready: $demoUrl"
    Write-Host "Opening the website. Keep this window open during the presentation."
    Write-Host "Press Enter here when you want to stop the demo."
    Start-Process $demoUrl
    [void](Read-Host "Press Enter to stop")
}
catch {
    Write-Host ""
    Write-Host "Could not start the native demo: $($_.Exception.Message)" -ForegroundColor Red
    throw
}
finally {
    if ($null -ne $process -and -not $process.HasExited) {
        Write-Host ""
        Write-Host "Stopping the native application..."
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        [void]$process.WaitForExit(10000)
    }

    foreach ($name in $environmentNames) {
        $previousValue = $previousEnvironment[$name]
        if ($null -eq $previousValue) {
            Remove-Item "Env:$name" -ErrorAction SilentlyContinue
        }
        else {
            [Environment]::SetEnvironmentVariable($name, $previousValue, "Process")
        }
    }

    $apiKey = $null
    $secureKey = $null
}
