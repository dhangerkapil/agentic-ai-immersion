#!/usr/bin/env pwsh

# ============================================================================
# Azure Resource Provisioning Script
# Creates all necessary Azure resources for the Agentic AI Immersion workshop
# ============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
function Write-Step { param([string]$msg) Write-Host "`n▶ $msg" -ForegroundColor Blue }
function Write-Success { param([string]$msg) Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Warn { param([string]$msg) Write-Host "  ⚠ $msg" -ForegroundColor Yellow }
function Write-Err { param([string]$msg) Write-Host "  ✗ $msg" -ForegroundColor Red }

function Invoke-Az {
    param([string[]]$Arguments, [switch]$Silent)
    $output = az @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        if (-not $Silent) {
            Write-Err "az $($Arguments -join ' ') failed:`n$output"
        }
        throw "Azure CLI error: $output"
    }
    return $output
}

function Invoke-AzJson {
    param([string[]]$Arguments)
    return (Invoke-Az ($Arguments + @("-o", "json"))) | ConvertFrom-Json
}

function Invoke-AzRestJson {
    param(
        [string]$Method,
        [string]$Url,
        [string]$Body = "",
        [string]$ApiVersion = "",
        [switch]$Silent
    )

    $arguments = @("rest", "--method", $Method, "--url", $Url)
    if (-not [string]::IsNullOrWhiteSpace($ApiVersion)) {
        $arguments += @("--uri-parameters", "api-version=$ApiVersion")
    }
    if (-not [string]::IsNullOrWhiteSpace($Body)) {
        $tempFile = [System.IO.Path]::GetTempFileName()
        try {
            $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
            [System.IO.File]::WriteAllText($tempFile, $Body, $utf8NoBom)
            $arguments += @("--headers", "Content-Type=application/json", "--body", "@$tempFile")
            return Invoke-Az $arguments -Silent:$Silent
        }
        finally {
            if (Test-Path $tempFile) {
                Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
            }
        }
    }

    return Invoke-Az $arguments -Silent:$Silent
}

function Invoke-AzRestJsonObject {
    param(
        [string]$Method,
        [string]$Url,
        [string]$Body = "",
        [string]$ApiVersion = "",
        [switch]$Silent
    )

    return (Invoke-AzRestJson -Method $Method -Url $Url -Body $Body -ApiVersion $ApiVersion -Silent:$Silent | ConvertFrom-Json)
}

function Invoke-AzRestWithRetry {
    param(
        [string]$Method,
        [string]$Url,
        [string]$Body = "",
        [string]$ApiVersion = "",
        [int]$MaxRetries = 3,
        [int]$InitialDelaySeconds = 2
    )

    $delay = $InitialDelaySeconds
    for ($attempt = 1; $attempt -le $MaxRetries; $attempt++) {
        try {
            return Invoke-AzRestJson -Method $Method -Url $Url -Body $Body -ApiVersion $ApiVersion
        }
        catch {
            $errorMsg = $_.Exception.Message
            # Retry on transient errors like ParentResourceNotFound or temporary unavailability
            if ($attempt -lt $MaxRetries -and ($errorMsg -match "ParentResourceNotFound|Conflict|BadGateway|ServiceUnavailable|RequestTimeout")) {
                Write-Host "    Retry in ${delay}s (attempt $attempt/$MaxRetries)..." -ForegroundColor DarkGray
                Start-Sleep -Seconds $delay
                $delay = [Math]::Min($delay * 2, 10)  # Exponential backoff, cap at 10s
                continue
            }
            throw
        }
    }
}

function Ensure-RoleAssignment {
    param(
        [string]$RoleName,
        [string]$AssigneeObjectId,
        [string]$AssigneePrincipalType,
        [string]$Scope
    )

    if ([string]::IsNullOrWhiteSpace($AssigneeObjectId)) { return }

    $existing = Invoke-AzJson @(
        "role", "assignment", "list",
        "--assignee-object-id", $AssigneeObjectId,
        "--scope", $Scope,
        "--role", $RoleName,
        "--query", "[0].id"
    )

    if ($existing) {
        Write-Host "    Role already assigned: $RoleName" -ForegroundColor DarkGray
        return
    }

    try {
        Invoke-Az @(
            "role", "assignment", "create",
            "--role", $RoleName,
            "--assignee-object-id", $AssigneeObjectId,
            "--assignee-principal-type", $AssigneePrincipalType,
            "--scope", $Scope
        ) | Out-Null
        Write-Success "Role assigned: $RoleName"
    }
    catch {
        $msg = $_.Exception.Message
        if ($msg -match "RoleAssignmentExists|already exists") {
            Write-Host "    Role already assigned: $RoleName" -ForegroundColor DarkGray
        }
        else {
            throw
        }
    }
}

