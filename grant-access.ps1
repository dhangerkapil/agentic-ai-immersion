#!/usr/bin/env pwsh

# ============================================================================
# Grant workshop participant access to Azure AI Foundry
#
# Assigns the "Azure AI Developer" role on the AIServices account so that
# participants can create and manage agents, threads, runs, and call model endpoints.
#
# Usage:
#   pwsh grant-access.ps1                        # prompts for a list of emails
#   pwsh grant-access.ps1 -EmailFile emails.txt  # reads emails from a file (one per line)
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
# 1. Login & subscription
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Grant Workshop Participant Access — Agentic AI Immersion     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Step "Reading .env file..."

$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Err ".env not found at $envFile — run provision.ps1 first or copy your .env to the repo root"
    exit 1
}

# Parse key=value pairs, skipping comments and blanks
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

# Derive the AIServices account scope by stripping /projects/<name> from the end
# e.g. .../accounts/myaccount/projects/myproject  →  .../accounts/myaccount
$accountScope = $projectResourceId -replace '/projects/[^/]+$', ''
$projectScope = $projectResourceId

Write-Success "Resource group : $rgName"
Write-Success "Account scope  : $accountScope"
Write-Success "Project scope  : $projectScope"

# ---------------------------------------------------------------------------
# 2. Login & set subscription
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
Write-Host "  Will assign 'Azure AI Developer' to:" -ForegroundColor Cyan
$emails | ForEach-Object { Write-Host "    - $_" -ForegroundColor Cyan }
$go = Read-Host "`n  Proceed? (y/n)"
if ($go -notmatch "^[Yy]$") { Write-Warn "Aborted."; exit 0 }

# ---------------------------------------------------------------------------
# 5. Assign roles
# ---------------------------------------------------------------------------
Write-Step "Assigning roles..."

$succeeded = @()
$failed    = @()

foreach ($email in $emails) {
    Write-Host "  Processing $email..." -ForegroundColor DarkGray

    # Look up the Entra object ID for the user
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

    # Azure AI Developer grants the data plane actions required for agents, OpenAI inference,
    # and embeddings. The project endpoint enforces its own RBAC check so the project scope
    # assignment is required in addition to account scope.
    $roleAssignments = @(
        @{ Role = "Azure AI Developer"; Scope = $accountScope; Label = "account" },
        @{ Role = "Azure AI Developer"; Scope = $projectScope; Label = "project" }
    )

    $assignOk = $true
    foreach ($ra in $roleAssignments) {
        $existing = Invoke-AzJson @(
            "role", "assignment", "list",
            "--assignee", $userId,
            "--role", $ra.Role,
            "--scope", $ra.Scope,
            "--query", "length(@)"
        )

        if ($existing -gt 0) {
            Write-Warn "$email already has '$($ra.Role)' at $($ra.Label) scope — skipping"
            continue
        }

        try {
            Invoke-Az @(
                "role", "assignment", "create",
                "--assignee-object-id", $userId,
                "--assignee-principal-type", "User",
                "--role", $ra.Role,
                "--scope", $ra.Scope
            ) | Out-Null
            Write-Success "$email assigned '$($ra.Role)' at $($ra.Label) scope"
        } catch {
            Write-Err "Failed to assign '$($ra.Role)' for $email at $($ra.Label) scope"
            $assignOk = $false
        }
    }

    if ($assignOk) { $succeeded += $email } else { $failed += $email }
}

# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Role assignments complete                                    ║" -ForegroundColor Green
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
Write-Host "  Note: RBAC propagation typically takes 1–5 minutes." -ForegroundColor DarkGray
Write-Host "  If participants still get PermissionDenied, have them re-authenticate:" -ForegroundColor DarkGray
Write-Host "    az login --tenant $($env['TENANT_ID'])" -ForegroundColor DarkGray
Write-Host ""
