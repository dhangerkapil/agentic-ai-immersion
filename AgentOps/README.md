# 🛠️ AgentOps — GitOps for a Foundry Hosted Agent

[← Back to main README](../README.md)

A complete, **GitOps + GitHub Actions** delivery example for a Microsoft Foundry **hosted
agent** — an FSI **Employee Benefits Concierge**. Every artefact that affects the agent
(prompt, config, tools, infra) is version-controlled, reviewed in a pull request, and
deployed by automation. No one deploys from their laptop.

> **Scope:** a working **single-project (dev)** deploy, with **test/prod promotion
> documented as a reference**.

## Why GitOps for agents?

Prompts drift, tools change, models get upgraded — each can alter behaviour silently.
Treating the agent definition as source code gives you review gates, automated validation,
traceable deployments, and a tested rollback path.

## Repository structure

```
AgentOps/
├── src/
│   ├── agents/      agent.py + agent_config.json   (entry point + versioned settings)
│   ├── prompts/     system.txt + instructions.txt  (prompts as reviewable files)
│   └── tools/       toolbox_config.py              (versioned Foundry Toolbox, "toolbox-as-code")
├── tests/           unit / integration / smoke
├── infra/           main.bicep + environments/{dev,test,prod}.parameters.json
├── scripts/         validate_agent.py + smoke_test.py
├── .github/         workflows/{validate,build-deploy,rollback}.yml + CODEOWNERS
├── Dockerfile
└── docs/architecture.md
```

## Pipeline (commit → production)

1. **validate.yml** (on PR) — validate config + prompts, run unit tests.
2. **build-deploy.yml** (on merge) — build the image **once**, push to ACR, deploy to **dev**, smoke-test.
3. Promotion to **test** then **prod** reuses the *same image tag* behind GitHub **Environment approval gates** (reference job in `build-deploy.yml`).
4. **rollback.yml** (manual) — redeploy a previous known-good image tag.

> **Activating the workflows:** they live here for self-containment. GitHub Actions only runs
> workflows from the **repository root** `.github/workflows/`. To run this pipeline, either use
> `AgentOps/` as its own repository, or copy these workflows to the repo root and set the
> required secrets/variables below.

## Run locally

```bash
# from AgentOps/, with the workshop venv active
python scripts/validate_agent.py     # config + prompt validation (offline)
pytest tests/unit -v                  # unit tests (offline)
python scripts/smoke_test.py          # builds the agent + one live turn (needs az login)
```

Run the container locally: `pip install -r requirements.txt && python src/agents/agent.py`
(serves the Responses protocol on port 8088).

## Activate the pipeline (first time)

GitHub Actions only runs workflows from the **repository root** `.github/workflows/`, so these ship in `AgentOps/.github/workflows/` for self-containment and must be activated once:

```bash
# 1. Copy the workflows to the repo root so Actions picks them up
cp AgentOps/.github/workflows/*.yml .github/workflows/

# 2. Set up OIDC federated login (no stored passwords): create an Entra app +
#    federated credential for this repo. Guide:
#    https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect

# 3. Add repo secrets + variables: Settings -> Secrets and variables -> Actions (see table below)
# 4. Open a PR  -> validate.yml runs; merge -> build-deploy.yml deploys to dev;
#    approve the environment gate to promote test -> prod; rollback.yml is manual.
```

## Required CI secrets & variables (to activate the pipeline)

| Kind | Name | Purpose |
|------|------|---------|
| Secret | `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_SUBSCRIPTION_ID` | OIDC federated login (no stored passwords) |
| Variable | `FOUNDRY_PROJECT_DEV` (+ `_TEST` / `_PROD`) | Target Foundry project per environment |

The agent uses **managed identity / Entra** at runtime (no API keys). Secrets, if any, come from
**Azure Key Vault**.

## 🧭 Troubleshooting

| Issue | Solution |
|-------|----------|
| **401 / 403 on smoke test** | Role propagation — the **Foundry User** role takes **5–15 min**. Wait, then retry. See [setup-permissions](../README.md#step-6-required-azure-rbac-roles--storage-access). |
| **`az login` needed** | `python scripts/smoke_test.py` runs a live turn — sign in with `az login` first. |
| **Workflows don't trigger** | Actions only run from the **repo-root** `.github/workflows/`; copy them up (see above) and set the secrets/variables. |

## 📚 Learn more
- [OIDC from GitHub to Azure](https://learn.microsoft.com/azure/developer/github/connect-from-azure-openid-connect)
- [Azure Container Registry](https://learn.microsoft.com/azure/container-registry/)
- [OpenGitOps principles](https://opengitops.dev/)
