# Agent 2 summary blocks for Labs 1, 3 and Stretch 6

For the orchestrator: paste each block at the matching marker in `labs/README.md` (`<!-- LAB1-ROW -->`,
`<!-- LAB3-ROW -->`, `<!-- S6-ROW -->`, `<!-- LAB1-LEARN -->`, `<!-- LAB3-LEARN -->`, `<!-- S6-LEARN -->`,
`<!-- LAB1-FEATURES -->`, `<!-- LAB3-FEATURES -->`, `<!-- S6-FEATURES -->`) and add the SETUP rows to `SETUP.md`.
Formats match the existing rows in those files. Copy the row text exactly as written here.

## Agenda rows (table `| # | Folder | Type | Builds | Artifact |`)

<!-- LAB1-ROW -->
| 1 | `lab1-hosted-agent-basics` | Hosted | Agent Framework `Agent` + `FoundryChatClient` + three `@tool` functions over via_data (`get_participant`, `get_enrollment_window`, `get_hra_account`) + `guardrails.COMPLIANCE_INSTRUCTIONS`, served by `ResponsesHostServer` as `via-concierge-hosted`. `prepare.py` vendors `common/` and `data/` into the flat `hosted/` folder; the driver starts `main.py` locally on 8088, chats S1 and S2 through `POST /responses`, prints the `azd ai agent init` + `azd up` commands, records the deployed version, calls it with `agent_reference`; `test_local.py` is the smoke test Lab 4 reuses | `artifacts/lab1/hosted.json`, `transcripts.md`, `hosted_local.log` |

<!-- LAB3-ROW -->
| 3 | `lab3-hosted-multi-agent-handoff` | Hosted, multi-agent | Inside the container: `WorkflowBuilder` graph intake (LOB classifier) -> `marketplace-guide` + `accounts-assistant` (explicit fan-out, counting fan-in) -> `compliance-reviewer` reflection (revise once, then flag) -> `advisor-handoff` Pydantic `HandoffPacket`. **Human approval across HTTP turns**: the packet returns with `status: pending_advisor_approval` and is stored in `common.session_store`; the advisor's next turn `approve` / `revise: ...` / `decline: ...` resumes the paused workflow (or finishes from the stored packet after a restart, `resume_path=session_store`). Agent middleware routes every turn deterministically. Run S1, S2, S3 locally (`--auto-approve`, interactive, `--restart-between-turns`), deploy `via-triage-hosted` | `artifacts/lab3/handoff_packets/S1..S3.json`, `hosted.json`, `sessions/` |

<!-- S6-ROW -->
| S6 | `stretch6-invocations-toolbox-skills` | Hosted, second protocol | `via-claims-review-invocations` on `InvocationsHostServer`: `{"claim_ids": [...]}` in, one `ClaimReview` per claim out (facts from `claims_review.py` over via_data + KB-ACC-001, the model writes only `participant_explanation`). Plus the Responses concierge with a bundled Skill (`skills/hra-reimbursement-rules/SKILL.md`, index embedded at startup, `read_skill` on demand) and an optional Foundry Toolbox (`MCPStreamableHTTPTool`, preview). Two-protocol comparison; `--offline` runs without a model | `artifacts/stretch6/invocations.json`, `claim_reviews/CLM-*.json`, `skills_transcript.md` |

## What you'll learn

<!-- LAB1-LEARN -->
**Lab 1**
- Build an Agent Framework `Agent` on `FoundryChatClient` with three `@tool` functions over the systems of record and the shared compliance block.
- Serve that agent over the OpenAI Responses protocol with `ResponsesHostServer`, and explain what Foundry does with the folder when you run `azd up`.
- Call a hosted agent the way a web chat backend does: `POST /responses` locally, `responses.create(..., agent_reference)` for the deployed version.
- Explain the RBAC split (Foundry Project Manager to deploy, Foundry Agent Consumer or Foundry User to invoke) and read a version's status and logs in the portal.
- Ship a second version by changing one instruction and re-running `azd up`, and say why the old version stays.
- Diagnose the two startup failures learners hit most: a failed version (bad ZIP or pins) and `424 session_not_ready`.

<!-- LAB3-LEARN -->
**Lab 3**
- Build an explicit `WorkflowBuilder` graph with custom executors: fan-out to two specialists, fan-in by counting, a compliance gate that sends a draft back once, and a coordinator that asks a human.
- Produce a strict JSON handoff packet with Pydantic `response_format` and carry compliance flags through it.
- Explain how `ctx.request_info` pauses a workflow and how to resume it with `workflow.run(responses={request_id: ...})`.
- Move human-in-the-loop from a terminal `input()` to HTTP turns: the packet comes back `pending_advisor_approval`, the decision arrives as the next `POST /responses`.
- Keep the paused case in `common.session_store` so a restarted container or another replica can still finish it.
- Route every Responses turn through agent middleware that short-circuits the model when the turn is a case or a decision.

<!-- S6-LEARN -->
**Stretch 6**
- Explain when a hosted agent should speak Invocations (one structured request, one structured response, stateless) instead of Responses (multi-turn, streaming, sessions).
- Build an Invocations agent whose facts are deterministic (a tool over the systems of record and KB-ACC-001) and whose model contribution is bounded (a plain-language explanation inside a Pydantic schema).
- Bundle a Skill as `skills/<name>/SKILL.md`, embed its index at startup and load the body on demand (progressive disclosure).
- Attach a Foundry Toolbox (web_search, code_interpreter) to a hosted agent over MCP, and state the rule for what may go to the web.
- Deploy two agents with two protocols from two flat folders using the same azd commands.

