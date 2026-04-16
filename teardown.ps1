#!/usr/bin/env pwsh

# ============================================================================
# Azure Resource Teardown Script
# Deletes all workshop resources by removing the resource group
# ============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step    { param([string]$msg) Write-Host "`n▶ $msg" -ForegroundColor Blue }
function Write-Success { param([string]$msg) Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn    { param([string]$msg) Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Err     { param([string]$msg) Write-Host "  ✗ $msg" -ForegroundColor Red }

# ---------------------------------------------------------------------------
# Read a value from the .env file
# ---------------------------------------------------------------------------
function Get-EnvValue {
    param([string]$Key, [string]$EnvPath)
    $line = Get-Content $EnvPath | Where-Object { $_ -match "^$Key=" } | Select-Object -First 1
    if (-not $line) { return $null }
    return $line.Split("=", 2)[1].Trim()
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║   Azure Resource Teardown — Agentic AI Immersion              ║" -ForegroundColor Red
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""

# Locate .env
$envPath = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envPath)) {
    Write-Err ".env not found at $envPath"
    Write-Host "  Run provision.ps1 first, or create a .env with AZURE_RESOURCE_GROUP set." -ForegroundColor Yellow
    exit 1
}

# Read required values
$resourceGroup  = Get-EnvValue -Key "AZURE_RESOURCE_GROUP"  -EnvPath $envPath
$subscriptionId = Get-EnvValue -Key "AZURE_SUBSCRIPTION_ID" -EnvPath $envPath

if ([string]::IsNullOrWhiteSpace($resourceGroup)) {
    Write-Err "AZURE_RESOURCE_GROUP is not set in .env"
    exit 1
}

# Show what will be deleted
Write-Step "Resources to be deleted"
Write-Host "  Resource Group  : $resourceGroup" -ForegroundColor Cyan
Write-Host "  Subscription ID : $subscriptionId" -ForegroundColor Cyan
Write-Host ""
Write-Host "  This will permanently delete:" -ForegroundColor Yellow
Write-Host "    • Azure AI Services account + all model deployments" -ForegroundColor Yellow
Write-Host "    • AI Foundry project + all agents, threads, and memory stores" -ForegroundColor Yellow
Write-Host "    • Azure AI Search service + all indexes" -ForegroundColor Yellow
Write-Host "    • Bing Grounding resource + Foundry connections" -ForegroundColor Yellow
Write-Host "    • All other resources in the resource group" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "  Type the resource group name to confirm deletion"
if ($confirm -ne $resourceGroup) {
    Write-Warn "Name did not match. Aborting."
    exit 0
}

# Verify login
Write-Step "Verifying Azure login..."
$loginCheck = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warn "Not logged in — running az login"
    az login | Out-Null
}
Write-Success "Logged in"

# Set subscription if present
if (-not [string]::IsNullOrWhiteSpace($subscriptionId)) {
    az account set --subscription $subscriptionId | Out-Null
    Write-Success "Subscription set: $subscriptionId"
}

# Delete resource group
Write-Step "Deleting resource group '$resourceGroup'..."
Write-Host "  This may take a few minutes..." -ForegroundColor DarkGray

az group delete --name $resourceGroup --yes
if ($LASTEXITCODE -ne 0) {
    Write-Err "Failed to delete resource group"
    exit 1
}

Write-Success "Resource group '$resourceGroup' deleted"

# Offer to wipe .env
Write-Host ""
$wipeEnv = Read-Host "  Clear .env file? (y/n)"
if ($wipeEnv -match "^[Yy]$") {
    Remove-Item -Force $envPath
    Write-Success ".env removed"
} else {
    Write-Warn ".env kept — contains stale values"
}

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Teardown complete                                            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
