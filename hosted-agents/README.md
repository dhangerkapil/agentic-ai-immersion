# 🚀 Hosted Agents

[← Back to main README](../README.md)

Two **Microsoft Foundry Hosted Agents** that demonstrate the two hosting **protocols** on a
single, generic FSI scenario — **employee benefits**. You supply the agent code, a model, and
(optionally) tools and skills; Foundry runs and scales the container.

| Agent | Protocol | What it shows |
|-------|----------|---------------|
| [`benefits-review-invocations/`](benefits-review-invocations) | **Invocations** | A single structured request → structured response (fire-and-forget). |
| [`benefits-advisor-responses/`](benefits-advisor-responses) | **Responses** | Multi-turn, streaming, model-directed tools — **Foundry Toolbox** + **Foundry Skills**. |

> These are deliberately minimal teaching examples. The same agent-build pattern
> (`FoundryChatClient` → `Agent` → host server) is used for both — only the **host server**
> (and therefore the protocol) differs.

## Invocations vs Responses — when to use which

| Dimension | Invocations (Review) | Responses (Advisor) |
|-----------|----------------------|---------------------|
| Interaction | Single structured request → response | Multi-turn natural conversation |
| Tool use | None (deterministic) | Model-directed (decides when to search/compute) |
| Streaming | No (batch result) | Token-by-token (OpenAI-compatible) |
| State | Stateless | Session history managed by the platform |
| Best for | Batch, API-to-API, deterministic pipelines | Interactive advisory, research, exploration |
| Host server | `InvocationsHostServer(agent)` | `ResponsesHostServer(agent)` |

## Prerequisites

- A **Microsoft Foundry project** with a deployed chat model (e.g. `gpt-4.1-mini` or `gpt-4o`).
- **Azure CLI** signed in: `az login`.
- **Python 3.12+** locally; the Foundry **hosted** runtime must be **Python 3.14**.
- **Entra (AAD) auth** — these agents use `DefaultAzureCredential` (no API keys). Locally you need
  the **Foundry User** role on the project.

## Run locally

Each agent has a `test_local.py` that builds the agent and runs one turn against your project.
They read the workshop root `.env` (or the agent-local `.env`).

```bash
# from the repo root, with the workshop venv active
python hosted-agents/benefits-review-invocations/test_local.py
python hosted-agents/benefits-advisor-responses/test_local.py
```

To run the full container locally, install the agent's `requirements.txt` and run `python main.py`
(starts the host server on port 8088).

### Advisor extras: Toolbox + Skills (optional)

The advisor can use a **Foundry Toolbox** (web_search + code_interpreter) and **Foundry Skills**:

1. **Skills** are bundled as `skills/<name>/SKILL.md` and embedded into the agent's instructions
   at startup (progressive disclosure). Set `SKILL_NAMES` to choose which to embed (default: both).
2. **Toolbox**: create a Foundry Toolbox named in `TOOLBOX_NAME` containing `web_search` and
   `code_interpreter`, then set `TOOLBOX_NAME`.

If `TOOLBOX_NAME` / `SKILL_NAMES` are unset, the advisor still runs — just without tools/skills.

## Deploy to Foundry — step by step

Each agent ships an `agent.yaml`, `agent.manifest.yaml`, and `Dockerfile`. Foundry builds and runs the container — you only push code.

**Prerequisites:** [Azure Developer CLI (`azd`)](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd) v1.26+, `az login`, a Foundry project with a chat model deployed, and the **Foundry User** role on the project. One-time: `azd config set auth.useAzCliAuth true` (reuse `az` login, no browser) and install the agents extension: `azd extension install azure.ai.agents`.

```bash
cd hosted-agents/benefits-advisor-responses      # or benefits-review-invocations

azd ai agent init        # wizard: pick "Source Code (ZIP upload)", runtime "Python 3.14", entry main.py, remote build
azd deploy               # zips, uploads, server-side build + provisions the hosted agent (no ACR; takes ~2 min)

# Smoke-test the deployed agent
azd ai agent invoke <agent-name> '<sample payload>'
```

> **Runtime must be Python 3.14.** Choosing 3.13 fails the remote build: `agent-framework[foundry]` pulls `agent-framework-hyperlight`, which needs `hyperlight-sandbox-backend-wasm` (no published wheel) only for `python<3.14`. The agents' `requirements.txt` are pinned to `agent-framework[foundry]==1.9.0` + `agent-framework-foundry-hosting==1.0.0a260618` to keep the resolver consistent.

