# SETUP: environment for the WTW Foundry Agents Labs (Hosted Agents)

This folder drops into the base repo `github.com/dhangerkapil/agentic-ai-immersion` (fork
`hoopdad/agentic-ai-immersion`) and reuses its dev container, `.env` variable names, RBAC script and pinned
requirements. Do the base repo's prerequisites first (its `PREREQUISITES` datasheet and `.env.example`), then
the items below. Everything authenticates with Entra ID through `az login`. There are no API keys anywhere in
these labs and none should be added to `.env`.

## 1. Where things live

```
agentic-ai-immersion/                  base repo (dev container, .env, requirements lock, RBAC script)
  .env                                 shared variables, read by common/foundry_env.load_env()
  wtw-foundry-hosted-agents-labs/             this folder
    common/                            via_data, foundry_env, guardrails, session_store, message_store
    data/                              synthetic systems of record and knowledge base
    tools/py_to_ipynb.py               script -> notebook converter (stdlib only)
    labs/                              the sequence: lab1..lab4, stretch5, stretch6, catch_up.py, artifacts/
      labN-*/labN_*.py + labN_walkthrough.ipynb    workstation side (the cockpit)
      labN-*/hosted/main.py + requirements.txt     container side (the product; azd ships this folder)
```

`load_env()` reads, in order and without overriding anything already exported: the base repo root `.env`,
then `wtw-foundry-hosted-agents-labs/.env`, then `./.env`. Keep one `.env` at the base repo root; the others are for
per-environment overrides (Lab 4 `envs/*.example`).

## 1a. Where things run

Two runtimes; every lab README has a "Where this runs" line.

| Runtime | What runs there | Auth | Notes |
|---|---|---|---|
| Learner workstation: VS Code + the base repo dev container (Docker Desktop) or GitHub Codespaces | the `labN_walkthrough.ipynb` notebooks and `labN_*.py` driver scripts: build indexes, start and kill `hosted/main.py` as a local process on port 8088, deploy with `azd`, call endpoints, evaluate, read results | `az login` (Entra), `AzureCliCredential` / `DefaultAzureCredential` | The Jupyter kernel is the dev container's Python. Nothing customer-facing runs here |
| Microsoft Foundry (Azure) | prompt agents, workflow agents, knowledge bases and evals inside the project; **hosted agents as containers Foundry builds from the ZIP `azd` uploads** (`main.py` + `requirements.txt` + vendored `common/` and `data/`, flat folder) | the hosted agent's managed identity (`DefaultAzureCredential` in the container) | Hosted code is plain `.py`, never a notebook. The same `main.py` runs locally for testing |

State that must survive a container restart (conversation history, the session map) lives in Redis
(`VIA_REDIS_URL`) or, on one laptop, in files under `labs/artifacts/labN/`; never inside the container.

## 2. Environment variables

