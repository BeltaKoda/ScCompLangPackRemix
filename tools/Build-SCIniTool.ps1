# SC Global.ini Extractor - Build Script
# This script clones/updates the repo, sets up the environment, and builds the EXE

param(
    [switch]$SkipClone,
    [switch]$FreshClone,
    [string]$RepoUrl = "https://github.com/BeltaKoda/ScCompLangPackRemix.git",
    [string]$Branch = "beta/extraction-tool"
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Text)
    Write-Host ""
    Write-Host ">>> $Text" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Text)
    Write-Host "✗ ERROR: $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "  $Text" -ForegroundColor Gray
}

# ============================================================================
# Main Build Process
# ============================================================================

Write-Header "SC Global.ini Extractor - Build Script"

# Step 1: Clone or update repository (optional)
if (-not $SkipClone) {
    Write-Step "Step 1: Getting repository"

    $buildDir = Join-Path $PWD "build_temp"

    # Check if we should do a fresh clone
    if ($FreshClone -and (Test-Path $buildDir)) {
        Write-Info "FreshClone requested - removing existing build directory..."
        Remove-Item $buildDir -Recurse -Force
    }

    # Check if build_temp exists and is a valid git repo
    $gitDir = Join-Path $buildDir ".git"
    if ((Test-Path $buildDir) -and (Test-Path $gitDir)) {
        # Existing repo found - do git pull
        Write-Info "Found existing repository - updating..."
        Write-Info "Repository: $RepoUrl"
        Write-Info "Branch: $Branch"

        Push-Location $buildDir

        # Ensure we're on the correct branch
        git checkout $Branch 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning-Message "Branch checkout failed, doing fresh clone..."
            Pop-Location
            Remove-Item $buildDir -Recurse -Force
            git clone --branch $Branch --single-branch $RepoUrl $buildDir
        } else {
            # Pull latest changes
            git pull origin $Branch
            if ($LASTEXITCODE -ne 0) {
                Write-ErrorMsg "Git pull failed"
                Pop-Location
                exit 1
            }
            Pop-Location
            Write-Success "Repository updated successfully"
        }
    } else {
        # No existing repo - do fresh clone
        if (Test-Path $buildDir) {
            Write-Info "Removing invalid build directory..."
            Remove-Item $buildDir -Recurse -Force
        }

        Write-Info "Cloning from: $RepoUrl"
        Write-Info "Branch: $Branch"

        git clone --branch $Branch --single-branch $RepoUrl $buildDir

        if ($LASTEXITCODE -ne 0) {
            Write-ErrorMsg "Git clone failed"
            exit 1
        }

        Write-Success "Repository cloned successfully"
    }

    $toolsDir = Join-Path $buildDir "tools"
    Set-Location $toolsDir
} else {
    Write-Step "Step 1: Using existing directory (SkipClone enabled)"
    $toolsDir = $PWD
}

# Step 2: Check Python
Write-Step "Step 2: Checking Python installation"

$pythonCmd = $null
foreach ($cmd in @("python", "python3", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python 3\.") {
            $pythonCmd = $cmd
            Write-Success "Found Python: $version"
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonCmd) {
    Write-ErrorMsg "Python 3 not found!"
    Write-Info "Please install Python 3.8 or newer from:"
    Write-Info "https://www.python.org/downloads/"
    exit 1
}

# Step 3: Create virtual environment
Write-Step "Step 3: Creating Python virtual environment"

$venvDir = Join-Path $toolsDir "venv"
if (Test-Path $venvDir) {
    Write-Info "Removing existing virtual environment..."
    Remove-Item $venvDir -Recurse -Force
}

& $pythonCmd -m venv $venvDir

if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Failed to create virtual environment"
    exit 1
}

Write-Success "Virtual environment created"

# Activate virtual environment
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
. $activateScript

Write-Success "Virtual environment activated"

# Step 4: Install dependencies
Write-Step "Step 4: Installing Python dependencies"

Write-Info "Upgrading pip..."
python -m pip install --upgrade pip --quiet

Write-Info "Installing requirements..."
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Failed to install dependencies"
    exit 1
}

Write-Success "Dependencies installed"

# Step 5: Download unp4k.exe if needed
Write-Step "Step 5: Checking for unp4k.exe"