Then call it from Python: `AIProjectClient(endpoint=..., credential=DefaultAzureCredential(), allow_preview=True).get_openai_client(agent_name="<agent-name>")`. Tear down with `azd down`. For a full click-by-click walkthrough see notebook [10-hosted-agent-with-skills](../azure-ai-agents/10-hosted-agent-with-skills.ipynb); for an automated **CI/CD pipeline** (build → promote → smoke test → rollback) see the [`AgentOps/`](../AgentOps) example.

## 🔗 Dependency sync (avoid version drift)

There are two pinning layers; **only the Agent Framework version must match** between them:

| File | Scope | Pinning |
|------|-------|---------|
| `../requirements.in` → `../requirements.txt` | Notebooks + dev (source of truth, full lock) | `agent-framework==1.9.0`, `foundry-hosting==1.0.0a260618` |
| `benefits-*/requirements.txt` | Hosted agent only (minimal) | mirror the same two pins |

**Rule:** bump `agent-framework[foundry]` and `agent-framework-foundry-hosting` in root `requirements.in` first, re-lock with `pip-compile`, then mirror those two lines into each `benefits-*/requirements.txt` and redeploy. The hosted files stay minimal (Foundry installs them server-side) so they don't need the full lock — only matching framework versions, otherwise local notebooks and deployed agents diverge.

## ✅ Test after deployment

Confirm the agents are live, then invoke them with sample questions.

```bash
# 1. Confirm both appear in the project
python -c "import os; from dotenv import load_dotenv; load_dotenv(); from azure.identity import DefaultAzureCredential; from azure.ai.projects import AIProjectClient; c=AIProjectClient(endpoint=os.environ['AI_FOUNDRY_PROJECT_ENDPOINT'],credential=DefaultAzureCredential()); print([a.name for a in c.agents.list()])"

# 2. Invoke each (CLI). Invocations needs JSON {"message"}; Responses takes a plain string.
azd ai agent invoke benefits-review-invocations '{"message":"Review: 200-employee fintech; employee-only health, 5% match, 12d leave, no life/dental/parental."}'
azd ai agent invoke benefits-advisor-responses  "What's a competitive retirement match for a 500-employee tech firm, vs market P50?"
```

**Benefits Review** (Invocations) — paste a full program, get a structured review:

| Sample payload | Expected |
|----------------|----------|
| 200-emp fintech; employee-only health, 5% match, 12d leave, no life/dental/parental | Gaps: dental, life, parental; quick-win recs |
| 1,000-emp manufacturer; family health, 8% pension, 25d leave, 2x life, income protection | P50–P75; gap = wellness |
| 30-person startup; stipend health, no retirement, unlimited leave, equity-heavy | Retirement + risk-benefit gaps |

**Benefits Advisor** (Responses) — ask conversational questions:

| Sample question | Exercises |
|-----------------|-----------|
| Compare dental+vision vs wellness stipend for 500 staff — cost table | code_interpreter |
| Project cost of 12→20 leave days for 250 staff at 60 CU/hr | calculation |
| Explain P50 benchmark; how to move P25→P50 | skills |
| Current 2026 parental-leave top-up trends | web_search (Toolbox) |

The portal **Agent playground** (URL printed by `azd deploy`) is the quickest way to try these interactively. Per-agent payloads: [review](benefits-review-invocations/README.md#test-after-deployment) · [advisor](benefits-advisor-responses/README.md#test-after-deployment).

## 🧭 Troubleshooting

| Issue | Solution |
|-------|----------|
| **401 / 403 on `test_local.py`** | Role propagation — the **Foundry User** role takes **5–15 min** to apply. Wait, then retry. Run [setup-permissions](../README.md#step-6-required-azure-rbac-roles--storage-access) if you haven't. |
| **HTTP 500 on `invoke` (Review/Invocations)** | The Invocations server calls `request.json()` — send **JSON**: `'{"message":"..."}'`, not a plain string. (Responses/Advisor accepts a plain string.) |
| **HTTP 500 model access from a deployed agent** | The agent's **Instance Identity** (see `azd ai agent show`) needs `Cognitive Services OpenAI User` on the Foundry account. Grant it, wait 5–15 min, retry. |
| **`az login` / wrong subscription** | `az login` then `az account set --subscription <id>`; confirm with `az account show`. |
| **Missing values** | These agents read the repo-root `.env` — no API keys; leave `AZURE_OPENAI_API_KEY` blank. |
| **`azd` not found** | [Install azd](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd). |

## 📚 Learn more
