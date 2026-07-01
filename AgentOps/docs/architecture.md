# AgentOps — Architecture & Runbook

## Reference architecture

```
+---------------------------+
|    GitHub Repository       |
|  /src  /tests  /infra      |
|  /.github/workflows        |   single source of truth
+------------+--------------+
             | PR / push to main
             v
+---------------------------+
|   GitHub Actions           |
|  validate -> build ->      |
|  push -> deploy -> smoke   |
+------------+--------------+
             | image:<sha>
             v
+---------------------------+        +---------------------------+
|  Azure Container Registry  | -----> |   Foundry project (dev)    |
+---------------------------+        +------------+--------------+
                                                  | approval gate
                                                  v
                                     +---------------------------+
                                     |  Foundry test -> prod      |
                                     +------------+--------------+
                                                  v
                                     Azure Monitor / App Insights
```

Key decisions:

- The repository is the single source of truth for prompts, config, tools, and infra.
- The image is built **once per commit** and the same tag is promoted across environments.
- Environment promotion requires a **GitHub Environment approval**.
- Identity is **managed identity / Entra (OIDC)** — no long-lived secrets.

## Runbook

| Situation | Action |
|-----------|--------|
| Prompt change | Edit `src/prompts/*.txt` in a PR; `validate.yml` runs; merge deploys to dev. |
| New tool | Update `src/tools/toolbox_config.py`; the toolbox version is published in CI; the stable endpoint means no agent redeploy. |
| Bad deploy | Run `rollback.yml` with the last known-good image tag (from a previous build run). |
| Model upgrade | Bump `model`/`modelVersion` in `infra/environments/*.parameters.json` + `agent_config.json`; PR + evaluate before promotion. |

## Observability

Log the **agent version (image tag)**, session id, tool called, and outcome. Alert on error
rate and latency. Correlate request traces with the deployed image tag for fast debugging.
