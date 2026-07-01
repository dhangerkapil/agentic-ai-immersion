<#
.SYNOPSIS
    One-shot permission + networking setup for the Agentic AI Immersion Workshop.

.DESCRIPTION
    Microsoft Foundry projects created via SDK/CLI (or some portal flows) do NOT
    automatically receive every role the workshop notebooks need. Running the
    notebooks then fails with confusing errors such as:

        - "ProjectMIUnauthorized" / "The project mi lacks the required action"   (evaluations)
        - "(401) Principal does not have access to API/Operation"                (Foundry IQ retrieval)
        - "(403) Failed to upload file using upload_url"                         (agent file search)
        - "AuthorizationFailure ... request is not authorized"                   (storage firewall)

    This script assigns the required Entra (AAD) RBAC roles to the three identities
    the workshop uses — your user, the Foundry PROJECT managed identity, and the
    Azure AI SEARCH service managed identity — and opens the project storage account
    so the managed Foundry services can reach it. It is idempotent: existing
    assignments are detected and skipped.

    Authentication is Entra-only (no API keys). Run `az login` first.

.PARAMETER SubscriptionId
    Azure subscription ID that contains the Foundry resources.

.PARAMETER ResourceGroup
    Resource group that contains the Foundry account, AI Search, and storage.

.PARAMETER AccountName
    Microsoft Foundry (Cognitive Services) account name, e.g. "my-foundry".

.PARAMETER ProjectName
    Foundry project name, e.g. "my-project".

.PARAMETER SearchServiceName
    Azure AI Search service name (needed for notebooks 5 & 8). Optional.

.PARAMETER StorageAccountName
    Project storage account name (needed for file search + evaluations). Optional.

.PARAMETER OpenStoragePublicAccess
    If set, enables publicNetworkAccess on the storage account so the managed
    Foundry evaluation + agent file-upload services can reach it. RBAC/Entra is
    still enforced. Omit if your storage uses private endpoints reachable by Foundry.

.EXAMPLE
    ./scripts/setup-permissions.ps1 `
        -SubscriptionId "00000000-0000-0000-0000-000000000000" `
        -ResourceGroup "rg-foundry" `
        -AccountName "my-foundry" `
        -ProjectName "my-project" `
        -SearchServiceName "my-foundry-search" `
        -StorageAccountName "stmyfoundry" `
        -OpenStoragePublicAccess
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $SubscriptionId,
    [Parameter(Mandatory = $true)] [string] $ResourceGroup,
    [Parameter(Mandatory = $true)] [string] $AccountName,
    [Parameter(Mandatory = $true)] [string] $ProjectName,
    [Parameter(Mandatory = $false)] [string] $SearchServiceName,
    [Parameter(Mandatory = $false)] [string] $StorageAccountName,
    [Parameter(Mandatory = $false)] [switch] $OpenStoragePublicAccess
)

$ErrorActionPreference = "Stop"
# az writes warnings to stderr; don't let that blank out captures or abort the script
$PSNativeCommandUseErrorActionPreference = $false

# Foundry User role GUID — use the ID (not the name) because the role was recently
# renamed (Azure AI User -> Foundry User) and the name may not resolve everywhere.
$FOUNDRY_USER_ROLE = "53ca6127-db72-4b80-b1b0-d745d6d5456d"

function Assert-AzLogin {
    try { az account show -o none 2>$null } catch { }
    if ($LASTEXITCODE -ne 0) { throw "Not logged in. Run 'az login' first." }
    az account set --subscription $SubscriptionId | Out-Null
    Write-Host "✅ Using subscription $SubscriptionId" -ForegroundColor Green
}

# Idempotent role assignment by principal object id.
function Grant-Role {
    param(
        [string] $PrincipalId,
        [string] $PrincipalType,   # User | ServicePrincipal
        [string] $Role,            # role name or GUID
        [string] $Scope,
        [string] $Label
    )
    if ([string]::IsNullOrWhiteSpace($PrincipalId)) {
        Write-Host "   ⏭️  Skipped ($Label): principal id not available" -ForegroundColor DarkGray
        return
    }
    # Detect an existing assignment by role name, or (when a GUID is passed) by role id suffix.
    $existing = az role assignment list --assignee $PrincipalId --scope $Scope --query "[?roleDefinitionName=='$Role'].id" -o tsv 2>$null
    if (-not $existing -and $Role -match '^[0-9a-fA-F-]{36}$') {
        $existing = az role assignment list --assignee $PrincipalId --scope $Scope --query "[?ends_with(roleDefinitionId, '$Role')].id" -o tsv 2>$null
    }
    if ($existing) {
        Write-Host "   ✓ $Label already has '$Role'" -ForegroundColor DarkGray
        return
    }
    az role assignment create --role $Role --assignee-object-id $PrincipalId --assignee-principal-type $PrincipalType --scope $Scope -o none 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ➕ Granted '$Role' to $Label" -ForegroundColor Cyan
    } else {
        Write-Host "   ⚠️  Could not grant '$Role' to $Label (may already exist or lack permission)" -ForegroundColor Yellow
    }
}

Assert-AzLogin

# ── Resolve scopes ───────────────────────────────────────────────────────────
$accountScope = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.CognitiveServices/accounts/$AccountName"
$storageScope = if ($StorageAccountName) { "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Storage/storageAccounts/$StorageAccountName" } else { $null }
$searchScope  = if ($SearchServiceName)  { "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Search/searchServices/$SearchServiceName" } else { $null }

# ── Resolve identities ───────────────────────────────────────────────────────
Write-Host "`n🔎 Resolving identities..." -ForegroundColor White
$userId = az ad signed-in-user show --query id -o tsv
Write-Host "   • You (user):        $userId"

