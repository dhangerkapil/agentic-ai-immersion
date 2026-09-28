# Foundry Agents Labs: Hosted Agents on Microsoft Foundry

One use case (the Benefits Marketplace Concierge, see `../USE-CASE.md`), one data set (`../data/`), one
sequence. The focus is **Hosted Agents**: Agent Framework code that Foundry builds into a container, versions,
scales and fronts with the Responses API. Prompt agents (platform-managed definitions) appear once, in Stretch 5,
where they belong: business-owned instructions and a governed workflow that the hosted agent can delegate to.

Audience: software engineers (Python, VS Code, Git). Format per breakout: teach 10, demo 10, do 35,
checkpoint 5. Four core labs build on each other's artifacts; two stretch labs for fast finishers and follow-up.

## Where things run

Two runtimes. Every lab says which one each step uses.

1. **Learner workstation: VS Code + the base repo dev container (or a local venv).** This is where the notebooks
   run. The Jupyter kernel is the Python inside the dev container on the laptop (Docker Desktop) or in GitHub
   Codespaces if your organization allows it. Notebooks authenticate with `az login` (Entra), call the Foundry project over
   HTTPS, build indexes, deploy hosted agents with `azd`, invoke endpoints and read results. Nothing
   customer-facing runs here.
2. **Microsoft Foundry (Azure).** Prompt agents, workflow agents, knowledge bases and evals run inside the
   Foundry project. **Hosted agents run as containers that Foundry builds from the ZIP `azd` uploads and scales
   on your behalf.** Their code is plain `.py` (`main.py` + `requirements.txt`, flat folder, no wrapper) and
   cannot be a notebook. Locally, the same `main.py` runs as a process on port 8088 for testing.

Rule of thumb: **notebook = the learner's cockpit** (build, deploy, call, inspect, break things);
**`hosted/main.py` = the product** (what ships). Each lab therefore has both: `labN_walkthrough.ipynb`
(generated from the `# %%` script with `../tools/py_to_ipynb.py`, same cells plus Markdown) and the `.py` files.

```
 workstation (notebook kernel, az login)                      Microsoft Foundry (Azure)
 +----------------------------------------------+            +-----------------------------------------------+
 | labN_walkthrough.ipynb / labN_*.py           |  HTTPS     | project: models, prompt agents, workflow      |
 |  build KB, start/kill local main.py, call    |----------->|   agents (S5), evals, tracing, connections    |
 |  8088, azd up, call deployed, evaluate       |            | hosted agents: containers built from the ZIP  |
 | hosted/main.py as a local process on :8088   |  azd up    |   azd uploads; versions; POST /responses      |
 +----------------------------------------------+----------->|   benefits-concierge-hosted (L1, L2), benefits-triage-  |
                                                             |   hosted (L3), benefits-claims-review-invocations  |
 state outside the container: Redis (BENEFITS_REDIS_URL) or files |   (S6)                                        |
 knowledge: Azure AI Search + Foundry IQ KB over MCP         +-----------------------------------------------+
```

## Agenda