## Technical features by lab (one line each)

<!-- LAB1-FEATURES -->
- **Lab 1:** `FoundryChatClient(project_endpoint, model, credential=DefaultAzureCredential())`; `Agent(client, name, instructions, tools, default_options={"store": False})`; `@tool(approval_mode="never_require")` with `Annotated[str, Field(...)]`; `guardrails.COMPLIANCE_INSTRUCTIONS` asserted on the instructions; `ResponsesHostServer(agent).run()`; `prepare.py` vendoring into a flat deployable; `subprocess.Popen` + port probe for the local server; `httpx.post("/responses", {"input", "previous_response_id"})`; `azd ai agent init --protocol responses --deploy-mode code --runtime python_3_14 --dep-resolution remote_build` + `azd up`; `responses.create(..., extra_body=agent_reference)`; `test_local.py` guardrail smoke test.
<!-- LAB3-FEATURES -->
- **Lab 3:** `WorkflowBuilder(start_executor).add_edge(...).build()`; `Executor` + `@handler` with `WorkflowContext[T]`; `ctx.send_message(..., target_id=)` fan-out and a counting merge; `AgentExecutor(agent, id=)` / `AgentExecutorRequest` / `AgentExecutorResponse`; `response_format=ReviewVerdict` / `HandoffPacket`; bounded reflection (`ComplianceGate`) + `guardrails.contains_recommendation`; `ctx.request_info` + `@response_handler` + `workflow.run(responses={...})`; agent middleware `triage_router(context, call_next)` setting `context.result`; `common.session_store` holding the pending packet (`resume_path` workflow / session_store); local `search_knowledge` or `MCPStreamableHTTPTool` to Lab 2's KB via `VIA_KB_MCP_URL`.
<!-- S6-FEATURES -->
- **Stretch 6:** `InvocationsHostServer(agent).run()` with `{"message": ...}` bodies (path VERIFY); deterministic `claims_review.review_claims` parsed from KB-ACC-001 exposed as `@tool`; `response_format=ClaimReviewBatch`; `skills/<name>/SKILL.md` frontmatter, `load_skills()` index in instructions + `read_skill` tool; `MCPStreamableHTTPTool(url=TOOLBOX_MCP_URL, http_client=httpx.AsyncClient(auth=EntraBearerAuth()))` with `_ping_available = False` (preview, VERIFY); `azd ai agent init --protocol invocations` and `--protocol responses` from two folders; `--offline` mode.

## SETUP.md additions

### Section 2, environment variables (table `| Variable | Used by | Example shape (no real values here) | Notes |`)

| `VIA_SESSION_DIR` | Lab 3 hosted agent (local) | `labs/artifacts/lab3/sessions` | File fallback for the session map when `VIA_REDIS_URL` is unset; the Lab 3 driver sets it so pending packets are visible next to the artifacts |
| `VIA_INVOCATIONS_PATH` | Stretch 6 client | `/invocations` | Path the local `InvocationsHostServer` serves (VERIFY); `test_local.py` also tries `/invoke` and `/` |
| `SKILL_NAMES` | Stretch 6 skills agent | `hra-reimbursement-rules` | Comma list of `skills/<name>/SKILL.md` to embed; unset embeds every skill in the folder |
| `TOOLBOX_NAME`, `TOOLBOX_MCP_URL` | Stretch 6 skills agent (preview) | `agent-tools`, `https://.../mcp` | Foundry Toolbox with web_search + code_interpreter over MCP; unset disables the toolbox, the agent still runs |
| `VIA_AGENT_NAME` | Stretch 6 skills agent | `via-concierge-hosted` | Override the agent name when you do not want the skills build to become a new version of the concierge |

### Section 4, Azure resources (table `| Resource | Needed by | Setup |`)

| Foundry Toolbox (preview) | Stretch 6 skills agent, optional | Create a Toolbox with `web_search` and `code_interpreter` in the project (base repo `AgentOps/src/tools/toolbox_config.py` pattern), set `TOOLBOX_NAME` and `TOOLBOX_MCP_URL` on the hosted agent. Region-limited; skip if unavailable |

### Section 5, RBAC (table `| Principal | Scope | Role | Why |`)

| Hosted agent managed identity (`via-concierge-hosted`, skills version) | Foundry project / Toolbox | Access to the Toolbox MCP endpoint (VERIFY the exact role) | `MCPStreamableHTTPTool` calls to web_search / code_interpreter (Stretch 6, preview) |

### Section 7, five-minute verification (append after the `common/` self-tests)

```bash
# 2. Hosted folders build without Azure. Expect "wrote artifacts/lab1/hosted.json", "...lab3/hosted.json", 3 claim packets.
python labs/lab1-hosted-agent-basics/lab1_hosted_basics.py --skip-demo
python labs/lab3-hosted-multi-agent-handoff/lab3_hosted_multi_agent.py --skip-demo --standalone
python labs/stretch6-invocations-toolbox-skills/stretch6_invocations.py --offline
python labs/stretch6-invocations-toolbox-skills/hosted-invocations/test_local.py --offline
```

### Agent names used by these labs

| Agent | Lab | Protocol | Folder |
|---|---|---|---|
| `via-concierge-hosted` | 1 (v1), 2 (v2, Agent 1), S6 skills build (optional new version) | responses | `lab1-hosted-agent-basics/hosted/`, `stretch6-.../hosted-responses-skills/` |
| `via-triage-hosted` | 3 | responses | `lab3-hosted-multi-agent-handoff/hosted/` |
| `via-claims-review-invocations` | S6 | invocations | `stretch6-.../hosted-invocations/` |