| Variable | Used by | Example shape (no real values here) | Notes |
|---|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | all | `https://<account>.services.ai.azure.com/api/projects/<project>` | Foundry portal, project Overview page. Required by every lab |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | all | `gpt-5.4-mini` | Chat model deployment name. Default `gpt-5.4-mini` |
| `FOUNDRY_MODEL` | hosted agents | `gpt-5.4-mini` | Agent Framework model name; defaults to `AZURE_AI_MODEL_DEPLOYMENT_NAME` |
| `EMBEDDING_MODEL_DEPLOYMENT_NAME` | Lab 2 | `text-embedding-3-large` | 3072 dimensions; the index schema assumes this model |
| `AZURE_AI_SEARCH_ENDPOINT` | Lab 2 | `https://<search>.search.windows.net` | Basic tier or above, semantic ranker enabled |
| `AZURE_OPENAI_ENDPOINT` | Lab 2, Lab 4 judges | `https://<account>.openai.azure.com/` | Only the resource host is used; `/openai/...` suffixes are stripped |
| `PROJECT_RESOURCE_ID` | Lab 2 (project connection PUT), every `azd ai agent init` | `/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>` | ARM id of the project |
| `TENANT_ID` | all | `<guid>` | Passed to `AzureCliCredential(tenant_id=...)` and `az login --tenant` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Lab 4, hosted agents | `InstrumentationKey=...;IngestionEndpoint=...` | Optional on the workstation (Lab 4 fetches it from the project when blank). On the hosted agent it is set with `azd env set` and turns the container's tracing on |
| `VIA_TODAY` | all | `2026-10-06` | Workshop "today" for enrollment-window answers. See section 9 |
| `VIA_KB_MCP_URL` | Lab 2 hosted agent, Lab 4, CI | `https://<search>.search.windows.net/knowledgebases/via-benefits-kb/mcp?api-version=2025-11-01-Preview` | The knowledge base MCP endpoint. Written to `artifacts/lab2/knowledge.json` by Lab 2; the lab passes it to the local `main.py`; `azd env set VIA_KB_MCP_URL ...` for the container |
| `VIA_REDIS_URL` | Lab 2 hosted agent (message store + session map), Lab 3, S6 | `redis://localhost:6379/0` locally; `rediss://<name>.<region>.redis.azure.net:10000/0` for Azure Managed Redis | Optional. Unset means the file store under `labs/artifacts/labN/` (one laptop). Set means every replica shares history |
| `VIA_SESSION_TTL_SECONDS` | Redis stores | `604800` | Idle session expiry, default 7 days |
| `VIA_HOSTED_PORT` | local `main.py` | `8088` | Only for running two local replicas in the Lab 2 YOUR TURN |
| `VIA_WORKFLOW_AGENT_NAME` | Stretch 5 hosted tool | `via-triage-workflow` | Lets the hosted agent find the workflow agent without the artifacts file |
| `VIA_SESSION_DIR` | Lab 3 hosted agent (local) | `labs/artifacts/lab3/sessions` | File fallback for the session map when `VIA_REDIS_URL` is unset; the Lab 3 driver sets it so pending packets are visible next to the artifacts |
| `VIA_INVOCATIONS_PATH` | Stretch 6 client | `/invocations` | Path the local `InvocationsHostServer` serves (VERIFY); `test_local.py` also tries `/invoke` and `/` |
| `SKILL_NAMES` | Stretch 6 skills agent | `hra-reimbursement-rules` | Comma list of `skills/<name>/SKILL.md` to embed; unset embeds every skill in the folder |
| `TOOLBOX_NAME`, `TOOLBOX_MCP_URL` | Stretch 6 skills agent (preview) | `agent-tools`, `https://.../mcp` | Foundry Toolbox with web_search + code_interpreter over MCP; unset disables the toolbox, the agent still runs |
| `VIA_AGENT_NAME` | Stretch 6 skills agent | `via-concierge-hosted` | Override the agent name when you do not want the skills build to become a new version of the concierge |

`VIA_*` variables hold no secrets. Every lab README lists the ones it reads.

## 3. Model deployments

Deploy in the Foundry project, in a region that offers Agent Service, Foundry IQ and evaluations (the base
repo datasheet lists tested regions):

| Deployment | Purpose | Notes |
|---|---|---|
| `gpt-5.4-mini` (or the name you put in `AZURE_AI_MODEL_DEPLOYMENT_NAME`) | every agent, the evaluators' grader model, the label_model criteria | Global Standard, 100K+ TPM for a room of 20. Raise quota before the day |
| `text-embedding-3-large` | knowledge indexes (Lab 2) | 3072 dimensions |
| (no other deployments) | | The hosted agents and the evaluation judges share `gpt-5.4-mini` |

## 4. Azure resources and connections