| # | Folder | Type | Builds | Artifact |
|---|---|---|---|---|
| 1 | `lab1-hosted-agent-basics` | Hosted | Agent Framework `Agent` + `FoundryChatClient` + three `@tool` functions over benefits_data (`get_participant`, `get_enrollment_window`, `get_hra_account`) + `guardrails.COMPLIANCE_INSTRUCTIONS`, served by `ResponsesHostServer` as `benefits-concierge-hosted`. `prepare.py` vendors `common/` and `data/` into the flat `hosted/` folder; the driver starts `main.py` locally on 8088, chats S1 and S2 through `POST /responses`, prints the `azd ai agent init` + `azd up` commands, records the deployed version, calls it with `agent_reference`; `test_local.py` is the smoke test Lab 4 reuses | `artifacts/lab1/hosted.json`, `transcripts.md`, `hosted_local.log` |
| 2 | `lab2-hosted-knowledge-sessions` | Hosted + Foundry IQ | Notebook part: Foundry IQ knowledge base from `data/knowledge` (two indexes, knowledge sources, KB, project connection). Hosted part: `benefits-concierge-hosted` v2 adds `MCPStreamableHTTPTool` to the KB MCP endpoint (Entra bearer via httpx auth), `search_plans` / `compare_plans`, and **session storage for resiliency**: `common.message_store` (Redis when `BENEFITS_REDIS_URL`, file fallback) + `common.session_store`. Demo: two turns, kill the process, restart, third turn depends on memory; redeploy as a new version and sessions survive | `artifacts/lab2/knowledge.json`, `hosted.json`, `sessions/`, `transcripts.md` |
| 3 | `lab3-hosted-multi-agent-handoff` | Hosted, multi-agent | Inside the container: `WorkflowBuilder` graph intake (LOB classifier) -> `marketplace-guide` + `accounts-assistant` (explicit fan-out, counting fan-in) -> `compliance-reviewer` reflection (revise once, then flag) -> `advisor-handoff` Pydantic `HandoffPacket`. **Human approval across HTTP turns**: the packet returns with `status: pending_advisor_approval` and is stored in `common.session_store`; the advisor's next turn `approve` / `revise: ...` / `decline: ...` resumes the paused workflow (or finishes from the stored packet after a restart, `resume_path=session_store`). Agent middleware routes every turn deterministically. Run S1, S2, S3 locally (`--auto-approve`, interactive, `--restart-between-turns`), deploy `benefits-triage-hosted` | `artifacts/lab3/handoff_packets/S1..S3.json`, `hosted.json`, `sessions/` |
| 4 | `lab4-operate-hosted-agents` | Hosted, operations | OpenTelemetry from the container to Application Insights (`APPLICATIONINSIGHTS_CONNECTION_STRING` on the hosted agent), read a trace end to end; evaluation of the hosted endpoint over `golden_questions.jsonl` with `azure-ai-evaluation` (Groundedness, Relevance) + custom NoRecommendation and PiiLeak evaluators, optional Foundry eval; versions list / promote / roll back with azd; `eval_gate.py`, `promote.py`, `.github/workflows/agent-ci.yml` (validate -> eval gate -> deploy dev -> smoke -> manual promote -> rollback) | `artifacts/lab4/eval_report.md`, `gate_result.json`, `pipeline.md` |
| S5 | `stretch5-prompt-agents-and-workflows` | Prompt (platform-managed) | Condensed prompt-agent story: `benefits-concierge` with FunctionTools, four specialists (knowledge MCPTool), the YAML `benefits-triage-workflow` agent (preview); run S1 through it; then the **hosted** agent gets a `run_triage_workflow` tool that calls the workflow agent with `agent_reference`. Teach: platform-managed versus hosted | `artifacts/stretch5/agents.json`, `handoff_packets/S1.json` |
| S6 | `stretch6-invocations-toolbox-skills` | Hosted, second protocol | `benefits-claims-review-invocations` on `InvocationsHostServer`: `{"claim_ids": [...]}` in, one `ClaimReview` per claim out (facts from `claims_review.py` over benefits_data + KB-ACC-001, the model writes only `participant_explanation`). Plus the Responses concierge with a bundled Skill (`skills/hra-reimbursement-rules/SKILL.md`, index embedded at startup, `read_skill` on demand) and an optional Foundry Toolbox (`MCPStreamableHTTPTool`, preview). Two-protocol comparison; `--offline` runs without a model | `artifacts/stretch6/invocations.json`, `claim_reviews/CLM-*.json`, `skills_transcript.md` |

## What you'll learn

**Lab 1**
- Build an Agent Framework `Agent` on `FoundryChatClient` with three `@tool` functions over the systems of record and the shared compliance block.
- Serve that agent over the OpenAI Responses protocol with `ResponsesHostServer`, and explain what Foundry does with the folder when you run `azd up`.
- Call a hosted agent the way a web chat backend does: `POST /responses` locally, `responses.create(..., agent_reference)` for the deployed version.
- Explain the RBAC split (Foundry Project Manager to deploy, Foundry Agent Consumer or Foundry User to invoke) and read a version's status and logs in the portal.
- Ship a second version by changing one instruction and re-running `azd up`, and say why the old version stays.
- Diagnose the two startup failures learners hit most: a failed version (bad ZIP or pins) and `424 session_not_ready`.