$unp4kPath = Join-Path $toolsDir "unp4k.exe"
if (Test-Path $unp4kPath) {
    Write-Success "unp4k.exe already present"
} else {
    Write-Info "unp4k.exe not found - you'll need to download it manually"
    Write-Info "Download from: https://github.com/dolkensp/unp4k/releases"
    Write-Info ""
    Write-Info "Extract these files to the tools/ directory:"
    Write-Info "  - unp4k.exe"
    Write-Info "  - All .dll files"
    Write-Info "  - x64/ folder"
    Write-Info "  - x86/ folder"
    Write-Info ""

    $response = Read-Host "Have you placed unp4k.exe and dependencies in tools/? (y/n)"
    if ($response -ne "y") {
        Write-ErrorMsg "Build cancelled - unp4k.exe is required"
        exit 1
    }

    if (-not (Test-Path $unp4kPath)) {
        Write-ErrorMsg "unp4k.exe still not found in tools/ directory"
        exit 1
    }

    Write-Success "unp4k.exe found"
}

# Verify dependencies exist
$missingFiles = @()
if (-not (Test-Path (Join-Path $toolsDir "ICSharpCode.SharpZipLib.dll"))) {
    $missingFiles += "ICSharpCode.SharpZipLib.dll"
}
if (-not (Test-Path (Join-Path $toolsDir "Zstd.Net.dll"))) {
    $missingFiles += "Zstd.Net.dll"
}
if (-not (Test-Path (Join-Path $toolsDir "x64"))) {
    $missingFiles += "x64/ folder"
}

if ($missingFiles.Count -gt 0) {
    Write-ErrorMsg "Missing required files:"
    foreach ($file in $missingFiles) {
        Write-Info "  - $file"
    }
    Write-Info ""
    Write-Info "Please download the complete unp4k-suite from:"
    Write-Info "https://github.com/dolkensp/unp4k/releases"
    exit 1
}

Write-Success "All unp4k dependencies present"

# Step 6: Build EXE with PyInstaller
Write-Step "Step 6: Building EXE with PyInstaller"

Write-Info "This may take 2-3 minutes..."
Write-Host ""

pyinstaller extract_tool.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "PyInstaller build failed"
    exit 1
}

Write-Success "EXE built successfully"

# Step 7: Verify output
Write-Step "Step 7: Verifying build output"

$distDir = Join-Path $toolsDir "dist"
$exePath = Join-Path $distDir "SC_GlobalIni_Extractor.exe"

if (-not (Test-Path $exePath)) {
    Write-ErrorMsg "EXE not found at expected location: $exePath"
    exit 1
}

$exeSize = [math]::Round((Get-Item $exePath).Length / 1MB, 2)
Write-Success "EXE found: $exePath"
Write-Info "Size: $exeSize MB"

# Step 8: Create release package
Write-Step "Step 8: Creating release package"

$releaseDir = Join-Path $PWD "release"
if (Test-Path $releaseDir) {
    Remove-Item $releaseDir -Recurse -Force
}
New-Item -ItemType Directory -Path $releaseDir | Out-Null

Copy-Item $exePath $releaseDir

# Create README for release
$readmeContent = @"
# SC Global.ini Extractor

## How to Use

1. Run SC_GlobalIni_Extractor.exe
2. The tool will automatically scan for Star Citizen installations
3. Select which installation (LIVE, PTU, EPTU, or HOTFIX)
4. Enter the Star Citizen version (e.g., 4.3.2)
5. Click "Extract global.ini"
6. The extracted file will be saved to: stock-global-ini/global-VERSION-BRANCH.ini

## Requirements

- Windows 10/11
- Star Citizen installed

## Support

For issues or questions, visit:
https://github.com/BeltaKoda/ScCompLangPackRemix

Not affiliated with Cloud Imperium Games.
"@

Set-Content -Path (Join-Path $releaseDir "README.txt") -Value $readmeContent

Write-Success "Release package created in: $releaseDir"

# Done!
Write-Header "BUILD COMPLETE!"

Write-Host ""
Write-Success "EXE Location: $exePath"
Write-Success "Release Package: $releaseDir"
Write-Host ""
Write-Info "You can now distribute the contents of the release/ folder"
Write-Host ""

# Cleanup option
if (-not $SkipClone) {
    Write-Host ""
    $cleanup = Read-Host "Delete build directory? (y/n)"
    if ($cleanup -eq "y") {
        Set-Location $PWD.Parent.Parent
        Remove-Item $buildDir -Recurse -Force
        Write-Success "Build directory cleaned up"
    }
}

Write-Host ""
Read-Host "Press Enter to exit"
