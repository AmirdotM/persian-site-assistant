$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

Write-Host "Building the native Windows package..."
& (Join-Path $PSScriptRoot "package_native.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "Native packaging failed."
}

Write-Host ""
Write-Host "Building the Docker package..."
& (Join-Path $PSScriptRoot "package_portable.ps1") -SkipIndexBuild
if ($LASTEXITCODE -ne 0) {
    throw "Docker packaging failed."
}

$releaseRoot = Join-Path $repoRoot "release"
$nativeSource = Join-Path $releaseRoot "native-demo"
$dockerSource = Join-Path $releaseRoot "portable-demo"
$demoBundle = Join-Path $releaseRoot "demo"

foreach ($source in @($nativeSource, $dockerSource)) {
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "A packaging output is missing: $source"
    }
}

if (Test-Path -LiteralPath $demoBundle) {
    Remove-Item -LiteralPath $demoBundle -Recurse -Force
}
$nativeTarget = Join-Path $demoBundle "native"
$dockerTarget = Join-Path $demoBundle "docker"
New-Item -ItemType Directory -Path $nativeTarget, $dockerTarget -Force | Out-Null

Get-ChildItem -LiteralPath $nativeSource -Force |
    Copy-Item -Destination $nativeTarget -Recurse -Force
Get-ChildItem -LiteralPath $dockerSource -Force |
    Copy-Item -Destination $dockerTarget -Recurse -Force

Copy-Item -LiteralPath (Join-Path $PSScriptRoot "start_demo.bat") -Destination (Join-Path $demoBundle "START-DEMO.bat")
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "start_native.ps1") -Destination (Join-Path $demoBundle "START-NATIVE.ps1")
Copy-Item -LiteralPath (Join-Path $repoRoot "README_PORTABLE.md") -Destination (Join-Path $demoBundle "README.md")

Write-Host ""
Write-Host "Combined USB demo package created:"
Write-Host $demoBundle
Write-Host ""
Write-Host "Copy the complete 'demo' folder to the USB drive."
Write-Host "Run START-DEMO.bat on the presentation PC and choose native or Docker mode."