**Lab 2**
- Build a Foundry IQ knowledge base from Markdown documentation and expose it over MCP with a project connection, Entra only.
- Attach it to an in-process Agent Framework agent with `MCPStreamableHTTPTool` and an httpx auth that injects the container's own token.
- Explain why a hosted container must be stateless and what state lives outside it (message history, the session map).
- Wire `common.message_store` and `common.session_store` into the agent so history is keyed by session id, not by process.
- Prove resiliency with a kill-and-restart demo and explain why the same mechanism makes version rolls and scale-out safe.
- Deploy a new version from source with `azd` and pass configuration through environment variables.

**Lab 3**
- Build an explicit `WorkflowBuilder` graph with custom executors: fan-out to two specialists, fan-in by counting, a compliance gate that sends a draft back once, and a coordinator that asks a human.
- Produce a strict JSON handoff packet with Pydantic `response_format` and carry compliance flags through it.
- Explain how `ctx.request_info` pauses a workflow and how to resume it with `workflow.run(responses={request_id: ...})`.
- Move human-in-the-loop from a terminal `input()` to HTTP turns: the packet comes back `pending_advisor_approval`, the decision arrives as the next `POST /responses`.
- Keep the paused case in `common.session_store` so a restarted container or another replica can still finish it.
- Route every Responses turn through agent middleware that short-circuits the model when the turn is a case or a decision.

**Lab 4**
- Turn on OpenTelemetry for a hosted agent with one container environment variable and read a trace end to end.
- Evaluate the hosted endpoint with `azure-ai-evaluation` local evaluators plus deterministic policy evaluators written as Python classes.
- Explain when a Foundry evaluation run fits and when local evaluators fit.
- Turn the evaluation into a release gate that fails a build on one violation.
- List, promote and roll back hosted agent versions, and explain why sessions survive both.
- Read a GitHub Actions pipeline that validates, gates, deploys from source, smoke-tests and rolls back with OIDC and no secrets.

**Stretch 5**
- Create versioned prompt agents with `PromptAgentDefinition`, FunctionTools from shared schemas and the knowledge base as an `MCPTool`.
- Run the client-side function-call loop once and explain why a platform workflow cannot run client tools.
- Deploy a declarative multi-agent workflow (YAML, preview) and read its `workflow_action` stream.
- Decide per agent when platform-managed fits and when hosted code fits.
- Connect the two with one `@tool` on the hosted agent.

**Stretch 6**
- Explain when a hosted agent should speak Invocations (one structured request, one structured response, stateless) instead of Responses (multi-turn, streaming, sessions).
- Build an Invocations agent whose facts are deterministic (a tool over the systems of record and KB-ACC-001) and whose model contribution is bounded (a plain-language explanation inside a Pydantic schema).
- Bundle a Skill as `skills/<name>/SKILL.md`, embed its index at startup and load the body on demand (progressive disclosure).
- Attach a Foundry Toolbox (web_search, code_interpreter) to a hosted agent over MCP, and state the rule for what may go to the web.
- Deploy two agents with two protocols from two flat folders using the same azd commands.

## Technical features by lab