| Resource | Needed by | Setup |
|---|---|---|
| Foundry account + project | all | Create the project first; copy `FOUNDRY_PROJECT_ENDPOINT` and `PROJECT_RESOURCE_ID` |
| azd + `azure.ai.agents` extension | Labs 1 to 4, S6 (every hosted deploy) | `azd config set auth.useAzCliAuth true`, `azd extension install azure.ai.agents`. Deployer needs Foundry Project Manager on the project |
| Azure AI Search with Foundry IQ | Lab 2 (and every later lab through `VIA_KB_MCP_URL`) | Enable system-assigned managed identity on the search service. Semantic ranker: free or standard |
| Project connection to the Foundry IQ knowledge base | Lab 2 | Created by the lab code with an ARM PUT on `{PROJECT_RESOURCE_ID}/connections/via-benefits-kb-connection` (authType ProjectManagedIdentity, category RemoteTool). Needs a role that can write connections (Azure AI Owner or Contributor on the account) |
| Redis | Lab 2 YOUR TURN (scale-out), Lab 3, S6; test/prod environments | Locally `docker run -d -p 6379:6379 redis:latest` and `VIA_REDIS_URL=redis://localhost:6379/0`. Azure: Azure Managed Redis with Entra auth (`rediss://`). Optional: the file store carries the demo without it |
| Application Insights | Lab 4 and the hosted agents' tracing | Connect it to the project (Foundry portal: project, Tracing, connect) so `telemetry.get_application_insights_connection_string()` works; set the connection string on the hosted agent with `azd env set` |
| GitHub repository with Environments `dev`, `test`, `prod` and an Entra app with OIDC federated credentials | Lab 4 pipeline (optional on the day) | See `labs/lab4-operate-hosted-agents/infra/README.md` |
| Foundry Toolbox (preview) | Stretch 6 skills agent, optional | Create a Toolbox with `web_search` and `code_interpreter` in the project (base repo `AgentOps/src/tools/toolbox_config.py` pattern), set `TOOLBOX_NAME` and `TOOLBOX_MCP_URL` on the hosted agent. Region-limited; skip if unavailable |

## 5. RBAC

Run the base repo RBAC script first, then confirm these. Propagation takes 5 to 15 minutes; the most common
"it does not work" on the day is a role that was assigned 3 minutes ago.

| Principal | Scope | Role | Why |
|---|---|---|---|
| Attendee (user) | Foundry account or project | Azure AI User (minimum) or Azure AI Developer | Create agents, conversations, evals |
| Attendee | Foundry project | Azure AI Owner or Contributor (Lab 2 only) | ARM PUT of the project connection |
| Attendee (deployer) | Foundry project | Foundry Project Manager | `azd ai agent init` / `azd up` of a hosted agent (every lab); one proctor can deploy for the room |
| Attendee | Azure AI Search service | Search Service Contributor + Search Index Data Contributor | Create indexes, knowledge sources, knowledge base; upload documents |
| Attendee | Application Insights | Monitoring Reader (or Reader) | Read traces in the portal |
| Project managed identity | Azure AI Search service | Search Index Data Reader | Agent calls the knowledge base MCP endpoint through the connection |
| Search service managed identity | Foundry account | Cognitive Services OpenAI User AND Cognitive Services User | Vectorizer and knowledge base answer synthesis call the models |
| Invokers of a hosted agent | Foundry project | Foundry Agent Consumer or Foundry User | Call the deployed Responses endpoint (`hosted/test_local.py --deployed`) |
| Hosted agent managed identity | Foundry project | Azure AI User | `FoundryChatClient` model calls from the container |
| Hosted agent managed identity | Azure AI Search service | Search Index Data Reader | `MCPStreamableHTTPTool` to the knowledge base (Lab 2 onwards) |
| Hosted agent managed identity | Azure Managed Redis (test/prod) | Redis data access policy (Entra) | message store and session map |
| Attendee | Azure OpenAI / Foundry account | Cognitive Services OpenAI User | Lab 4 judges (`azure-ai-evaluation`) and Lab 2 embeddings |
| Hosted agent managed identity (`via-concierge-hosted`, skills version) | Foundry project / Toolbox | Access to the Toolbox MCP endpoint (VERIFY the exact role) | `MCPStreamableHTTPTool` calls to web_search / code_interpreter (Stretch 6, preview) |

## 6. Python packages

