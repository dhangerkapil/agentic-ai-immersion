# 🧪 Workshop End-to-End Validation Review

**Reviewer:** Independent first-time user (no prior knowledge of repo/tech)
**Date:** 2026-06-28 (re-validated 2026-06-29 via self-driving runner)
**Method:** Followed `README.md` step by step; ran **all** notebooks + code live, fixed gaps.
**Verdict:** ✅ Runnable end-to-end. Self-driving re-validation: **58/59 PASS** (56 notebooks + 2 hosted-agent smoke tests + AgentOps pytest); the lone fail was a transient model 408 that passes on re-run. Both hosted agents redeployed and invoked live. Setup-script bug fixed; hosted-agent deploy/runtime/invoke gaps documented.

---

## Result summary

| Step | Result |
|------|--------|
| 1. Clone + Python 3.12+ | ✅ env is Python 3.14.5 (≥3.12, works) |
| 2. venv + `pip install -r requirements.txt` | ✅ azure-ai-projects 2.2.0 et al. present |
| 3. `az login` / `az account show` | ✅ documented + works |
| 4. Create project + deploy models | ✅ documented with portal steps |
| 5. `.env` (repo root, Entra-only) | ✅ all keys present; blank API key correct |
| 6. `scripts/setup-permissions.ps1` | 🔴→✅ **bug fixed** (see below); now grants user + project MI + search MI |
| 7. Verify command | ✅ "Connected to Foundry" |
| Phase 1 `1-basics.ipynb` | ✅ exit 0 |
| **Full notebook suite (56)** | ✅ azure-ai-agents 15, agent-framework 36, observability-and-evals 5 — all PASS |
| AgentOps unit+integration tests | ✅ 4 passed |
| hosted-agents `test_local.py` (both) | ✅ live 200 |
| Foundry agents | ✅ kept — deletion code commented `# [kept-in-foundry]` in 11 notebooks per request |

---

## Gaps found & fixed during this run

1. **CRITICAL — `scripts/setup-permissions.ps1` skipped all project-MI roles.** The Project managed identity wouldn't resolve (`principal id not available`), so the #1 grant (`Foundry User`, plus `Cognitive Services User`) was silently skipped → would cause `ProjectMIUnauthorized`. Root cause: `az rest` returns empty inside the script context. **Fix:** resolve via `az resource show --ids "<account>/projects/<project>"` (matches the working CLI pattern) with `az rest` fallback; added `$PSNativeCommandUseErrorActionPreference=$false` and a loud red failure message. Now all five project-MI roles are assigned.
2. **README setup order** — `.env` came before creating the project; `az login` was implicit. Reordered to clone → venv → `az login` → create project → `.env` → roles → verify.
3. **Deployment steps** — added `azd ai agent init` + `azd deploy` to `hosted-agents/README.md` and pipeline activation to `AgentOps/README.md`; added per-agent READMEs and `azure.yaml`. Note: the `azure.ai.agents` azd extension has no `deploy` subcommand — `init` runs a wizard, then plain `azd deploy` ships it.
4. **Accuracy** — Entra blank-key + repo-root `.env` + Python 3.12 made consistent across folder READMEs; stale `red_teams`→`beta.red_teams`; created `byouc/README.md`; back-links + 401/403 troubleshooting.
5. **Verify command** — fixed to `load_dotenv()` so it doesn't `KeyError`.
6. **Hosted-agent deploy prerequisites (now documented)** — needed `azd` (winget install) with PATH refresh per shell, `azd config set auth.useAzCliAuth true` (no browser), `AZD_SKIP_FIRST_RUN=true`, and the `azure.ai.agents` azd extension. Deploy = `azd ai agent init` (ZIP upload, Remote build) then `azd deploy`.
7. **Runtime + requirements pin (CRITICAL for deploy)** — hosted runtime MUST be **Python 3.14**; on 3.13 the remote build fails ResolutionImpossible because `agent-framework[foundry]` pulls `agent-framework-hyperlight` needing `hyperlight-sandbox-backend-wasm` (no published dist) for `python<3.14`. Also pinned both hosted-agents `requirements.txt` to `agent-framework[foundry]==1.9.0` + `agent-framework-foundry-hosting==1.0.0a260618` (loose `>=1.2.2` resolved to 1.2.2 vs `agent-framework-orchestrations` needing core>=1.9.0).
8. **Hosted-agent invoke payload (CLI) — protocol-specific.** The **Invocations** agent server calls `request.json()`, so `azd ai agent invoke` must receive **JSON**: `'{"message":"..."}'`. A plain string returns **HTTP 500** (`JSONDecodeError`). The **Responses** agent accepts a plain string. Fixed the sample commands in `hosted-agents/README.md` + the review agent README and added a troubleshooting row.
9. **Hosted-agent instance identity needs model RBAC.** A deployed agent runs under its own **Instance Identity** (`azd ai agent show`); it needs `Cognitive Services OpenAI User` on the Foundry account to call the model. Documented as a troubleshooting row (grant + wait 5–15 min).
10. **`.env.example` search auth was key-first, contradicting Entra-only.** Only `context-providers/2` reads `AZURE_AI_SEARCH_API_KEY` (and treats it as optional); `SEARCH_AUTHENTICATION_METHOD` is not read by any notebook. Made the template Entra-first: key blank by default (RBAC), `SEARCH_AUTHENTICATION_METHOD=rbac` marked informational.

## Independent re-validation (full suite, self-driving runner)

Ran `scripts/run-workshop-validation.ps1` end-to-end (logs in `.validation-run/`, report in `WORKSHOP-VALIDATION-REPORT.md`): **58 / 59 PASS** — all 15 azure-ai-agents, 36 agent-framework, 5 observability-and-evaluations, both hosted-agent `test_local.py`, and AgentOps pytest. The single FAIL was a **transient server-side 408 Timeout** from the model on `agent-framework/agents/azure-ai-agents/5-azure-ai-with-code-interpreter.ipynb` (not a code/doc defect) — re-running it passes. Both hosted agents were also redeployed and invoked live end-to-end.

## Notes / minor
- Python 3.14 works but cold imports are ~3s; pin **3.12** if you want fastest start.
- `threads/2-redis` needs a local Redis; `azd` + Python 3.14 runtime needed for hosted deploy — documented. Both hosted agents deployed live & verified.
- Role propagation 5–15 min; retry on 401/403.

## Remaining recommendations
- Run `setup-permissions.ps1` once and wait for propagation before notebooks 2–8.
- Optional: pin requirements for 3.12 to match the documented version.
