#!/usr/bin/env pwsh

# ============================================================================
# Revoke workshop participant access to Azure AI Foundry
#
# Removes the "Azure AI Developer" role at both the AIServices
# account scope and the project scope for each participant.
#
# Usage:
#   pwsh revoke-access.ps1                        # prompts for a list of emails
#   pwsh revoke-access.ps1 -EmailFile emails.txt  # reads emails from a file (one per line)
#
# Required role for caller: Owner or User Access Administrator on the
# AIServices account (or its resource group / subscription).
# ============================================================================

param(
    [string]$EmailFile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step    { param([string]$msg) Write-Host "`n▶ $msg" -ForegroundColor Blue }
function Write-Success { param([string]$msg) Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn    { param([string]$msg) Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Err     { param([string]$msg) Write-Host "  ✗ $msg" -ForegroundColor Red }

function Invoke-Az {
    param([string[]]$Arguments)
    $output = az @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Err "az $($Arguments -join ' ') failed:`n$output"
        throw "Azure CLI error"
    }
    return $output
}

function Invoke-AzJson {
    param([string[]]$Arguments)
    return (Invoke-Az ($Arguments + @("-o", "json"))) | ConvertFrom-Json
}

# ---------------------------------------------------------------------------
# 1. Banner
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
Write-Host "║   Revoke Workshop Participant Access — Agentic AI Immersion    ║" -ForegroundColor Red
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
Write-Host ""

# ---------------------------------------------------------------------------
# 2. Read .env
# ---------------------------------------------------------------------------
Write-Step "Reading .env file..."

$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Err ".env not found at $envFile — run provision.ps1 first or copy your .env to the repo root"
    exit 1
}

$env = @{}
Get-Content $envFile | Where-Object { $_ -match '^\s*[^#]\S+=\S' } | ForEach-Object {
    $parts = $_ -split '=', 2
    $env[$parts[0].Trim()] = $parts[1].Trim()
}

$projectResourceId = $env['PROJECT_RESOURCE_ID']
$subId             = $env['AZURE_SUBSCRIPTION_ID']
$rgName            = $env['AZURE_RESOURCE_GROUP']

if (-not $projectResourceId) {
    Write-Err "PROJECT_RESOURCE_ID not found in .env"
    exit 1
}
if (-not $subId) {
    Write-Err "AZURE_SUBSCRIPTION_ID not found in .env"
    exit 1
}

$accountScope = $projectResourceId -replace '/projects/[^/]+$', ''
$projectScope = $projectResourceId

Write-Success "Resource group : $rgName"
Write-Success "Account scope  : $accountScope"
Write-Success "Project scope  : $projectScope"

# ---------------------------------------------------------------------------
# 3. Login & set subscription
# ---------------------------------------------------------------------------
Write-Step "Verifying Azure login..."
try { Invoke-Az @("account", "show") | Out-Null } catch {
    Write-Warn "Not logged in — running az login"
    Invoke-Az @("login") | Out-Null
}

$current = Invoke-AzJson @("account", "show", "--query", "{id:id, name:name}")
if ($current.id -ne $subId) {
    Write-Host "  Switching to subscription $subId..." -ForegroundColor DarkGray
    Invoke-Az @("account", "set", "--subscription", $subId) | Out-Null
    $current = Invoke-AzJson @("account", "show", "--query", "{id:id, name:name}")
}
Write-Success "Subscription: $($current.name)"

# ---------------------------------------------------------------------------
# 4. Collect participant emails
# ---------------------------------------------------------------------------
Write-Step "Loading participant emails..."

$emails = @()

if ($EmailFile) {
    if (-not (Test-Path $EmailFile)) {
        Write-Err "Email file not found: $EmailFile"
        exit 1
    }
    $emails = Get-Content $EmailFile |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and $_ -notmatch '^\s*#' } |
        ForEach-Object { $_.Trim() }
    Write-Success "Loaded $($emails.Count) email(s) from $EmailFile"
} else {
    Write-Host "  Paste all emails (one per line). Press Enter on a blank line when done." -ForegroundColor DarkGray
    Write-Host ""
    while ($true) {
        $email = Read-Host "  Email (or blank to finish)"
        if ([string]::IsNullOrWhiteSpace($email)) { break }
        $emails += $email.Trim()
    }
}

if ($emails.Count -eq 0) {
    Write-Warn "No emails provided. Nothing to do."
    exit 0
}

Write-Host ""
Write-Host "  Will remove 'Azure AI Developer' from:" -ForegroundColor Cyan
$emails | ForEach-Object { Write-Host "    - $_" -ForegroundColor Cyan }
$go = Read-Host "`n  Proceed? (y/n)"
if ($go -notmatch "^[Yy]$") { Write-Warn "Aborted."; exit 0 }

# ---------------------------------------------------------------------------
# 5. Remove roles
# ---------------------------------------------------------------------------
Write-Step "Removing roles..."

$succeeded = @()
$failed    = @()

foreach ($email in $emails) {
    Write-Host "  Processing $email..." -ForegroundColor DarkGray

    try {
        $userId = (Invoke-AzJson @(
            "ad", "user", "show",
            "--id", $email,
            "--query", "id"
        )).Trim('"')
    } catch {
        Write-Err "Could not look up user '$email' in Entra ID — skipping"
        $failed += $email
        continue
    }

    # List all role assignments for this user, then filter client-side.
    # Passing --role with --all triggers an Azure CLI bug on non-standard scopes.
    $assignments = @(Invoke-AzJson @(
        "role", "assignment", "list",
        "--assignee", $userId,
        "--all"
    )) | Where-Object { $_.roleDefinitionName -eq "Azure AI Developer" }
    $assignments = @($assignments)

    if ($assignments.Count -eq 0) {
        Write-Warn "$email has no 'Azure AI Developer' assignments — skipping"
        $succeeded += $email
        continue
    }

    $removeOk = $true
    foreach ($assignment in $assignments) {
        try {
            Invoke-Az @(
                "role", "assignment", "delete",
                "--ids", $assignment.id
            ) | Out-Null
            Write-Success "$email removed from '$($assignment.roleDefinitionName)' at scope $($assignment.scope)"
        } catch {
            Write-Err "Failed to delete assignment $($assignment.id) for $email"
            $removeOk = $false
        }
    }

    if ($removeOk) { $succeeded += $email } else { $failed += $email }
}

# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Role removals complete                                       ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

if ($succeeded.Count -gt 0) {
    Write-Host "  Succeeded ($($succeeded.Count)):" -ForegroundColor Green
    $succeeded | ForEach-Object { Write-Host "    ✓ $_" -ForegroundColor Green }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "  Failed ($($failed.Count)) — check that these accounts exist in Entra ID" `
        -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "    ✗ $_" -ForegroundColor Red }
}

Write-Host ""