Python 3.12 or newer (the dev container ships 3.14). Every workstation package these labs need —
`agent-framework`, `agent-framework-foundry`, `agent-framework-foundry-hosting`, `agent-framework-redis`,
`azure-ai-projects`, `openai`, `azure-identity`, `azure-search-documents`, `redis`, `azure-cosmos`,
`azure-ai-evaluation`, `azure-monitor-opentelemetry`, `opentelemetry-api`, `PyYAML`, `mcp`, `ruff`, `jupyter`,
`python-dotenv`, `pydantic`, `requests`, `httpx` — is already pinned in the base repo root
`requirements.txt`. Install from the repo root (the dev container's `postCreateCommand` already does this):

```bash
pip install -r requirements.txt
```

| Where | File | Contents |
|---|---|---|
| Workstation (notebooks, driver scripts, running `main.py` locally) | base repo root `requirements.txt` (`labs/requirements.txt` is a pointer to it, not a second lock) | see the package list above |
| Container (each hosted agent) | `labs/labN-*/hosted/requirements.txt` | minimal explicit pins: `agent-framework`, `agent-framework-foundry`, `agent-framework-foundry-hosting`, `azure-ai-projects`, `azure-identity`, `python-dotenv`, plus `httpx`, `redis`, `azure-monitor-opentelemetry` where used. Never `agent-framework[foundry]`. These ship inside the container and are pinned separately from the workstation lock; mirror the exact root versions here before the workshop (each file says so) |
| Tools | `azd` + `azure.ai.agents` extension (`azd extension install azure.ai.agents`, same as `hosted-agents/README.md`), Docker Desktop (dev container and local Redis) | |

`common/via_data.py`, `common/guardrails.py`, `common/session_store.py` and `common/message_store.py` need
nothing beyond the standard library for their self-tests, which is how they run on a laptop with no Azure packages.
Notebooks are generated from the scripts with `python tools/py_to_ipynb.py <script.py>`; nbformat is not required.

## 7. Five-minute verification

Run from the base repo root inside the dev container, after `az login --tenant $TENANT_ID`.

```bash
cd wtw-foundry-hosted-agents-labs

# 1. Data and helpers, no Azure needed. Expect "ALL CHECKS PASSED" and two "PASS" lines.
python common/via_data.py
python common/session_store.py
python common/message_store.py

# 2. Environment variables resolved (blank values are printed as "(blank)").
python common/foundry_env.py

# 3. Foundry project reachable with your identity (lists model deployments and agents).
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from common import foundry_env
project = foundry_env.get_project_client()
print("deployments:", [d.name for d in project.deployments.list()])
openai_client = foundry_env.get_openai_client(project)
r = openai_client.responses.create(model=foundry_env.model_name(), input="Reply with the single word ready.")
print("model says:", r.output_text)
EOF

# 4. Search endpoint reachable (Lab 2 only).
python - <<'EOF'
import sys; sys.path.insert(0, ".")
from common import foundry_env
from azure.search.documents.indexes import SearchIndexClient
env = foundry_env.load_env()
client = SearchIndexClient(env["AZURE_AI_SEARCH_ENDPOINT"], foundry_env.get_credential())
print("indexes:", [i for i in client.list_index_names()])
EOF
```

```bash
# 5. Hosted agent toolchain (Labs 1 to 4).
azd version && azd extension list | grep azure.ai.agents
python -c "import agent_framework, agent_framework_foundry_hosting; print('agent framework ok')"
```

Expected: step 1 ends with `ALL CHECKS PASSED` and `PASS`; step 3 prints your deployment names and `model says: ready`
(or a close variant); step 4 prints a list, possibly empty. A 401 or 403 in step 3 or 4 is RBAC or the wrong
tenant; see the troubleshooting table in every lab README.


Hosted folders build without Azure. Expect "wrote artifacts/lab1/hosted.json", "...lab3/hosted.json", and three claim packets:

```bash
python labs/lab1-hosted-agent-basics/lab1_hosted_basics.py --skip-demo
python labs/lab3-hosted-multi-agent-handoff/lab3_hosted_multi_agent.py --skip-demo --standalone
python labs/stretch6-invocations-toolbox-skills/stretch6_invocations.py --offline
python labs/stretch6-invocations-toolbox-skills/hosted-invocations/test_local.py --offline
```

### Agent names used by these labs

| Agent | Lab | Protocol | Folder |
|---|---|---|---|
| `via-concierge-hosted` | 1 (v1), 2 (v2), S6 skills build (optional new version) | responses | `lab1-hosted-agent-basics/hosted/`, `lab2-hosted-knowledge-sessions/hosted/`, `stretch6-.../hosted-responses-skills/` |
| `via-triage-hosted` | 3 | responses | `lab3-hosted-multi-agent-handoff/hosted/` |
| `via-claims-review-invocations` | S6 | invocations | `stretch6-.../hosted-invocations/` |

## 8. Proctor smoke test, the day before

Do this on the exact room account and network you will use. Tick every line.

- [ ] `az login --tenant <TENANT_ID>` works on the room laptops and in the dev container; no MFA prompt loops.
- [ ] `.env` at the base repo root has every variable in section 2 filled, `VIA_TODAY` included.
- [ ] Model quota: `gpt-5.4-mini` at 100K+ TPM, `text-embedding-3-large` deployed. Run the section 7 snippet.
- [ ] RBAC table (section 5) applied at least 30 minutes ago; project managed identity and search identity
      roles verified in the portal, not assumed.
- [ ] Application Insights connected to the project; a test trace shows up in the portal.
- [ ] `cd labs && python catch_up.py --through 2`, then `python lab2-hosted-knowledge-sessions/lab2_hosted_knowledge.py --demo-only`:
      `continuity check: OK` with two pids and a [KB-MKT-001] citation in turn 2.
- [ ] One proctor has deployed `via-concierge-hosted` with `azd up` on the room project and
      `python labs/lab2-hosted-knowledge-sessions/hosted/test_local.py --deployed` prints `PASS`; the version shows
      `active` in the portal. Note how long the first build took.
- [ ] `azd` login and the `azure.ai.agents` extension install on the room network without a proxy error.
- [ ] Docker Desktop runs the dev container and `redis:latest` on the room laptops (Lab 2 YOUR TURN).
- [ ] `python labs/lab4-operate-hosted-agents/lab4_operate.py --limit 3 --skip-judges` passes and a
      `via.golden_question` span shows up in Application Insights.
- [ ] Remote attendees: the recording and screen share show the terminal font at a readable size; the
      Foundry portal tabs you will click through are bookmarked.
- [ ] `data/` is untouched (`git status` clean) so every table shows the same numbers on every laptop.
- [ ] A throwaway `via-concierge-unsafe` agent (the "break the guardrail on purpose" YOUR TURN) has been
      created and deleted once, so you know how the model behaves without the compliance block.

## 9. VIA_TODAY

Enrollment windows depend on the date. The labs read `VIA_TODAY` (ISO date) through `common/via_data.py` so
every attendee gets the same answer regardless of the real date. The default `2026-10-06` is nine days before
the Annual Enrollment Period opens, which makes the S1 answer "AEP opens October 15" with an SEP reminder.

| `VIA_TODAY` | S1 Evelyn (Medicare, MA) | S3 Rosa (pre-Medicare) |
|---|---|---|
| `2026-10-06` (default) | SEP-possible, next window AEP 2026-10-15 to 2026-12-07 | SEP-possible, next window ACA OEP 2026-11-01 |
| `2026-10-20` | AEP | SEP-possible |
| `2026-11-15` | AEP | OEP (ACA open enrollment) |
| `2027-02-10` | OEP (MA open enrollment) | SEP-possible |
| `2027-09-01` | SEP-possible | IEP (turns 65 on 2027-11-20) |

Set it in `.env` or inline: `VIA_TODAY=2026-10-20 python labs/lab2-hosted-knowledge-sessions/lab2_hosted_knowledge.py --demo-only`.
The hosted `main.py` reads it too (`azd env set VIA_TODAY ...` for the container). Tests and demos that need a
fixed answer pass `today="..."` to `get_enrollment_window` directly.