$projectMi = az resource show --ids "$accountScope/projects/$ProjectName" --query "identity.principalId" -o tsv 2>$null
if ([string]::IsNullOrWhiteSpace($projectMi)) {
    $projectMi = az rest --method get --url "https://management.azure.com$accountScope/projects/$ProjectName?api-version=2025-04-01-preview" --query "identity.principalId" -o tsv 2>$null
}
$projectMi = ($projectMi | Out-String).Trim()
Write-Host "   • Project MI:        $projectMi"
if ([string]::IsNullOrWhiteSpace($projectMi)) {
    Write-Host "   🔴 Could NOT resolve the Project managed identity — the CRITICAL 'Foundry User' grant will be skipped, which causes ProjectMIUnauthorized. Verify -ProjectName '$ProjectName' and that the project has a system-assigned identity (Foundry project -> Identity)." -ForegroundColor Red
}

$accountMi = az cognitiveservices account show -n $AccountName -g $ResourceGroup --query "identity.principalId" -o tsv 2>$null
Write-Host "   • Account MI:        $accountMi"

$searchMi = $null
if ($SearchServiceName) {
    $searchMi = az search service show -n $SearchServiceName -g $ResourceGroup --query "identity.principalId" -o tsv 2>$null
    Write-Host "   • Search service MI: $searchMi"
}

# ── User roles ───────────────────────────────────────────────────────────────
Write-Host "`n👤 Assigning USER roles..." -ForegroundColor White
Grant-Role -PrincipalId $userId -PrincipalType "User" -Role $FOUNDRY_USER_ROLE -Scope $accountScope -Label "you"
Grant-Role -PrincipalId $userId -PrincipalType "User" -Role "Cognitive Services OpenAI User" -Scope $accountScope -Label "you"
if ($storageScope) { Grant-Role -PrincipalId $userId -PrincipalType "User" -Role "Storage Blob Data Contributor" -Scope $storageScope -Label "you" }
if ($searchScope) {
    Grant-Role -PrincipalId $userId -PrincipalType "User" -Role "Search Index Data Contributor" -Scope $searchScope -Label "you"
    Grant-Role -PrincipalId $userId -PrincipalType "User" -Role "Search Index Data Reader" -Scope $searchScope -Label "you"
    Grant-Role -PrincipalId $userId -PrincipalType "User" -Role "Search Service Contributor" -Scope $searchScope -Label "you"
}

# ── Project managed identity roles ───────────────────────────────────────────
Write-Host "`n🤖 Assigning PROJECT managed-identity roles..." -ForegroundColor White
Grant-Role -PrincipalId $projectMi -PrincipalType "ServicePrincipal" -Role $FOUNDRY_USER_ROLE -Scope $accountScope -Label "project MI"
Grant-Role -PrincipalId $projectMi -PrincipalType "ServicePrincipal" -Role "Cognitive Services OpenAI User" -Scope $accountScope -Label "project MI"
Grant-Role -PrincipalId $projectMi -PrincipalType "ServicePrincipal" -Role "Cognitive Services User" -Scope $accountScope -Label "project MI"
if ($storageScope) { Grant-Role -PrincipalId $projectMi -PrincipalType "ServicePrincipal" -Role "Storage Blob Data Contributor" -Scope $storageScope -Label "project MI" }
if ($searchScope) { Grant-Role -PrincipalId $projectMi -PrincipalType "ServicePrincipal" -Role "Search Index Data Reader" -Scope $searchScope -Label "project MI" }

# ── Account managed identity roles (file upload / evaluation storage) ────────
if ($storageScope -and $accountMi) {
    Write-Host "`n🏦 Assigning ACCOUNT managed-identity roles..." -ForegroundColor White
    Grant-Role -PrincipalId $accountMi -PrincipalType "ServicePrincipal" -Role "Storage Blob Data Contributor" -Scope $storageScope -Label "account MI"
}

# ── Search service managed identity roles (Foundry IQ agentic retrieval) ─────
if ($searchMi) {
    Write-Host "`n🔍 Assigning SEARCH service managed-identity roles..." -ForegroundColor White
    # Embedding (vectorizer) calls:
    Grant-Role -PrincipalId $searchMi -PrincipalType "ServicePrincipal" -Role "Cognitive Services OpenAI User" -Scope $accountScope -Label "search MI"
    # Agentic-retrieval reasoning model calls (needs the broader role):
    Grant-Role -PrincipalId $searchMi -PrincipalType "ServicePrincipal" -Role "Cognitive Services User" -Scope $accountScope -Label "search MI"
}

# ── Storage networking ───────────────────────────────────────────────────────
if ($StorageAccountName -and $OpenStoragePublicAccess) {
    Write-Host "`n🌐 Enabling public network access on storage '$StorageAccountName'..." -ForegroundColor White
    Write-Host "   (RBAC/Entra is still enforced — this only lets the managed Foundry services reach the endpoint)" -ForegroundColor DarkGray
    az storage account update -n $StorageAccountName -g $ResourceGroup --public-network-access Enabled -o none
    Write-Host "   ✅ publicNetworkAccess = Enabled" -ForegroundColor Green
}

Write-Host "`n✅ Permission setup complete." -ForegroundColor Green
Write-Host "⏳ Note: Entra data-plane role assignments can take 5–15 minutes to propagate." -ForegroundColor Yellow
Write-Host "   If a notebook still returns 401/403 right after running this, wait a few minutes and retry." -ForegroundColor Yellow
