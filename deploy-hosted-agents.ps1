#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy the WebSearchAgent hosted agent to Microsoft Foundry.
.DESCRIPTION
    Reads resource values from the repo .env and uses the Azure Developer CLI
    (azd) to build and deploy the WebSearchAgent container to Azure Container
    Apps via Microsoft Foundry Hosted Agents.

    Requires provision.ps1 to have been run first (needs .env and a Bing
    Grounding connection).
.PARAMETER EnvName
    Name for the azd environment (default: websearch-agent).
.PARAMETER SkipLogin
    Skip azd auth login if you are already authenticated in this session.
.PARAMETER Down
    Tear down the deployed agent instead of deploying.
.EXAMPLE
    pwsh deploy-hosted-agents.ps1
.EXAMPLE
    pwsh deploy-hosted-agents.ps1 -Down
#>
param(
    [string]$EnvName  = "websearch-agent",
    [switch]$SkipLogin,
    [switch]$Down
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot       = $PSScriptRoot
$HostedDir      = Join-Path $RepoRoot "hosted-agents"
$EnvFile        = Join-Path $RepoRoot ".env"

function Write-Step    { param([string]$m) Write-Host "`n▶  $m" -ForegroundColor Blue }
function Write-Success { param([string]$m) Write-Host "  ✓ $m" -ForegroundColor Green }
function Write-Warn    { param([string]$m) Write-Host "  ⚠  $m" -ForegroundColor Yellow }
function Write-Err     { param([string]$m) Write-Host "  ✗ $m" -ForegroundColor Red }

# ── azd present? ───────────────────────────────────────────────────────────────
if (-not (Get-Command azd -ErrorAction SilentlyContinue)) {
    Write-Err "Azure Developer CLI (azd) is not installed."
    Write-Host ""
    Write-Host "  macOS/Linux:  brew tap azure/azd && brew install azd"
    Write-Host "  Windows:      winget install microsoft.azd"
    Write-Host "  Docs:         https://aka.ms/install-azd"
    exit 1
}

# ── azd ai extension ───────────────────────────────────────────────────────────
Write-Step "Checking azd azure.ai.agents extension..."
$extOut = azd extension list --installed 2>&1
if ($extOut -notmatch "azure\.ai\.agents") {
    Write-Warn "Extension not installed — installing now..."
    azd extension install azure.ai.agents | Out-Null
    Write-Success "Extension installed"
} else {
    Write-Success "Extension present"
}

# ── Read .env ──────────────────────────────────────────────────────────────────
if (-not (Test-Path $EnvFile)) {
    Write-Err ".env not found at $EnvFile — run provision.ps1 first."
    exit 1
}

Write-Step "Reading .env..."
$ev = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') { $ev[$Matches[1].Trim()] = $Matches[2].Trim() }
}

$need = "AZURE_SUBSCRIPTION_ID","AZURE_RESOURCE_GROUP","AZURE_PROJECT_NAME",
        "PROJECT_RESOURCE_ID","AI_FOUNDRY_PROJECT_ENDPOINT","BING_CONNECTION_ID"
$missing = $need | Where-Object { -not $ev[$_] }
if ($missing) {
    Write-Err "Missing from .env: $($missing -join ', ')"
    Write-Host "  Re-run provision.ps1 with Bing Grounding enabled."
    exit 1
}
Write-Success "Values loaded"

# ── Work inside hosted-agents/ ─────────────────────────────────────────────────
Push-Location $HostedDir
try {

    # ── Tear-down path ─────────────────────────────────────────────────────────
    if ($Down) {
        Write-Step "Tearing down WebSearchAgent..."
        azd down --force --purge
        Write-Success "Agent resources removed"
        exit 0
    }

    # ── Authenticate ───────────────────────────────────────────────────────────
    if (-not $SkipLogin) {
        Write-Step "Signing in to Azure Developer CLI..."
        azd auth login
    }

    # ── Init azd environment (idempotent) ──────────────────────────────────────
    $azdDir = Join-Path $HostedDir ".azure"
    if (-not (Test-Path $azdDir)) {
        Write-Step "Initialising azd environment '$EnvName'..."
        azd init -e $EnvName
        Write-Success "Environment created"
    } else {
        Write-Success "azd environment already initialised"
    }

    # ── Populate azd env vars from .env ────────────────────────────────────────
    Write-Step "Configuring azd environment..."
    azd env set AZURE_SUBSCRIPTION_ID       $ev["AZURE_SUBSCRIPTION_ID"]
    azd env set AZURE_RESOURCE_GROUP        $ev["AZURE_RESOURCE_GROUP"]
    azd env set AZURE_AI_PROJECT_NAME       $ev["AZURE_PROJECT_NAME"]
    azd env set AZURE_AI_PROJECT_ID         $ev["PROJECT_RESOURCE_ID"]
    azd env set AI_FOUNDRY_PROJECT_ENDPOINT $ev["AI_FOUNDRY_PROJECT_ENDPOINT"]
    Write-Success "Variables set"

    # ── Agent init (interactive) ───────────────────────────────────────────────
    Write-Step "Initialising hosted agent configuration (interactive)..."
    Write-Host ""
    Write-Host "  You will be prompted for model and container settings." -ForegroundColor DarkGray
    Write-Host "  Recommended values:" -ForegroundColor DarkGray
    Write-Host "    Model SKU        -> GlobalStandard" -ForegroundColor Cyan
    Write-Host "    Model deployment -> gpt-4o" -ForegroundColor Cyan
    Write-Host "    Memory           -> 2Gi" -ForegroundColor Cyan
    Write-Host "    CPU              -> 1" -ForegroundColor Cyan
    Write-Host "    Min replicas     -> 1" -ForegroundColor Cyan
    Write-Host "    Max replicas     -> 3" -ForegroundColor Cyan
    Write-Host ""
    azd ai agent init

    # ── Deploy ─────────────────────────────────────────────────────────────────
    Write-Step "Deploying WebSearchAgent (typically 5–10 minutes)..."
    azd deploy

    Write-Host ""
    Write-Success "WebSearchAgent deployed successfully"
    Write-Host ""
    Write-Host "  Open the Agent playground URL shown above to test the agent." -ForegroundColor Cyan
    Write-Host "  To remove:  pwsh deploy-hosted-agents.ps1 -Down" -ForegroundColor DarkGray

} finally {
    Pop-Location
}
