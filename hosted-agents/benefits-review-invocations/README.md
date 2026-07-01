# Employee Benefits Review — Invocations agent

A minimal **Microsoft Foundry hosted agent** using the **Invocations** protocol: one structured
request → one structured response (fire-and-forget, no tools, deterministic). Good for batch jobs
and API-to-API pipelines.

## Files
- `main.py` — builds the agent (`FoundryChatClient` → `Agent`) and serves it on `InvocationsHostServer`
- `agent.yaml` / `agent.manifest.yaml` — Foundry agent definition + deploy manifest
- `Dockerfile`, `requirements.txt` — container build
- `test_local.py` — build the agent and run one review against your project (no deploy needed)

## Run locally
```bash
# from repo root, workshop venv active, after `az login`
python hosted-agents/benefits-review-invocations/test_local.py
```
Reads the repo-root `.env` (needs `AI_FOUNDRY_PROJECT_ENDPOINT` + `AZURE_AI_MODEL_DEPLOYMENT_NAME`).
Run the full container with `pip install -r requirements.txt && python main.py` (port 8088).

## Deploy
`azd ai agent init` (pick **ZIP upload**, **Python 3.14**, `main.py`) → `azd deploy`. See [../README.md](../README.md#deploy-to-foundry--step-by-step).

## Test after deployment

This is the **Invocations** protocol: send one structured benefits program, get one Markdown review back. The payload must be **JSON with a `message` field** (a plain string returns HTTP 500 — the server calls `request.json()`).

```bash
azd ai agent invoke benefits-review-invocations '{"message":"Review this employee benefits program: 200-employee fintech; basic health (employee only), 5% match, 12 days leave, no life/dental/parental."}'
```

More sample payloads to try:

| # | Payload (one structured request) | Expect |
|---|----------------------------------|--------|
| 1 | `Review: 1,000-employee manufacturer; full-family health, 8% pension match, 25 days leave, 2x life, income protection, no wellness budget.` | Strong P50–P75 positioning; gap = wellness |
| 2 | `Review: 30-person startup; stipend-only health, no retirement plan, unlimited leave, equity-heavy comp.` | Gaps in retirement + risk benefits; quick-win recs |
| 3 | `Review: 500-employee retailer; family health, 4% match, 15 days leave, dental, no parental, no income protection.` | Below-market match + parental gap |

Review output sections: **Summary → Strengths → Gaps → Benchmark Positioning (P25/P50/P75) → Recommendations**. It states assumptions and never asks follow-ups (deterministic, single-shot).