- **Lab 1:** `FoundryChatClient(project_endpoint, model, credential=DefaultAzureCredential())`; `Agent(client, name, instructions, tools, default_options={"store": False})`; `@tool(approval_mode="never_require")` with `Annotated[str, Field(...)]`; `guardrails.COMPLIANCE_INSTRUCTIONS` asserted on the instructions; `ResponsesHostServer(agent).run()`; `prepare.py` vendoring into a flat deployable; `subprocess.Popen` + port probe for the local server; `httpx.post("/responses", {"input", "previous_response_id"})`; `azd ai agent init --protocol responses --deploy-mode code --runtime python_3_14 --dep-resolution remote_build` + `azd up`; `responses.create(..., extra_body=agent_reference)`; `test_local.py` guardrail smoke test.
- **Lab 2:** `SearchIndex` + `AzureOpenAIVectorizer` + `SemanticSearch`; `SearchIndexKnowledgeSource`, `KnowledgeBase`, `create_or_update_knowledge_base`; ARM project connection (ProjectManagedIdentity, RemoteTool); `MCPStreamableHTTPTool` with `httpx.Auth` Entra bearer; `@tool` over benefits_data; `Agent(context_providers=[history], default_options={"store": False})`; `common.message_store` (Redis / file) and `common.session_store`; `ResponsesHostServer` as a local subprocess; `azd env set` + `azd up` version roll.
- **Lab 3:** `WorkflowBuilder(start_executor).add_edge(...).build()`; `Executor` + `@handler` with `WorkflowContext[T]`; `ctx.send_message(..., target_id=)` fan-out and a counting merge; `AgentExecutor(agent, id=)` / `AgentExecutorRequest` / `AgentExecutorResponse`; `response_format=ReviewVerdict` / `HandoffPacket`; bounded reflection (`ComplianceGate`) + `guardrails.contains_recommendation`; `ctx.request_info` + `@response_handler` + `workflow.run(responses={...})`; agent middleware `triage_router(context, call_next)` setting `context.result`; `common.session_store` holding the pending packet (`resume_path` workflow / session_store); local `search_knowledge` or `MCPStreamableHTTPTool` to Lab 2's KB via `BENEFITS_KB_MCP_URL`.
- **Lab 4:** `APPLICATIONINSIGHTS_CONNECTION_STRING` + `configure_azure_monitor` + `configure_otel_providers` (VERIFY); OpenTelemetry spans around each golden question; `GroundednessEvaluator`, `RelevanceEvaluator` with Entra-only `AzureOpenAIModelConfiguration`; custom `NoRecommendationEvaluator`, `PiiLeakEvaluator`; hosted endpoint as target (local `POST /responses` or deployed `agent_reference`); optional `evals.create` / `evals.runs.create`; `eval_gate.py`; `promote.py`; GitHub Actions with OIDC, environments, rollback job; `pipeline.md` generated from the YAML.
- **Stretch 5:** `PromptAgentDefinition`, `project.agents.create_version`, `FunctionTool` from `benefits_data.TOOL_SCHEMAS`, `MCPTool(project_connection_id=...)`, `WorkflowAgentDefinition` (preview) with `InvokeAzureAgent` / `ConditionGroup`, streaming `workflow_action` items, `@tool run_triage_workflow` -> `responses.create(..., extra_body=agent_reference)` from the hosted agent.
- **Stretch 6:** `InvocationsHostServer(agent).run()` with `{"message": ...}` bodies (path VERIFY); deterministic `claims_review.review_claims` parsed from KB-ACC-001 exposed as `@tool`; `response_format=ClaimReviewBatch`; `skills/<name>/SKILL.md` frontmatter, `load_skills()` index in instructions + `read_skill` tool; `MCPStreamableHTTPTool(url=TOOLBOX_MCP_URL, http_client=httpx.AsyncClient(auth=EntraBearerAuth()))` with `_ping_available = False` (preview, VERIFY); `azd ai agent init --protocol invocations` and `--protocol responses` from two folders; `--offline` mode.

## Artifact chain

```
 lab1/hosted.json ----> lab2/knowledge.json + hosted.json + sessions/ ----> lab3/hosted.json + handoff_packets/
        |                        |            |                                     |
        |                        |            +------> lab4/eval_report.md, gate_result.json, pipeline.md (target: lab2 hosted)
        |                        |
        |                        +------> stretch5/agents.json (MCPTool uses the lab2 connection) --> hosted_tool_snippet.py
        |
        +------> stretch6/invocations.json (second protocol, same conventions)
 catch_up.py --through K recreates 1..K by calling each lab's build()
```

## Facilitator notes
- Run `python ../common/benefits_data.py`, `python ../common/session_store.py` and `python ../common/message_store.py` on the room image the day before: all three pass with no Azure packages installed.
- `BENEFITS_TODAY=2026-10-06` in `.env` makes every enrollment-window answer identical across laptops (see `../SETUP.md` section 9).
- The kill-and-restart demo in Lab 2 is the moment of the day. Rehearse it: server log shows `[hosted] history: file (...)` or `redis (...)`, two pids in the continuity line.
- Foundry Project Manager is needed for every `azd up`. If the room does not have it, one proctor deploys and everyone calls the deployed agent with `hosted/test_local.py --deployed`; the local `python main.py` path needs no deploy rights.
- RBAC propagation is the number one failure. Assign roles at least 30 minutes before the lab that needs them (SETUP.md section 5) and re-check the project managed identity and the hosted agent identity in the portal, not from memory.
- Redis: `docker run -d -p 6379:6379 redis:latest` on each laptop for the Lab 2 YOUR TURN; the base repo already uses this container for `threads/2`. Without Docker, the file store fallback carries the demo.
- Preview features are marked in every README and every `# VERIFY` comment: workflow YAML (S5), `agent_framework.observability`, hosted-agent session handling in `ResponsesHostServer`, hosted agents as Foundry eval targets. Verify them against the linked docs the week before.
- Remote attendees: bookmark the portal blades you will click (Agents > versions, Observability > Tracing, Azure AI Search > Knowledge bases, Management center > Connections).

