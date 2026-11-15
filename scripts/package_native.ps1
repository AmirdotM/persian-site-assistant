$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$packageVenv = Join-Path $repoRoot ".venv-portable"
$pythonExecutable = Join-Path $packageVenv "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExecutable -PathType Leaf)) {
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pythonLauncher) {
        throw "The Python launcher was not found. Install Python 3.12 and enable the 'py' launcher."
    }

    Write-Host "Creating an isolated Python 3.12 packaging environment..."
    & $pythonLauncher.Source -3.12 -m venv $packageVenv
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the packaging environment. Confirm that Python 3.12 is installed."
    }
}

$pythonVersion = & $pythonExecutable -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0 -or $pythonVersion.Trim() -ne "3.12") {
    throw "The packaging environment must use Python 3.12. Remove .venv-portable and run this script again."
}

$modelDir = Join-Path $repoRoot "models\multilingual-e5-small"
$dataDir = Join-Path $repoRoot "data"
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
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required E5 model file is missing: $requiredFile. Run scripts/download_embedding_model.py first."
    }
}

$knowledgeBase = Join-Path $dataDir "raw\demo_company"
if (-not (Test-Path -LiteralPath $knowledgeBase -PathType Container)) {
    throw "The demo knowledge base is missing: $knowledgeBase"
}

foreach ($requiredDirectory in @("website", "widget")) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $requiredDirectory) -PathType Container)) {
        throw "Required application folder is missing: $requiredDirectory"
    }
}

Write-Host "Installing CPU-only PyTorch and the application packaging dependencies..."
& $pythonExecutable -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Could not upgrade pip in the packaging environment."
}

& $pythonExecutable -m pip install torch --index-url https://download.pytorch.org/whl/cpu
if ($LASTEXITCODE -ne 0) {
    throw "Could not install CPU-only PyTorch."
}

& $pythonExecutable -m pip install -e ".[embeddings]" sentencepiece "pyinstaller>=6.11"
if ($LASTEXITCODE -ne 0) {
    throw "Could not install the application or PyInstaller dependencies."
}

$previousEnvironment = @{
    "DATA_DIR" = $env:DATA_DIR
    "EMBEDDING_MODEL" = $env:EMBEDDING_MODEL
    "EMBEDDING_DEVICE" = $env:EMBEDDING_DEVICE
}
try {
    $env:DATA_DIR = $dataDir
    $env:EMBEDDING_MODEL = $modelDir
    $env:EMBEDDING_DEVICE = "cpu"

    Write-Host "Rebuilding the vector index using the local E5 model..."
    & $pythonExecutable "scripts/build_index.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Index build failed. Fix the error before packaging."
    }
}
finally {
    foreach ($name in $previousEnvironment.Keys) {
        $previousValue = $previousEnvironment[$name]
        if ($null -eq $previousValue) {
            Remove-Item "Env:$name" -ErrorAction SilentlyContinue
        }
        else {
            [Environment]::SetEnvironmentVariable($name, $previousValue, "Process")
        }
    }
}

$indexDirectory = Join-Path $dataDir "index"
foreach ($fileName in @("vector_store.npz", "vector_store.json")) {
    if (-not (Test-Path -LiteralPath (Join-Path $indexDirectory $fileName) -PathType Leaf)) {
        throw "The generated vector index is incomplete: $fileName"
    }
}

$releaseRoot = Join-Path $repoRoot "release"
$buildRoot = Join-Path $repoRoot "build\pyinstaller-native"
$distRoot = Join-Path $buildRoot "dist"
$workRoot = Join-Path $buildRoot "work"
$nativeBundle = Join-Path $releaseRoot "native-demo"

if (Test-Path -LiteralPath $distRoot) {
    Remove-Item -LiteralPath $distRoot -Recurse -Force
}
if (Test-Path -LiteralPath $workRoot) {
    Remove-Item -LiteralPath $workRoot -Recurse -Force
}
if (Test-Path -LiteralPath $nativeBundle) {
    Remove-Item -LiteralPath $nativeBundle -Recurse -Force
}
New-Item -ItemType Directory -Path $distRoot, $workRoot, $nativeBundle -Force | Out-Null

$pyInstallerArguments = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onedir",
    "--console",
    "--contents-directory", "_internal",
    "--name", "PersianSiteAssistant",
    "--paths", (Join-Path $repoRoot "src"),
    "--distpath", $distRoot,
    "--workpath", $workRoot
)

$packagesToCollect = @(
    "torch",
    "sentence_transformers",
    "transformers",
    "huggingface_hub",
    "tokenizers",
    "safetensors",
    "sentencepiece",
    "numpy",
    "scipy",
    "sklearn",
    "uvicorn"
)
foreach ($package in $packagesToCollect) {
    $pyInstallerArguments += @("--collect-all", $package)
}

$metadataPackages = @(
    "torch",
    "sentence-transformers",
    "transformers",
    "huggingface-hub",
    "tokenizers",
    "safetensors",
    "sentencepiece",
    "numpy",
    "scipy",
    "scikit-learn"
)
foreach ($package in $metadataPackages) {
    $pyInstallerArguments += @("--copy-metadata", $package)
}

$hiddenImports = @(
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.lifespan.on",
    "sentence_transformers.models",
    "transformers.models.auto.modeling_auto"
)
foreach ($module in $hiddenImports) {
    $pyInstallerArguments += @("--hidden-import", $module)
}

$pyInstallerArguments += (Join-Path $repoRoot "scripts\native_launcher.py")

Write-Host "Building the one-folder Windows application. PyTorch makes this a large bundle..."
& $pythonExecutable @pyInstallerArguments
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed. Review the build output above."
}

$builtApplication = Join-Path $distRoot "PersianSiteAssistant"
if (-not (Test-Path -LiteralPath (Join-Path $builtApplication "PersianSiteAssistant.exe") -PathType Leaf)) {
    throw "PyInstaller completed but the executable was not found."
}

Get-ChildItem -LiteralPath $builtApplication -Force |
    Copy-Item -Destination $nativeBundle -Recurse -Force

Write-Host "Copying the local model, index, knowledge base, website and widget..."
New-Item -ItemType Directory -Path (Join-Path $nativeBundle "data\raw"), (Join-Path $nativeBundle "data\index") -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $repoRoot "models") -Destination $nativeBundle -Recurse -Force
Get-ChildItem -LiteralPath (Join-Path $dataDir "raw") -Force | Copy-Item -Destination (Join-Path $nativeBundle "data\raw") -Recurse -Force
Get-ChildItem -LiteralPath $indexDirectory -Force | Copy-Item -Destination (Join-Path $nativeBundle "data\index") -Recurse -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "website") -Destination $nativeBundle -Recurse -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "widget") -Destination $nativeBundle -Recurse -Force

# Use the current origin for API requests, including when a non-default port is selected.
$htmlEncoding = [System.Text.UTF8Encoding]::new($false)
Get-ChildItem -LiteralPath (Join-Path $nativeBundle "website") -Filter "*.html" -Recurse -File |
    ForEach-Object {
        $html = [System.IO.File]::ReadAllText($_.FullName)
        $html = $html.Replace('data-api-url="http://127.0.0.1:8000"', 'data-api-url=""')
        [System.IO.File]::WriteAllText($_.FullName, $html, $htmlEncoding)
    }

Write-Host ""
Write-Host "Native Windows package created:"
Write-Host $nativeBundle
Write-Host "It includes the Python runtime, CPU-only dependencies, E5 model, vector index and website assets."
Write-Host "The LLM API key is not included. Use the launcher to enter it at runtime."
