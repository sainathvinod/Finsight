# FinSight — Ask Fin runtime provisioning (Windows).
#
# Installs the local AI runtime FinSight's optional Ask Fin assistant uses, so a non-technical
# user never opens a terminal. Invoked by the installer's optional "Set up Ask Fin" task, or
# re-runnable later from the Start Menu entry.
#
#   powershell -ExecutionPolicy Bypass -File provision_ask_fin.ps1 [-ModelName llama3.2:3b] [-Quiet]
#
# WHY THIS IS OPTIONAL AND SEPARATE FROM THE APPLICATION
#   FinSight's deterministic review — intake, verification, validation, findings, reporting — runs
#   with no AI provider at all (FR-095). Ask Fin only ever explains results that already exist.
#   Provisioning is therefore never a precondition for installing or using FinSight: if it is
#   skipped, declined, or fails, FinSight still installs, launches, and completes a full review,
#   and Ask Fin simply reports itself unavailable.
#
# EXIT CODES
#   0  runtime ready (Ollama installed, service reachable, model present)
#   2  no network / download failed        — FinSight remains fully usable without Ask Fin
#   3  Ollama installed but service unreachable
#   4  model download failed
#   5  user declined
#
# Nothing here touches FinSight's encrypted store, review data, or configuration.

[CmdletBinding()]
param(
    [string]$ModelName = "llama3.2:3b",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # keeps Invoke-WebRequest from painting a progress UI

$OllamaApi = "http://127.0.0.1:11434"
$OllamaDownload = "https://ollama.com/download/OllamaSetup.exe"

function Write-Step([string]$Message) {
    if (-not $Quiet) { Write-Host "[FinSight] $Message" }
}

function Get-OllamaCommand {
    $cmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    # Ollama's Windows installer is per-user by default; check the standard locations too.
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
        (Join-Path $env:ProgramFiles "Ollama\ollama.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Test-OllamaService {
    try {
        Invoke-RestMethod -Uri "$OllamaApi/api/tags" -TimeoutSec 5 -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Start-OllamaService([string]$OllamaExe) {
    if (Test-OllamaService) { return $true }
    Write-Step "Starting the local AI service"
    try {
        Start-Process -FilePath $OllamaExe -ArgumentList "serve" -WindowStyle Hidden | Out-Null
    } catch {
        return $false
    }
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        if (Test-OllamaService) { return $true }
    }
    return $false
}

# --- 1. Ollama present? --------------------------------------------------------------------
$ollama = Get-OllamaCommand
if (-not $ollama) {
    Write-Step "Local AI runtime not found — downloading Ollama"
    $installer = Join-Path $env:TEMP "OllamaSetup.exe"
    try {
        Invoke-WebRequest -Uri $OllamaDownload -OutFile $installer -UseBasicParsing -TimeoutSec 600
    } catch {
        Write-Warning "Could not download the local AI runtime. FinSight is fully usable without Ask Fin; run this setup again when a connection is available."
        exit 2
    }

    Write-Step "Installing Ollama (no restart, no user interaction)"
    try {
        # Ollama's Windows installer is Inno Setup based and installs per-user by default.
        $process = Start-Process -FilePath $installer -ArgumentList "/VERYSILENT", "/NORESTART" -Wait -PassThru
        if ($process.ExitCode -ne 0) { throw "installer exit code $($process.ExitCode)" }
    } catch {
        Write-Warning "The local AI runtime could not be installed automatically. FinSight remains fully usable without Ask Fin."
        exit 2
    } finally {
        Remove-Item $installer -ErrorAction SilentlyContinue
    }

    $ollama = Get-OllamaCommand
    if (-not $ollama) {
        Write-Warning "Ollama installed but its program could not be located."
        exit 3
    }
} else {
    Write-Step "Local AI runtime already installed"
}

# --- 2. Service reachable on loopback? -----------------------------------------------------
if (-not (Start-OllamaService $ollama)) {
    Write-Warning "The local AI service did not become reachable. FinSight remains fully usable without Ask Fin."
    exit 3
}
Write-Step "Local AI service is reachable on 127.0.0.1"

# --- 3. Approved model present? ------------------------------------------------------------
$havemodel = $false
try {
    $tags = Invoke-RestMethod -Uri "$OllamaApi/api/tags" -TimeoutSec 10
    $havemodel = @($tags.models | Where-Object { $_.name -eq $ModelName }).Count -gt 0
} catch {
    $havemodel = $false
}

if ($havemodel) {
    Write-Step "Model '$ModelName' already present"
} else {
    Write-Step "Downloading model '$ModelName' (about 2 GB, one time)"
    try {
        & $ollama pull $ModelName
        if ($LASTEXITCODE -ne 0) { throw "pull exit code $LASTEXITCODE" }
    } catch {
        Write-Warning "The language model could not be downloaded. FinSight remains fully usable without Ask Fin."
        exit 4
    }
}

# --- 4. Verify end to end ------------------------------------------------------------------
try {
    $tags = Invoke-RestMethod -Uri "$OllamaApi/api/tags" -TimeoutSec 10
    if (-not (@($tags.models | Where-Object { $_.name -eq $ModelName }).Count -gt 0)) {
        Write-Warning "The model is not reporting as available after download."
        exit 4
    }
} catch {
    exit 3
}

Write-Step "Ask Fin is ready. Open FinSight and select Ask Fin."
exit 0
