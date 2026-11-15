$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$releaseRoot = Join-Path $repoRoot "release"
$nativeSource = Join-Path $releaseRoot "native-demo"
$dockerSource = Join-Path $releaseRoot "portable-demo"
$demoBundle = Join-Path $releaseRoot "demo"

Write-Host "Building the native Windows package..."
& (Join-Path $PSScriptRoot "package_native.ps1")
if (-not (Test-Path -LiteralPath (Join-Path $nativeSource "PersianSiteAssistant.exe") -PathType Leaf)) {
    throw "Native packaging failed. The executable was not created."
}

# A previous Docker export must not be mistaken for a fresh successful build.
if (Test-Path -LiteralPath $dockerSource) {
    Remove-Item -LiteralPath $dockerSource -Recurse -Force
}

$dockerBuilt = $false
Write-Host ""
Write-Host "Building the Docker package..."
try {
    & (Join-Path $PSScriptRoot "package_portable.ps1") -SkipIndexBuild
    if (Test-Path -LiteralPath (Join-Path $dockerSource "images.tar") -PathType Leaf) {
        $dockerBuilt = $true
    }
    else {
        throw "The Docker packaging script finished without producing images.tar."
    }
}
catch {
    Write-Warning "Docker packaging did not complete: $($_.Exception.Message)"
    Write-Warning "The native Windows package is still available and will be assembled on its own."
}

if (Test-Path -LiteralPath $demoBundle) {
    Remove-Item -LiteralPath $demoBundle -Recurse -Force
}
$nativeTarget = Join-Path $demoBundle "native"
New-Item -ItemType Directory -Path $nativeTarget -Force | Out-Null

Get-ChildItem -LiteralPath $nativeSource -Force |
    Copy-Item -Destination $nativeTarget -Recurse -Force

if ($dockerBuilt) {
    $dockerTarget = Join-Path $demoBundle "docker"
    New-Item -ItemType Directory -Path $dockerTarget -Force | Out-Null
    Get-ChildItem -LiteralPath $dockerSource -Force |
        Copy-Item -Destination $dockerTarget -Recurse -Force
}

Copy-Item -LiteralPath (Join-Path $PSScriptRoot "start_demo.bat") -Destination (Join-Path $demoBundle "START-DEMO.bat")
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "start_native.ps1") -Destination (Join-Path $demoBundle "START-NATIVE.ps1")
Copy-Item -LiteralPath (Join-Path $repoRoot "README_PORTABLE.md") -Destination (Join-Path $demoBundle "README.md")

if (-not $dockerBuilt) {
    $readmePath = Join-Path $demoBundle "README.md"
    $readme = [System.IO.File]::ReadAllText($readmePath)
    $readme += @"

## وضعیت این بسته

در زمان ساخت، بسته Docker آماده نشد؛ بنابراین این نسخه فقط شامل اجرای Native ویندوز است. گزینه Docker در منوی شروع در دسترس نخواهد بود. فایل اجرایی و وابستگی‌ها در پوشه \`native\` قرار دارند.
"@
    [System.IO.File]::WriteAllText(
        $readmePath,
        $readme,
        [System.Text.UTF8Encoding]::new($false)
    )
}

Write-Host ""
Write-Host "USB demo package created:"
Write-Host $demoBundle
if ($dockerBuilt) {
    Write-Host "Available modes: Native Windows and Docker."
}
else {
    Write-Warning "Available mode: Native Windows only. Docker output was not created."
}
Write-Host ""
Write-Host "Copy the complete 'demo' folder to the USB drive."
Write-Host "Run START-DEMO.bat on the presentation PC."
