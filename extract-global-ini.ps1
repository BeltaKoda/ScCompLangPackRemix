# Extract global.ini from Star Citizen Data.p4k
# This script extracts the latest global.ini from your Star Citizen installation

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Star Citizen global.ini Extractor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if unp4k.exe exists in the same directory
$unp4kPath = Join-Path $PSScriptRoot "unp4k.exe"
if (-not (Test-Path $unp4kPath)) {
    Write-Host "ERROR: unp4k.exe not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download unp4k from:" -ForegroundColor Yellow
    Write-Host "https://github.com/dolkensp/unp4k/releases" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Extract unp4k.exe to the same folder as this script:" -ForegroundColor Yellow
    Write-Host $PSScriptRoot -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Found unp4k.exe" -ForegroundColor Green
Write-Host ""

# Common Star Citizen installation paths
$commonPaths = @(
    "C:\Program Files\Roberts Space Industries\StarCitizen\LIVE\Data.p4k",
    "D:\Program Files\Roberts Space Industries\StarCitizen\LIVE\Data.p4k",
    "E:\Program Files\Roberts Space Industries\StarCitizen\LIVE\Data.p4k",
    "C:\Games\Roberts Space Industries\StarCitizen\LIVE\Data.p4k",
    "D:\Games\Roberts Space Industries\StarCitizen\LIVE\Data.p4k"
)

# Try to find Data.p4k automatically
$datap4kPath = $null
foreach ($path in $commonPaths) {
    if (Test-Path $path) {
        $datap4kPath = $path
        Write-Host "✓ Found Star Citizen installation at:" -ForegroundColor Green
        Write-Host "  $datap4kPath" -ForegroundColor White
        break
    }
}

# If not found, ask user
if (-not $datap4kPath) {
    Write-Host "Could not find Star Citizen installation automatically." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please enter the full path to Data.p4k:" -ForegroundColor Yellow
    Write-Host "Example: C:\Program Files\Roberts Space Industries\StarCitizen\LIVE\Data.p4k" -ForegroundColor Gray
    Write-Host ""

    $datap4kPath = Read-Host "Path to Data.p4k"

    if (-not (Test-Path $datap4kPath)) {
        Write-Host ""
        Write-Host "ERROR: File not found at: $datap4kPath" -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "Extracting global.ini from Data.p4k..." -ForegroundColor Cyan
Write-Host "This may take a minute..." -ForegroundColor Gray
Write-Host ""

# Create temporary extraction directory
$tempDir = Join-Path $PSScriptRoot "temp_extraction"
if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Extract global.ini
try {
    $process = Start-Process -FilePath $unp4kPath -ArgumentList "`"$datap4kPath`" `"*global.ini`"" -WorkingDirectory $tempDir -Wait -PassThru -NoNewWindow

    if ($process.ExitCode -ne 0) {
        throw "unp4k.exe exited with error code: $($process.ExitCode)"
    }

    # Find the extracted global.ini
    $extractedGlobalIni = Get-ChildItem -Path $tempDir -Filter "global.ini" -Recurse | Select-Object -First 1

    if (-not $extractedGlobalIni) {
        throw "global.ini was not found in the extracted files"
    }

    Write-Host "✓ Successfully extracted global.ini" -ForegroundColor Green
    Write-Host ""

    # Copy to the project location
    $targetPath = Join-Path $PSScriptRoot "data\Localization\english\global.ini"
    $targetDir = Split-Path $targetPath -Parent

    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }

    # Backup existing global.ini if it exists
    if (Test-Path $targetPath) {
        $backupPath = Join-Path $PSScriptRoot "global.ini.backup"
        Copy-Item $targetPath $backupPath -Force
        Write-Host "✓ Backed up existing global.ini to: global.ini.backup" -ForegroundColor Yellow
    }

    # Copy the new file
    Copy-Item $extractedGlobalIni.FullName $targetPath -Force
    Write-Host "✓ Copied global.ini to: data\Localization\english\global.ini" -ForegroundColor Green

    # Get file size
    $fileSize = [math]::Round((Get-Item $targetPath).Length / 1MB, 2)
    Write-Host "✓ File size: $fileSize MB" -ForegroundColor Green

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "The stock global.ini has been extracted." -ForegroundColor White
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Apply your component renaming process" -ForegroundColor White
    Write-Host "  2. Test the changes in-game" -ForegroundColor White
    Write-Host "  3. Create a new release" -ForegroundColor White

} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to extract global.ini" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
} finally {
    # Clean up temporary directory
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
}

Write-Host ""
Read-Host "Press Enter to exit"
