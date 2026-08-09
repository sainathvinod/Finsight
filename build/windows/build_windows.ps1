# FinSight — Windows build.
#
# Run from the repository root on a Windows machine with Python 3.12 (x64) available:
#     powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1
#
# Produces:
#     dist\FinSight\FinSight.exe          one-dir application
#     dist\FinSight-2.0.0-Setup.exe       installer (only when Inno Setup is installed)
#
# Creates its own build virtual environment so nothing depends on the developer's global
# interpreter. Fails loudly on the first error rather than producing a half-built package.

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
Write-Host "FinSight Windows build — repository root: $Root"

# --- 1. Interpreter -----------------------------------------------------------------------
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { $python = "py -3.12" } else { $python = "python" }
Write-Host "Using interpreter launcher: $python"

& cmd /c "$python -c ""import sys; assert sys.maxsize > 2**32, 'a 64-bit interpreter is required'; print('interpreter', sys.version)"""
if ($LASTEXITCODE -ne 0) { throw "A 64-bit Python 3.12 interpreter is required." }

# --- 2. Build environment -----------------------------------------------------------------
$BuildVenv = Join-Path $Root ".venv-winbuild"
if (-not (Test-Path $BuildVenv)) {
    Write-Host "Creating build virtual environment: $BuildVenv"
    & cmd /c "$python -m venv ""$BuildVenv"""
    if ($LASTEXITCODE -ne 0) { throw "Could not create the build virtual environment." }
}
$VenvPy = Join-Path $BuildVenv "Scripts\python.exe"

Write-Host "Installing pinned runtime and build dependencies"
& $VenvPy -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
& $VenvPy -m pip install -r (Join-Path $Root "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Runtime dependency installation failed." }
& $VenvPy -m pip install "PySide6==6.11.1" "QtAwesome==1.4.2" "QtPy==2.4.3" "pyinstaller==6.21.0"
if ($LASTEXITCODE -ne 0) { throw "Desktop/build dependency installation failed." }

# --- 3. Import check before packaging -----------------------------------------------------
# A missing native wheel is far cheaper to diagnose here than inside a frozen executable.
Write-Host "Verifying runtime imports"
$env:PYTHONPATH = Join-Path $Root "src"
& $VenvPy -c "import sqlcipher3, cryptography, openpyxl, PySide6, qtawesome, finsight; print('imports OK')"
if ($LASTEXITCODE -ne 0) { throw "Runtime import verification failed." }

# --- 4. Package ---------------------------------------------------------------------------
Write-Host "Running PyInstaller"
& $VenvPy -m PyInstaller --clean --noconfirm (Join-Path $Root "build\windows\finsight.spec")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

$ExePath = Join-Path $Root "dist\FinSight\FinSight.exe"
if (-not (Test-Path $ExePath)) { throw "Expected executable not produced: $ExePath" }
Write-Host "Built: $ExePath"

# --- 5. Packaged launch smoke -------------------------------------------------------------
# FINSIGHT_SMOKE starts the app, renders one event cycle and exits 0. This proves the frozen
# executable composes its services and opens its encrypted store on this machine.
Write-Host "Running packaged launch smoke"
$env:FINSIGHT_SMOKE = "1"
& $ExePath
$smoke = $LASTEXITCODE
Remove-Item Env:\FINSIGHT_SMOKE
if ($smoke -ne 0) { throw "Packaged launch smoke failed with exit code $smoke." }
Write-Host "Packaged launch smoke passed"

# --- 6. Installer -------------------------------------------------------------------------
$iscc = Get-Command iscc -ErrorAction SilentlyContinue
if (-not $iscc) {
    $candidate = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $candidate) { $iscc = $candidate } else { $iscc = $null }
}
if ($iscc) {
    Write-Host "Building installer with Inno Setup"
    & $iscc (Join-Path $Root "build\windows\finsight.iss")
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup build failed." }
    Write-Host "Installer: $(Join-Path $Root 'dist\FinSight-2.0.0-Setup.exe')"
} else {
    Write-Warning "Inno Setup (iscc) not found — the one-dir application was built but no installer was produced."
    Write-Warning "Install Inno Setup 6 and re-run, or ship dist\FinSight as a folder."
}

Write-Host "Windows build complete."