function Set-WorkshopRbac {
    param(
        [string]$SubId,
        [string]$ResourceGroup,
        [string]$ProjectManagedIdentityPrincipalId = ""
    )

    Write-Step "Assigning Azure RBAC roles (optional)..."
    $include = Read-Host "  Configure RBAC role assignments now? (Y/n)"
    if ($include -match "^[Nn]$") {
        Write-Warn "Skipping RBAC role assignment"
        return
    }

    $scope = "/subscriptions/$SubId/resourceGroups/$ResourceGroup"
    Write-Host "  Scope: $scope" -ForegroundColor Cyan

    $groupObjectId = Read-Host "  Enter Entra group object ID for shared permissions (Enter to skip)"
    if (-not [string]::IsNullOrWhiteSpace($groupObjectId)) {
        Write-Host "  Group role bundles:" -ForegroundColor Cyan
        Write-Host "  1. Core only (Azure AI Developer, Cognitive Services OpenAI User)"
        Write-Host "  2. Search only (Search Index Data Contributor, Search Index Data Reader, Search Service Contributor)"
        Write-Host "  3. Core + Search"
        Write-Host "  4. All workshop roles"
        $bundle = Read-Host "  Select group role bundle (Enter for 3)"
        if ([string]::IsNullOrWhiteSpace($bundle)) { $bundle = "3" }

        $groupRoles = switch ($bundle) {
            "1" { @("Azure AI Developer", "Cognitive Services OpenAI User") }
            "2" { @("Search Index Data Contributor", "Search Index Data Reader", "Search Service Contributor") }
            "4" { @("Azure AI Developer", "Cognitive Services OpenAI User", "Storage Blob Data Contributor", "Search Index Data Contributor", "Search Index Data Reader", "Search Service Contributor") }
            default { @("Azure AI Developer", "Cognitive Services OpenAI User", "Search Index Data Contributor", "Search Index Data Reader", "Search Service Contributor") }
        }

        Write-Host "  Assigning group roles..." -ForegroundColor DarkGray
        foreach ($role in $groupRoles) {
            Ensure-RoleAssignment -RoleName $role -AssigneeObjectId $groupObjectId -AssigneePrincipalType "Group" -Scope $scope
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($ProjectManagedIdentityPrincipalId)) {
        $assignMi = Read-Host "  Assign 'Search Index Data Reader' to project managed identity (recommended, notebook 8)? (Y/n)"
        if ($assignMi -notmatch "^[Nn]$") {
            Ensure-RoleAssignment -RoleName "Search Index Data Reader" -AssigneeObjectId $ProjectManagedIdentityPrincipalId -AssigneePrincipalType "ServicePrincipal" -Scope $scope
        }
    }

    Write-Success "RBAC configuration step complete"
}

# ---------------------------------------------------------------------------
# Wait for a CognitiveServices resource to finish provisioning
# ---------------------------------------------------------------------------
function Wait-Provisioning {
    param([string]$ResourceGroup, [string]$AccountName, [string]$SubId, [string]$ProjectName = "")

    for ($i = 0; $i -lt 30; $i++) {
        if ($ProjectName) {
            $url = "https://management.azure.com/subscriptions/$SubId/resourceGroups/$ResourceGroup/providers/Microsoft.CognitiveServices/accounts/$AccountName/projects/$ProjectName"
            try {
                $state = (Invoke-AzRestJsonObject -Method "GET" -Url $url -ApiVersion "2025-04-01-preview").properties.provisioningState
            }
            catch {
                $errorMsg = $_.Exception.Message
                if ($errorMsg -match "ResourceNotFound|ParentResourceNotFound") {
                    $state = "Accepted"
                }
                else {
                    throw
                }
            }
        }
        else {
            $url = "https://management.azure.com/subscriptions/$SubId/resourceGroups/$ResourceGroup/providers/Microsoft.CognitiveServices/accounts/$AccountName"
            try {
                $state = (Invoke-AzRestJsonObject -Method "GET" -Url $url -ApiVersion "2025-12-01").properties.provisioningState
            }
            catch {
                $errorMsg = $_.Exception.Message
                if ($errorMsg -match "ResourceNotFound|ParentResourceNotFound") {
                    $state = "Accepted"
                }
                else {
                    throw
                }
            }
        }
        if ($state -eq "Succeeded") { return }
        if ($state -eq "Failed") { throw "Provisioning failed" }
        Write-Host "    ... $state, waiting 10s" -ForegroundColor DarkGray
        Start-Sleep 10
    }
    throw "Timed out waiting for provisioning"
}

# ---------------------------------------------------------------------------
# STEP 1 — Azure login & subscription
# ---------------------------------------------------------------------------
function Get-SubscriptionInfo {
    Write-Step "Verifying Azure login..."
    try { Invoke-Az @("account", "show") | Out-Null } catch {
        Write-Warn "Not logged in — running az login"
        Invoke-Az @("login") | Out-Null
    }

    $account = Invoke-AzJson @("account", "show",
        "--query", "{id:id, tenantId:tenantId, name:name}")

    Write-Success "Logged in"
    Write-Host "  Current subscription: $($account.name)" -ForegroundColor Cyan

    $confirm = Read-Host "  Use this subscription? (Y/n)"
    if ($confirm -match "^[Nn]$") {
        $subs = Invoke-AzJson @("account", "list",
            "--query", "[].{id:id, name:name}")
        for ($i = 0; $i -lt $subs.Count; $i++) {
            Write-Host "  $($i+1). $($subs[$i].name)  [$($subs[$i].id)]"
        }
        $sel = [int](Read-Host "  Select subscription number") - 1
        Invoke-Az @("account", "set", "--subscription", $subs[$sel].id) | Out-Null
        $account = Invoke-AzJson @("account", "show",
            "--query", "{id:id, tenantId:tenantId, name:name}")
    }

    Write-Success "Subscription: $($account.name)"
    return $account
}

# ---------------------------------------------------------------------------
# STEP 2 — Resource group
# ---------------------------------------------------------------------------
function New-WorkshopResourceGroup {
    param([string]$SubId)

    Write-Step "Creating resource group..."

    $name = "poc-aim-wtw-workshop"  # "Enter resource group name (e.g. rg-ai-workshop)"

    # Region is fixed to East US 2 — required for hosted-agents (preview feature).
    # All other workshop notebooks also work in this region.
    $location = "eastus2"

    Invoke-Az @("group", "create",
        "--name", $name,
        "--location", $location,
        "--subscription", $SubId) | Out-Null

    Write-Success "Resource group '$name' created in $location"
    return @{ Name = $name; Location = $location }
}

# ---------------------------------------------------------------------------
# STEP 3 — AIServices account
# ---------------------------------------------------------------------------
function New-AIServicesAccount {
    param([string]$ResourceGroup, [string]$Location, [string]$SubId)

    Write-Step "Creating Azure AI Services account..."

    $default = "$ResourceGroup-aim-ai-services"
    $name = Read-Host "  Account name (Enter for '$default')"
    if ([string]::IsNullOrWhiteSpace($name)) { $name = $default }

    # Custom subdomain is required before projects can be created under the account.
    # It must be globally unique — default to the account name itself.
    $customDomain = $name
    # Some tenants/policies now require explicit public network access setting at create time.
    $publicNetworkAccess = "Enabled"

    # Use ARM REST for create to avoid Azure CLI version differences on flags
    # (for example, --public-network-access may be unavailable in older az versions).
    # allowProjectManagement must be true to create Foundry projects under this account.
    $accountApiVersion = "2025-12-01"
    $accountUrl = "https://management.azure.com/subscriptions/$SubId/resourceGroups/$ResourceGroup/providers/Microsoft.CognitiveServices/accounts/$name"
    $accountBody = "{`"kind`":`"AIServices`",`"location`":`"$Location`",`"sku`":{`"name`":`"S0`"},`"identity`":{`"type`":`"SystemAssigned`"},`"tags`":{`"gr401`":`"UC1`"},`"properties`":{`"customSubDomainName`":`"$customDomain`",`"publicNetworkAccess`":`"$publicNetworkAccess`",`"allowProjectManagement`":true}}"

    $existingAccount = $null
    try {
        $existingAccount = Invoke-AzRestJsonObject -Method "GET" -Url $accountUrl -ApiVersion $accountApiVersion -Silent
    }
    catch {
        $errorMsg = $_.Exception.Message
        if ($errorMsg -notmatch "ResourceNotFound|ParentResourceNotFound") {
            throw
        }
    }

    if ($existingAccount) {
        Write-Warn "AIServices account '$name' already exists — reusing and applying required settings"
        $patchBody = "{`"properties`":{`"publicNetworkAccess`":`"$publicNetworkAccess`",`"allowProjectManagement`":true},`"tags`":{`"gr401`":`"UC1`"}}"
        try {
            Invoke-AzRestWithRetry -Method "PATCH" -Url $accountUrl -Body $patchBody -ApiVersion $accountApiVersion -MaxRetries 6 -InitialDelaySeconds 3 | Out-Null
        }
        catch {
            Write-Warn "Could not patch account settings automatically; continuing with existing account"
        }
    }
    else {
        try {
            Invoke-AzRestWithRetry -Method "PUT" -Url $accountUrl -Body $accountBody -ApiVersion $accountApiVersion -MaxRetries 8 -InitialDelaySeconds 5 | Out-Null
        }
        catch {
            if ($_.Exception.Message -notmatch "FlagMustBeSetForRestore") { throw }

            # Account is soft-deleted — wait 5s and try once more before forcing purge
            Write-Warn "Soft-deleted account detected — waiting 5s and retrying once..."
            Start-Sleep 5
            try {
                Invoke-AzRestWithRetry -Method "PUT" -Url $accountUrl -Body $accountBody -ApiVersion $accountApiVersion -MaxRetries 2 -InitialDelaySeconds 3 | Out-Null
            }
            catch {
                if ($_.Exception.Message -notmatch "FlagMustBeSetForRestore") { throw }

                Write-Warn "Still soft-deleted — force purging..."
                Invoke-Az @("cognitiveservices", "account", "purge",
                    "--location", $Location, "--resource-group", $ResourceGroup,
                    "--name", $name, "--subscription", $SubId) | Out-Null
                Write-Success "Purged — recreating account..."
                Invoke-AzRestWithRetry -Method "PUT" -Url $accountUrl -Body $accountBody -ApiVersion $accountApiVersion -MaxRetries 4 -InitialDelaySeconds 5 | Out-Null
            }
        }
    }

    Write-Host "    waiting for provisioning..." -ForegroundColor DarkGray
    Wait-Provisioning -ResourceGroup $ResourceGroup -AccountName $name -SubId $SubId

    $resource = (Invoke-AzRestWithRetry -Method "GET" -Url "https://management.azure.com/subscriptions/$SubId/resourceGroups/$ResourceGroup/providers/Microsoft.CognitiveServices/accounts/$name" -ApiVersion "2025-12-01" -MaxRetries 5 -InitialDelaySeconds 2) | ConvertFrom-Json

    $openaiEndpoint = $resource.properties.endpoints."OpenAI Language Model Instance API"
    $foundryEndpoint = $resource.properties.endpoints."AI Foundry API"

    Write-Success "AIServices account '$name' ready"
    Write-Success "OpenAI endpoint:  $openaiEndpoint"
    Write-Success "Foundry endpoint: $foundryEndpoint"

    return @{
        Name            = $name
        Id              = $resource.id
        OpenAIEndpoint  = $openaiEndpoint
        FoundryEndpoint = $foundryEndpoint
    }
}

# ---------------------------------------------------------------------------
# STEP 4 — AI Foundry project
# ---------------------------------------------------------------------------
function New-FoundryProject {
    param([string]$ResourceGroup, [string]$Location, [string]$SubId,
        [string]$AccountName, [string]$AccountId)

    Write-Step "Creating AI Foundry project..."

    $default = "aim-ai-workshop"
    $projectName = Read-Host "  Project name (Enter for '$default')"
    if ([string]::IsNullOrWhiteSpace($projectName)) { $projectName = $default }

    $projectApiVersion = "2025-04-01-preview"
    $url = "https://management.azure.com$AccountId/projects/$projectName"
    # The identity block is required — without it the ARM API returns 400 "must enable a managed identity".
    $body = "{`"location`":`"$Location`",`"kind`":`"AIServices`",`"identity`":{`"type`":`"SystemAssigned`"},`"properties`":{}}"

    Invoke-AzRestJson -Method "PUT" -Url $url -Body $body -ApiVersion $projectApiVersion | Out-Null

    Write-Host "    waiting for provisioning..." -ForegroundColor DarkGray
    Wait-Provisioning -ResourceGroup $ResourceGroup -AccountName $AccountName `
        -SubId $SubId -ProjectName $projectName

    $project = Invoke-AzRestJsonObject -Method "GET" -Url "https://management.azure.com$AccountId/projects/$projectName" -ApiVersion $projectApiVersion

    $endpoint = $project.properties.endpoints."AI Foundry API"
    $resourceId = $project.id
    $projectMiPrincipalId = $project.identity.principalId

    Write-Success "Project '$projectName' ready"
    Write-Success "Project endpoint: $endpoint"

    return @{
        Name                       = $projectName
        Endpoint                   = $endpoint
        ResourceId                 = $resourceId
        ManagedIdentityPrincipalId = $projectMiPrincipalId
    }
}

# ---------------------------------------------------------------------------
# STEP 5 — Model deployments
# ---------------------------------------------------------------------------
function New-ModelDeployments {
    param([string]$ResourceGroup, [string]$AccountName, [string]$SubId)

    Write-Step "Deploying models..."

    $location = (Invoke-AzJson @("group", "show",
            "--name", $ResourceGroup, "--query", "location")).Trim('"')

    # List available models and let user pick chat model(s)
    Write-Host "  Fetching available chat models..." -ForegroundColor DarkGray
    # unique_by() is not supported in az CLI's JMESPath — deduplicate on the PowerShell side instead.
    $allChatModelsRaw = Invoke-AzJson @(
        "cognitiveservices", "model", "list",
        "--location", $location,
        "--query", "[?model.capabilities.chatCompletion=='true' && model.lifecycleStatus!='Deprecated' && model.lifecycleStatus!='Deprecating'].{name:model.name, version:model.version} | sort_by(@, &name)"
    )
    $allChatModels = $allChatModelsRaw | Sort-Object name | Group-Object name | ForEach-Object { $_.Group[0] }
    $gptChatModels  = @($allChatModels | Where-Object { $_.name -match '^gpt' })

    $chatModels = $gptChatModels
    $showingAll = $false

    function Show-ChatModelList {
        param([array]$Models, [bool]$All)
        $label = if ($All) { "All available chat models" } else { "GPT chat models (enter * to see all)" }
        Write-Host "`n  $label`:" -ForegroundColor Cyan
        for ($i = 0; $i -lt $Models.Count; $i++) {
            Write-Host "  $($i+1). $($Models[$i].name)"
        }
    }

    Show-ChatModelList -Models $chatModels -All $showingAll

    $chatIndexes = $null
    while ($null -eq $chatIndexes) {
        $chatSelectionRaw = Read-Host "  Select model number(s) (comma-separated), or * for full list"
        if ($chatSelectionRaw.Trim() -eq "*") {
            $chatModels = $allChatModels
            $showingAll = $true
            Show-ChatModelList -Models $chatModels -All $showingAll
            continue
        }
        $parsed = @($chatSelectionRaw -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -match '^\d+$' } | ForEach-Object { [int]$_ - 1 } | Where-Object { $_ -ge 0 -and $_ -lt $chatModels.Count } | Select-Object -Unique)
        if ($parsed.Count -eq 0) {
            Write-Warn "Invalid selection — enter one or more numbers from the list, or * to see all models"
            continue
        }
        $chatIndexes = $parsed
    }

    $chatDeploymentNames = @()
    foreach ($chatSel in $chatIndexes) {
        $chatModel = $chatModels[$chatSel].name

        # Get versions for selected model
        # unique_by() is not supported in az CLI's JMESPath — deduplicate on the PowerShell side.
        # format is captured so it can be passed to --model-format at deployment time.
        $chatVersionsRaw = Invoke-AzJson @(
            "cognitiveservices", "model", "list",
            "--location", $location,
            "--query", "[?model.name=='$chatModel' && model.lifecycleStatus!='Deprecated' && model.lifecycleStatus!='Deprecating'].{version:model.version, sku:model.skus[0].name, format:model.format}"
        )
        $chatVersions = $chatVersionsRaw | Group-Object version | ForEach-Object { $_.Group[0] } | Sort-Object version -Descending

        Write-Host "`n  Available versions for $chatModel`:"
        for ($i = 0; $i -lt $chatVersions.Count; $i++) {
            Write-Host "  $($i+1). $($chatVersions[$i].version)  [SKU: $($chatVersions[$i].sku)]"
        }
        $verSelection = Read-Host "  Select version number for $chatModel (Enter for 1)"
        if ([string]::IsNullOrWhiteSpace($verSelection)) { $verSelection = "1" }
        $verSel = [int]$verSelection - 1

        $chatVersion = $chatVersions[$verSel].version
        $chatSku = $chatVersions[$verSel].sku
        $chatFormat = $chatVersions[$verSel].format

        # Deployment name
        $chatDepDefault = $chatModel
        $chatDepName = Read-Host "  Deployment name for $chatModel (Enter for '$chatDepDefault')"
        if ([string]::IsNullOrWhiteSpace($chatDepName)) { $chatDepName = $chatDepDefault }

        Write-Host "  Deploying $chatModel ($chatVersion)..." -ForegroundColor DarkGray
        Invoke-Az @(
            "cognitiveservices", "account", "deployment", "create",
            "--resource-group", $ResourceGroup,
            "--name", $AccountName,
            "--deployment-name", $chatDepName,
            "--model-name", $chatModel,
            "--model-version", $chatVersion,
            "--model-format", $chatFormat,
            "--sku-capacity", "50",
            "--sku-name", $chatSku
        ) | Out-Null
        Write-Success "Chat model deployed: $chatDepName"
        $chatDeploymentNames += $chatDepName
    }

    # Embedding model
    $embedDefault = "text-embedding-3-large"
    Write-Host "`n  Deploying embedding model (default: $embedDefault)..." -ForegroundColor DarkGray
    # unique_by() is not supported in az CLI's JMESPath — deduplicate on the PowerShell side.
    # format and sku are captured so they can be passed to the deployment command.
    $embedModelsRaw = Invoke-AzJson @(
        "cognitiveservices", "model", "list",
        "--location", (Invoke-AzJson @("group", "show",
                "--name", $ResourceGroup, "--query", "location")).Trim('"'),
        "--query", "[?model.capabilities.embeddings=='true' && model.lifecycleStatus!='Deprecated' && model.lifecycleStatus!='Deprecating'].{name:model.name, version:model.version, format:model.format, sku:model.skus[0].name}"
    )
    $embedModels = $embedModelsRaw | Group-Object name | ForEach-Object { $_.Group[0] }

    Write-Host "`n  Available embedding models:"
    for ($i = 0; $i -lt $embedModels.Count; $i++) {
        Write-Host "  $($i+1). $($embedModels[$i].name)"
    }
    $embedSelectionRaw = Read-Host "  Select embedding model number(s) (comma-separated, e.g. 1,2)"
    if ([string]::IsNullOrWhiteSpace($embedSelectionRaw)) { $embedSelectionRaw = "1" }
    $embedIndexes = @($embedSelectionRaw -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ -match '^\d+$' } | ForEach-Object { [int]$_ - 1 } | Where-Object { $_ -ge 0 -and $_ -lt $embedModels.Count } | Select-Object -Unique)
    if ($embedIndexes.Count -eq 0) { throw "No valid embedding model selections were provided" }

    $embedDeploymentNames = @()
    foreach ($embedSel in $embedIndexes) {
        $embedModel = $embedModels[$embedSel].name
        $embedVersion = $embedModels[$embedSel].version
        $embedFormat = $embedModels[$embedSel].format
        $embedSku = $embedModels[$embedSel].sku

        $embedDepDefault = $embedModel
        $embedDepName = Read-Host "  Deployment name for $embedModel (Enter for '$embedDepDefault')"
        if ([string]::IsNullOrWhiteSpace($embedDepName)) { $embedDepName = $embedDepDefault }

        Invoke-Az @(
            "cognitiveservices", "account", "deployment", "create",
            "--resource-group", $ResourceGroup,
            "--name", $AccountName,
            "--deployment-name", $embedDepName,
            "--model-name", $embedModel,
            "--model-version", $embedVersion,
            "--model-format", $embedFormat,
            "--sku-capacity", "50",
            "--sku-name", $embedSku
        ) | Out-Null
        Write-Success "Embedding model deployed: $embedDepName"
        $embedDeploymentNames += $embedDepName
    }

    return @{
        ChatDeploymentName       = $chatDeploymentNames[0]
        EmbeddingDeploymentName  = $embedDeploymentNames[0]
        ChatDeploymentNames      = ($chatDeploymentNames -join ",")
        EmbeddingDeploymentNames = ($embedDeploymentNames -join ",")
    }
}

# ---------------------------------------------------------------------------
# STEP 6 — Azure AI Search (optional)
# ---------------------------------------------------------------------------
function New-SearchService {
    param([string]$ResourceGroup, [string]$Location, [string]$SubId, [string]$ProjectResourceId)

    Write-Step "Azure AI Search (optional)..."
    $include = Read-Host "  Create an Azure AI Search service? (Y/n)"
    if ($include -match "^[Nn]$") {
        Write-Warn "Skipping Azure AI Search"
        return @{
            Endpoint   = "<your-search-endpoint>"
            ApiKey     = "<your-search-api-key>"
            ApiVersion = "2025-03-01-preview"
            AuthMethod = "api-search-key"
            IndexName  = "<your-index-name>"
        }
    }

    $skus = @("free", "basic", "standard", "standard2", "standard3")
    Write-Host "`n  Available SKUs:"
    for ($i = 0; $i -lt $skus.Count; $i++) { Write-Host "  $($i+1). $($skus[$i])" }
    $skuSel = [int](Read-Host "  Select SKU (recommend 'standard' for workshop)") - 1
    $sku = $skus[$skuSel]

    $suffix = -join ((97..122) | Get-Random -Count 4 | ForEach-Object { [char]$_ })
    $default = "$ResourceGroup-search-$suffix"
    $name = Read-Host "  Search service name (Enter for '$default')"
    if ([string]::IsNullOrWhiteSpace($name)) { $name = $default }

    $searchLocation = $Location
    while ($true) {
        try {
            Invoke-Az @(
                "search", "service", "create",
                "--name", $name,
                "--resource-group", $ResourceGroup,
                "--location", $searchLocation,
                "--sku", $sku,
                "--subscription", $SubId
            ) | Out-Null
            break
        }
        catch {
            if ($_.Exception.Message -match "InsufficientResourcesAvailable") {
                Write-Warn "Region '$searchLocation' is out of AI Search capacity."
                $altRegion = Read-Host "  Enter an alternate region (Enter for 'centralus')"
                if ([string]::IsNullOrWhiteSpace($altRegion)) { $altRegion = "centralus" }
                $searchLocation = $altRegion
            }
            elseif ($_.Exception.Message -match "already exists") {
                Write-Warn "Name '$name' is already taken globally."
                $newSuffix = -join ((97..122) | Get-Random -Count 4 | ForEach-Object { [char]$_ })
                $suggested = "$ResourceGroup-search-$newSuffix"
                $name = Read-Host "  Enter a different name (Enter for '$suggested')"
                if ([string]::IsNullOrWhiteSpace($name)) { $name = $suggested }
            }
            else { throw }
        }
    }

    $endpoint = "https://$name.search.windows.net"
    $key = (Invoke-AzJson @(
            "search", "admin-key", "show",
            "--resource-group", $ResourceGroup,
            "--service-name", $name,
            "--subscription", $SubId
        )).primaryKey

    $indexName = Read-Host "  Index name to use (Enter for 'workshop-index')"
    if ([string]::IsNullOrWhiteSpace($indexName)) { $indexName = "workshop-index" }

    # Register search as a connection in the Foundry project
    $connUrl = "https://management.azure.com$ProjectResourceId/connections/$name"
    $connBody = "{`"properties`":{`"category`":`"CognitiveSearch`",`"target`":`"$endpoint`",`"authType`":`"ApiKey`",`"credentials`":{`"key`":`"$key`"}}}"
    try {
        Invoke-AzRestWithRetry -Method "PUT" -Url $connUrl -Body $connBody -ApiVersion "2025-04-01-preview" | Out-Null
        Write-Success "Search connection registered in Foundry project"
    }
    catch {
        Write-Warn "Could not register search connection in project (can be added manually)"
    }

    Write-Success "Search service '$name' ready: $endpoint"
    return @{
        Endpoint   = $endpoint
        ApiKey     = $key
        ApiVersion = "2025-03-01-preview"
        AuthMethod = "api-search-key"
        IndexName  = $indexName
    }
}

# ---------------------------------------------------------------------------
# STEP 7 — Bing Search connection (optional)
# ---------------------------------------------------------------------------
function New-BingConnection {
    param([string]$ResourceGroup, [string]$Location, [string]$SubId, [string]$ProjectResourceId)

    Write-Step "Bing Search grounding (required)..."

    $default = "$ResourceGroup-bing"
    $name = Read-Host "  Bing resource name (Enter for '$default')"
    if ([string]::IsNullOrWhiteSpace($name)) { $name = $default }

    # Create the Bing Grounding resource via Microsoft.Bing/accounts.
    # NOTE: Bing.Search.v7 (Microsoft.CognitiveServices kind) is deprecated and no longer valid.
    # The replacement is Microsoft.Bing/accounts with kind=Bing.Grounding and SKU=G1.
    $bingUrl = "https://management.azure.com/subscriptions/$SubId/resourceGroups/$ResourceGroup/providers/Microsoft.Bing/accounts/$name"
    $bingBody = "{`"location`":`"global`",`"kind`":`"Bing.Grounding`",`"sku`":{`"name`":`"G1`"},`"properties`":{}}"
    Invoke-AzRestJson -Method "PUT" -Url $bingUrl -Body $bingBody -ApiVersion "2025-05-01-preview" | Out-Null

    $bingKey = (Invoke-AzRestJsonObject -Method "POST" -Url "https://management.azure.com/subscriptions/$SubId/resourceGroups/$ResourceGroup/providers/Microsoft.Bing/accounts/$name/listKeys" -ApiVersion "2025-05-01-preview").key1

    # Register as connection in the Foundry project
    $connName = "bing-$name"
    $connUrl = "https://management.azure.com$ProjectResourceId/connections/$connName"
    $connBody = "{`"properties`":{`"category`":`"GroundingWithBingSearch`",`"target`":`"https://api.bing.microsoft.com`",`"authType`":`"ApiKey`",`"credentials`":{`"key`":`"$bingKey`"}}}"

    $conn = (Invoke-AzRestWithRetry -Method "PUT" -Url $connUrl -Body $connBody -ApiVersion "2025-04-01-preview") | ConvertFrom-Json
    $connId = $conn.id

    Write-Success "Bing connection '$connName' created"
    return @{
        ConnectionName = $connName
        ConnectionId   = $connId
    }
}

# ---------------------------------------------------------------------------
# STEP 8 — Foundry MCP Server connection (portal-guided, confirmed by script)
# ---------------------------------------------------------------------------
function Get-McpConnection {
    param(
        [string]$ProjectResourceId,
        [string]$TenantId,
        [string]$ProjectName
    )

    Write-Step "Foundry MCP Server connection..."

    $knownName  = "FoundryMCPServerpreview"
    $apiVersion = "2025-04-01-preview"
    $mgmtUrl    = "https://management.azure.com$ProjectResourceId/connections/$knownName"

    # Check if connection already exists
    $existing = try {
        $raw = az rest --method GET --url $mgmtUrl `
            --url-parameters "api-version=$apiVersion" -o json 2>$null
        $raw | ConvertFrom-Json
    } catch { $null }

    if ($existing -and "$($existing.id)".Trim()) {
        Write-Success "MCP connection already exists."
        return @{ ConnectionId = "$($existing.id)".Trim() }
    }

    # Not found — guide the implementer through the portal
    $encodedId  = [Uri]::EscapeDataString($ProjectResourceId)
    $portalUrl  = "https://ai.azure.com/build/tools?wsid=$encodedId&tid=$TenantId"

    Write-Host ""
    Write-Host "  ┌──────────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "  │  MANUAL STEP REQUIRED — Foundry MCP Server Connection            │" -ForegroundColor Cyan
    Write-Host "  │  This connection cannot yet be created via CLI (preview API gap). │" -ForegroundColor Cyan
    Write-Host "  └──────────────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Open this URL in your browser (project Tools page):" -ForegroundColor White
    Write-Host ""
    Write-Host "    $portalUrl" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "  Then follow these steps:" -ForegroundColor White
    Write-Host ""
    Write-Host "    1. Click  'Build'  in the top navigation menu" -ForegroundColor White
    Write-Host "       then click the  Tools  icon (screwdriver & wrench) in the left nav" -ForegroundColor White
    Write-Host "    2. Click  [ + Add tool ]  in the toolbar" -ForegroundColor White
    Write-Host "    3. In the panel that opens, click  [ Catalog ]" -ForegroundColor White
    Write-Host "    4. In the search box type:  Foundry MCP Server" -ForegroundColor White
    Write-Host "    5. Select  'Foundry MCP Server (preview)'  from the results" -ForegroundColor White
    Write-Host "    6. An Authentication dialog appears — leave defaults as-is:" -ForegroundColor White
    Write-Host "         OAuth Provider : Managed  (Microsoft managed OAuth app)" -ForegroundColor DarkGray
    Write-Host "         Audience       : https://mcp.ai.azure.com  (pre-filled, do not change)" -ForegroundColor DarkGray
    Write-Host "       Click  [ Connect ]  to confirm" -ForegroundColor White
    Write-Host "    7. After connecting you land on the tool page — the connection name" -ForegroundColor White
    Write-Host "       appears in bold at the very top next to the purple Foundry icon" -ForegroundColor White
    Write-Host "       (it will look like:  FoundryMCPServerpreview)" -ForegroundColor DarkGray
    Write-Host "    8. Copy that name" -ForegroundColor White
    Write-Host ""
    Write-Host "  Press Enter here once the connection has been created." -ForegroundColor Yellow
    Read-Host "  [ Enter to continue ]" | Out-Null

    $inputName = Read-Host "  Paste the connection name from the portal (Enter for '$knownName')"
    $connName  = if ([string]::IsNullOrWhiteSpace($inputName)) { $knownName } else { $inputName.Trim() }

    # Verify the connection exists
    Write-Host "  Verifying '$connName'..." -ForegroundColor DarkGray
    $verifyUrl = "https://management.azure.com$ProjectResourceId/connections/$connName"
    $verified  = try {
        $raw = az rest --method GET --url $verifyUrl `
            --url-parameters "api-version=$apiVersion" -o json 2>$null
        $raw | ConvertFrom-Json
    } catch { $null }

    if ($verified -and "$($verified.id)".Trim()) {
        $connId = "$($verified.id)".Trim()
        Write-Success "Verified: $connId"
        return @{ ConnectionId = $connId }
    }

    Write-Warn "Could not verify '$connName' — connection may not exist yet or the name is incorrect."
    Write-Warn "Writing constructed ID to .env. Rerun or edit FOUNDRY_MCP_CONNECTION_ID manually after creating it."
    return @{ ConnectionId = "$ProjectResourceId/connections/$connName" }
}

# ---------------------------------------------------------------------------
# STEP 9 — Write .env
# ---------------------------------------------------------------------------
function Write-EnvFile {
    param(
        [string]$TenantId, [string]$SubId, [string]$ResourceGroup,
        [hashtable]$Account, [hashtable]$Project, [hashtable]$Models,
        [hashtable]$Search, [hashtable]$Bing, [hashtable]$Mcp,
        [string]$ApiKey
    )

    $envPath = Join-Path $PSScriptRoot ".env"

    @"
# =============================================================================
# Agentic AI Immersion Day - Environment Configuration
# Generated by provision.ps1 on $(Get-Date -Format "yyyy-MM-dd HH:mm")
# =============================================================================

# =============================================================================
# AZURE AUTHENTICATION
# =============================================================================
TENANT_ID=$TenantId
AZURE_SUBSCRIPTION_ID=$SubId
AZURE_RESOURCE_GROUP=$ResourceGroup
AZURE_PROJECT_NAME=$($Project.Name)

# =============================================================================
# Microsoft Foundry PROJECT
# =============================================================================
AI_FOUNDRY_PROJECT_ENDPOINT=$($Project.Endpoint)
AZURE_AI_PROJECT_ENDPOINT=$($Project.Endpoint)
PROJECT_RESOURCE_ID=$($Project.ResourceId)

# =============================================================================
# MODEL DEPLOYMENTS
# =============================================================================
AZURE_AI_MODEL_DEPLOYMENT_NAME=$($Models.ChatDeploymentName)
AZURE_AI_MODEL_DEPLOYMENT_NAMES=$($Models.ChatDeploymentNames)
EMBEDDING_MODEL_DEPLOYMENT_NAME=$($Models.EmbeddingDeploymentName)
EMBEDDING_MODEL_DEPLOYMENT_NAMES=$($Models.EmbeddingDeploymentNames)

# =============================================================================
# AZURE OPENAI DIRECT ACCESS
# =============================================================================
AZURE_OPENAI_ENDPOINT=$($Account.OpenAIEndpoint)
AZURE_OPENAI_API_KEY=$ApiKey
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=$($Models.ChatDeploymentName)

# =============================================================================
# BING GROUNDING
# =============================================================================
GROUNDING_WITH_BING_CONNECTION_NAME=$($Bing.ConnectionName)
BING_CONNECTION_ID=$($Bing.ConnectionId)

# =============================================================================
# AZURE AI SEARCH
# =============================================================================
AZURE_AI_SEARCH_ENDPOINT=$($Search.Endpoint)
AZURE_AI_SEARCH_API_KEY=$($Search.ApiKey)
AZURE_AI_SEARCH_API_VERSION=$($Search.ApiVersion)
SEARCH_AUTHENTICATION_METHOD=$($Search.AuthMethod)
AZURE_SEARCH_INDEX_NAME=$($Search.IndexName)

# =============================================================================
# MCP TOOLS
# =============================================================================
FOUNDRY_MCP_CONNECTION_ID=$($Mcp.ConnectionId)

# =============================================================================
# OBSERVABILITY & TRACING
# =============================================================================
AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true
AZURE_SDK_TRACING_IMPLEMENTATION=opentelemetry
ENABLE_SENSITIVE_DATA=true

# =============================================================================
# OPTIONAL CONFIGURATION
# =============================================================================
# APPLICATIONINSIGHTS_CONNECTION_STRING=<your-app-insights-connection-string>
# OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
# OTEL_SERVICE_NAME=agentic-ai-workshop
# ENABLE_CONSOLE_EXPORTERS=true
"@ | Set-Content -Path $envPath -Encoding utf8

    Write-Success ".env written to $envPath"
}

# ---------------------------------------------------------------------------
# Pre-flight: model quota check
# ---------------------------------------------------------------------------
function Test-ModelQuota {
    param([string]$Location, [string]$SubId)

    Write-Step "Pre-flight: model quota check ($Location)..."

    $usages = try {
        Invoke-AzJson @("cognitiveservices", "usage", "list", "--location", $Location)
    }
    catch {
        Write-Warn "Could not retrieve quota data — skipping check: $($_.Exception.Message)"
        return
    }

    # Deployable SKUs only — exclude Batch, Provisioned, FineTuned, AccountCount, etc.
    $relevant = $usages | Where-Object {
        $_.name.value -match '^OpenAI\.(GlobalStandard|Standard)\.' -and
        $_.name.value -notmatch 'finetune|AccountCount'
    } | Sort-Object { $_.name.value }

    $needed = 50  # capacity units requested per deployment (1 unit = 1 000 TPM)
    $issues = @()

    Write-Host ("  {0,-52} {1,7}  {2,7}  {3,9}" -f "Model", "Limit", "Used", "Available") -ForegroundColor DarkGray
    Write-Host ("  " + ("-" * 79)) -ForegroundColor DarkGray

    foreach ($u in $relevant) {
        $avail = $u.limit - $u.currentValue
        $warn  = $avail -lt $needed
        $mark  = if ($warn) { " ⚠" } else { "" }
        $color = if ($warn) { "Yellow" } else { "DarkGray" }
        $line  = "{0,-52} {1,7:F0}  {2,7:F0}  {3,9:F0}{4}" -f $u.name.value, $u.limit, $u.currentValue, $avail, $mark
        Write-Host "  $line" -ForegroundColor $color
        if ($warn) { $issues += $u.name.value }
    }

    Write-Host ""

    if ($issues.Count -eq 0) {
        Write-Success "Quota looks good — all models have >= $needed units available."
    }
    else {
        Write-Warn "$($issues.Count) model(s) have < $needed units available (needed per deployment)."
        Write-Host "  You can still continue — the model selection step will let you pick" -ForegroundColor White
        Write-Host "  an alternative (e.g. gpt-4o-mini) that has sufficient quota above." -ForegroundColor White
        Write-Host ""
        Write-Host "  To request a quota increase instead:" -ForegroundColor White
        Write-Host "    https://aka.ms/oai/quotaincrease" -ForegroundColor DarkCyan
        Write-Host "  Or via Azure portal:" -ForegroundColor White
        Write-Host "    https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/QuotaRequestV2" -ForegroundColor DarkCyan
        Write-Host ""
        $cont = Read-Host "  Continue provisioning anyway? (Y/n)"
        if ($cont -match "^[Nn]$") {
            Write-Warn "Provisioning cancelled. Resolve quota first, then rerun."
            exit 1
        }
    }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
function Main {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   Azure Resource Provisioning — Agentic AI Immersion          ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    $account = Get-SubscriptionInfo
    $tenantId = $account.tenantId
    $subId = $account.id

    $rg = New-WorkshopResourceGroup -SubId $subId

    Test-ModelQuota -Location $rg.Location -SubId $subId

    $aiAccount = New-AIServicesAccount -ResourceGroup $rg.Name -Location $rg.Location -SubId $subId

    $apiKey = (Invoke-AzJson @(
            "cognitiveservices", "account", "keys", "list",
            "--name", $aiAccount.Name,
            "--resource-group", $rg.Name
        )).key1

    $project = New-FoundryProject `
        -ResourceGroup $rg.Name -Location $rg.Location `
        -SubId $subId -AccountName $aiAccount.Name -AccountId $aiAccount.Id

    $models = New-ModelDeployments -ResourceGroup $rg.Name -AccountName $aiAccount.Name -SubId $subId

    $search = New-SearchService `
        -ResourceGroup $rg.Name -Location $rg.Location `
        -SubId $subId -ProjectResourceId $project.ResourceId

    $bing = New-BingConnection `
        -ResourceGroup $rg.Name -Location $rg.Location `
        -SubId $subId -ProjectResourceId $project.ResourceId

    $mcp = Get-McpConnection `
        -ProjectResourceId $project.ResourceId `
        -TenantId $tenantId `
        -ProjectName $project.Name

    Set-WorkshopRbac `
        -SubId $subId -ResourceGroup $rg.Name `
        -ProjectManagedIdentityPrincipalId $project.ManagedIdentityPrincipalId

    Write-EnvFile `
        -TenantId $tenantId -SubId $subId -ResourceGroup $rg.Name `
        -Account $aiAccount -Project $project -Models $models `
        -Search $search -Bing $bing -Mcp $mcp -ApiKey $apiKey

    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║   Provisioning complete!                                       ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Resource Group : $($rg.Name)" -ForegroundColor Cyan
    Write-Host "  AI Account     : $($aiAccount.Name)" -ForegroundColor Cyan
    Write-Host "  Project        : $($project.Name)" -ForegroundColor Cyan
    Write-Host "  Chat Model     : $($models.ChatDeploymentName)" -ForegroundColor Cyan
    Write-Host "  Chat Models    : $($models.ChatDeploymentNames)" -ForegroundColor Cyan
    Write-Host "  Embedding Model: $($models.EmbeddingDeploymentName)" -ForegroundColor Cyan
    Write-Host "  Embedding Models: $($models.EmbeddingDeploymentNames)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  .env file has been written. Start with:" -ForegroundColor White
    Write-Host "  jupyter notebook agent-framework/agents/" -ForegroundColor White
    Write-Host ""
}

Main
