# Employee Benefits Advisor — Responses agent

A **Microsoft Foundry hosted agent** using the **Responses** protocol: multi-turn, streaming,
model-directed tools. Adds a **Foundry Toolbox** (web search + code interpreter) and **Foundry
Skills** (embedded `SKILL.md` guidance). Good for interactive advisory and research.

## Files
- `main.py` — builds the agent and serves it on `ResponsesHostServer` (Toolbox + Skills wired in)
- `provision_skills.py` — registers the Skills with the project (`beta.skills`)
- `skills/<name>/SKILL.md` — cost-analysis + regulatory-guidance skills
- `agent.yaml` / `agent.manifest.yaml`, `Dockerfile`, `requirements.txt`
- `test_local.py` — build the agent and run one turn against your project

## Run locally
```bash
# from repo root, workshop venv active, after `az login`
python hosted-agents/benefits-advisor-responses/test_local.py
```
Optional tools/skills (repo-root `.env`): `TOOLBOX_NAME=benefits-advisor-tools`,
`SKILL_NAMES=cost-analysis-methodology,regulatory-guidance`. If unset, the agent still runs
(without tools/skills). Full container: `pip install -r requirements.txt && python main.py` (port 8088).

## Deploy
`azd ai agent init` (pick **ZIP upload**, **Python 3.14**, `main.py`) → `azd deploy`. See [../README.md](../README.md#deploy-to-foundry--step-by-step).

## Test after deployment

This is the **Responses** protocol: multi-turn, streaming, model-directed tools. Ask conversational questions; it computes/searches and replies with tables.

```bash
azd ai agent invoke benefits-advisor-responses "What's a competitive retirement match for a 500-employee tech firm in 2026, and how does it compare to market P50?"
```

More sample questions to try:

| # | Question | Exercises |
|---|----------|-----------|
| 1 | `Compare adding dental+vision vs a wellness stipend for 500 employees — show a cost table.` | code_interpreter + tables |
| 2 | `Project the annual cost of raising leave from 12 to 20 days for 250 staff at 60 CU/hr.` | calculation + assumptions |
| 3 | `What is a P50 benefits cost benchmark and how do I move from P25 to P50?` | skills knowledge |
| 4 | `Find current 2026 market trends for parental-leave top-ups and summarize.` | web_search (needs Toolbox) |

Call from Python (OpenAI-compatible Responses endpoint):
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
c = AIProjectClient(endpoint="<project-endpoint>", credential=DefaultAzureCredential(), allow_preview=True)
oai = c.get_openai_client(agent_name="benefits-advisor-responses")
print(oai.responses.create(input="Benchmark dental coverage cost for 300 staff.", model="gpt-4.1-mini").output_text)
```
Tool questions (#1, #4) need a Toolbox: redeploy with `TOOLBOX_NAME` set; without it the agent still answers from reasoning + skills.
