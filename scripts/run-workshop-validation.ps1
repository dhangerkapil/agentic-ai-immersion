<#
.SYNOPSIS
    Self-contained, end-to-end workshop validation runner.

.DESCRIPTION
    Runs every workshop phase without interactive supervision:
      Phase 1  azure-ai-agents/                notebooks
      Phase 2  agent-framework/                notebooks
      Phase 3  observability-and-evaluations/  notebooks
      Phase 4  hosted-agents/ test_local.py    (both agents)
      Phase 5  AgentOps/ pytest                (unit + integration)
    Notebooks execute to throwaway copies (originals untouched). Each step's
    stdout/stderr is tee'd to a per-step log. A consolidated markdown report is
    written at the end. Safe to launch once and leave; it waits for everything.

.PARAMETER Timeout
    Per-notebook execution timeout (seconds). Default 420.

.EXAMPLE
    pwsh -NoProfile -File scripts/run-workshop-validation.ps1
#>
param(
    [int]$Timeout = 420,
    [string[]]$Areas = @('azure-ai-agents', 'agent-framework', 'observability-and-evaluations')
)

$ErrorActionPreference = 'Continue'
$root   = Split-Path -Parent $PSScriptRoot
$py     = Join-Path $root '.venv\Scripts\python.exe'
$runDir = Join-Path $root '.validation-run'
$report = Join-Path $root 'WORKSHOP-VALIDATION-REPORT.md'
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$started = Get-Date
$results = New-Object System.Collections.Generic.List[object]

function Write-Status($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format 'HH:mm:ss'), $msg
    Write-Host $line
    Add-Content -Path (Join-Path $runDir 'progress.log') -Value $line
}

if (-not (Test-Path $py)) { Write-Status "FATAL: venv python not found at $py"; exit 2 }

# ── Phases 1-3: notebooks ────────────────────────────────────────────────────
foreach ($area in $Areas) {
    $target = Join-Path $root $area
    if (-not (Test-Path $target)) { Write-Status "SKIP area (missing): $area"; continue }
    $nbs = Get-ChildItem -Path $target -Recurse -Filter *.ipynb |
        Where-Object { $_.FullName -notmatch 'ipynb_checkpoints|\\\.venv\\|node_modules|\\my-hosted-agent\\' } |
        Sort-Object FullName
    Write-Status "AREA $area : $($nbs.Count) notebooks"
    $n = 0
    foreach ($nb in $nbs) {
        $n++; $rel = $nb.FullName.Replace("$root\", '')
        $log = Join-Path $runDir ("{0}_{1}.log" -f ($area -replace '[\\/]', '_'), $n)
        $t0 = Get-Date
        Push-Location $nb.DirectoryName
        & $py -m jupyter nbconvert --to notebook --execute $nb.Name --output-dir $env:TEMP `
            --output ("_v{0}.ipynb" -f $n) --ExecutePreprocessor.kernel_name=aiimmersion314 `
            --ExecutePreprocessor.timeout=$Timeout *> $log
        $code = $LASTEXITCODE
        Pop-Location
        $secs = [int]((Get-Date) - $t0).TotalSeconds
        $err = ''
        if ($code -ne 0) { $err = (Select-String -Path $log -Pattern 'Error|Exception|Traceback' | Select-Object -Last 1).Line }
        $results.Add([pscustomobject]@{ phase = $area; item = $rel; pass = ($code -eq 0); secs = $secs; log = $log; err = $err })
        Write-Status ("  {0}  {1} ({2}s)" -f ($(if ($code -eq 0) {'PASS'} else {'FAIL'})), $rel, $secs)
    }
}

# ── Phase 4: hosted-agent local smoke tests ──────────────────────────────────
foreach ($agent in @('benefits-review-invocations', 'benefits-advisor-responses')) {
    $dir = Join-Path $root "hosted-agents\$agent"
    if (-not (Test-Path (Join-Path $dir 'test_local.py'))) { continue }
    $log = Join-Path $runDir ("hosted_$agent.log"); $t0 = Get-Date
    Push-Location $dir; & $py test_local.py *> $log; $code = $LASTEXITCODE; Pop-Location
    $err = ''; if ($code -ne 0) { $err = (Select-String -Path $log -Pattern 'Error|Exception|Traceback' | Select-Object -Last 1).Line }
    $results.Add([pscustomobject]@{ phase = 'hosted-agents'; item = "$agent/test_local.py"; pass = ($code -eq 0); secs = [int]((Get-Date)-$t0).TotalSeconds; log = $log; err = $err })
    Write-Status ("  {0}  hosted/{1}" -f ($(if ($code -eq 0) {'PASS'} else {'FAIL'})), $agent)
}

# ── Phase 5: AgentOps tests ──────────────────────────────────────────────────
$aops = Join-Path $root 'AgentOps'
if (Test-Path $aops) {
    $log = Join-Path $runDir 'agentops_pytest.log'; $t0 = Get-Date
    Push-Location $aops; & $py -m pytest -q tests/unit tests/integration *> $log; $code = $LASTEXITCODE; Pop-Location
    $results.Add([pscustomobject]@{ phase = 'AgentOps'; item = 'pytest unit+integration'; pass = ($code -eq 0); secs = [int]((Get-Date)-$t0).TotalSeconds; log = $log; err = '' })
    Write-Status ("  {0}  AgentOps pytest" -f ($(if ($code -eq 0) {'PASS'} else {'FAIL'})))
}

# ── Report ───────────────────────────────────────────────────────────────────
$pass = ($results | Where-Object pass).Count; $fail = ($results | Where-Object { -not $_.pass }).Count
$dur  = [int]((Get-Date) - $started).TotalMinutes
$md = @()
$md += "# Workshop Validation Run"; $md += ""
$md += "- Started: $($started.ToString('u'))  |  Duration: ${dur} min"
$md += "- Result: **PASS=$pass  FAIL=$fail** of $($results.Count)"; $md += ""
$md += "| Phase | Item | Status | Secs |"; $md += "|-------|------|--------|------|"
foreach ($r in $results) { $md += "| {0} | {1} | {2} | {3} |" -f $r.phase, $r.item, ($(if ($r.pass) {'PASS'} else {'FAIL'})), $r.secs }
if ($fail) { $md += ""; $md += "## Failures"; foreach ($r in ($results | Where-Object {-not $_.pass})) { $md += "- $($r.item): $($r.err)  (log: $($r.log))" } }
$md -join "`n" | Set-Content -Path $report -Encoding utf8
Write-Status "DONE PASS=$pass FAIL=$fail -> $report"