## Prerequisites delta (beyond the base repo)
See `../SETUP.md`: Azure AI Search with Foundry IQ, `azd` + `azure.ai.agents` extension, Application Insights connected to the project, Redis (Docker locally; Azure Managed Redis for test/prod), the Foundry Project Manager role for deployers and Foundry Agent Consumer for invokers, `BENEFITS_KB_MCP_URL` and `BENEFITS_REDIS_URL`. Python packages: `requirements.txt` in this folder (workstation) and each `hosted/requirements.txt` (container).

## Structure
```
labs/
  README.md                 this file             lab_helpers.py    shared driver helpers
  catch_up.py               --through 1..6        requirements.txt  workstation packages
  artifacts/README.md       the chain             ../tools/py_to_ipynb.py  script -> notebook
  lab1-hosted-agent-basics/            lab1_hosted_basics.py, lab1_walkthrough.ipynb, hosted/{main,prepare,test_local}.py
  lab2-hosted-knowledge-sessions/      lab2_hosted_knowledge.py, knowledge_base.py, lab2_walkthrough.ipynb, hosted/
  lab3-hosted-multi-agent-handoff/     lab3_hosted_multi_agent.py, lab3_walkthrough.ipynb, hosted/{main,benefits_specialists,benefits_workflow}.py
  lab4-operate-hosted-agents/          lab4_operate.py, eval_gate.py, promote.py, lab4_walkthrough.ipynb, .github/workflows/agent-ci.yml, envs/, infra/
  stretch5-prompt-agents-and-workflows/ stretch5_prompt_agents.py, benefits_triage_workflow.yaml, hosted_tool_snippet.py, stretch5_walkthrough.ipynb
  stretch6-invocations-toolbox-skills/ stretch6_invocations.py, hosted-invocations/main.py, skills/
```
Every driver script runs top to bottom (`python labN_*.py`) and cell by cell (`# %%` in VS Code); the notebook next to it has the same cells. `python catch_up.py --through N` recreates the artifacts of labs 1..N.

## What was cut and why
The earlier plan had three parallel option tracks (platform-managed prompt agents, code-first Agent Framework, enterprise integration) and prompt-agent core labs. The customer narrowed the scope to Hosted Agents for software engineers, so:
- **Prompt-agent core labs** (concierge with FunctionTools, knowledge agent, YAML workflow as Labs 1 to 3) are condensed into Stretch 5, where the point is the platform-managed versus hosted decision and the hosted agent delegating to the workflow.
- **Foundry evals as a core lab and the standalone AgentOps stretch** are merged into Lab 4: evaluation of the hosted endpoint is the release gate of the pipeline.
- **Custom MCP server** (FastMCP over the systems of record), **Teams / M365 Copilot publishing**, **FastAPI web chat**, **A2A**, **Routines, Memory store and Model Router** are out. Each has a reference notebook in the base repo: `azure-ai-agents/11-routines.ipynb`, `12-agent-memory.ipynb`, `13-model-router.ipynb`, `14-agent-to-agent-a2a.ipynb`, `15-managed-mcp-connectors.ipynb`; the Teams publish path is a portal walkthrough; a FastAPI front for the Responses API is a 60-line file a web team can write against the same `agent_reference` shape used in `hosted/test_local.py --deployed`.
- The in-process Agent Framework middleware and human-in-the-loop `request_info` labs from the old code-first track live on inside Lab 3's hosted workflow, where the approval crosses HTTP turns because the client is a web chat, not a terminal.
