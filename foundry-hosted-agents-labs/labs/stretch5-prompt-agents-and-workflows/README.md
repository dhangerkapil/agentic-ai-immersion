# Stretch 5: Prompt agents and a declarative workflow, called from the hosted agent

| | |
|---|---|
| Goal | Build the platform-managed side of the story: `benefits-concierge` and four specialist prompt agents with FunctionTools and the knowledge MCP tool, the YAML triage workflow agent (preview), run S1 through it, then give the hosted agent a `run_triage_workflow` tool that delegates to it. |
| Time | 60 min: teach 10, demo 10, do 35, checkpoint 5 (stretch: fast finishers or follow-up) |
| Starts from | artifacts/lab2/knowledge.json (or `python catch_up.py --through 2`) |
| Produces | artifacts/stretch5/agents.json, artifacts/stretch5/workflow.yaml, artifacts/stretch5/handoff_packets/S1.json |
| Learn path modules | 1 Develop AI agents with Microsoft Foundry and Visual Studio Code; 2 Integrate custom tools into your agent; 6 Build agent-driven workflows using Microsoft Foundry |

**Where this runs:** workstation notebook (`stretch5_walkthrough.ipynb` / `stretch5_prompt_agents.py`) creates and calls agents that run inside the Foundry project. No container here. `hosted_tool_snippet.py` is code for the Lab 2 container.

## What you'll learn
- Create versioned prompt agents server-side with `PromptAgentDefinition`, `FunctionTool` schemas from `benefits_data.TOOL_SCHEMAS`, and the knowledge base as an `MCPTool` through the project connection.
- Run the client-side function-call loop once and explain why a workflow cannot run client tools (facts are pre-fetched into the case).
- Deploy a declarative multi-agent workflow (`WorkflowAgentDefinition`, YAML, preview) and read its `workflow_action` stream.
- Decide, per agent, when a platform-managed prompt agent fits (business-owned instructions, portal governance, no deployment) and when hosted code fits (custom Python, session state, your own dependencies).
- Connect the two: one `@tool` on the hosted agent that calls the workflow agent with `agent_reference`.

## Technical features taught

| Feature | Foundry / SDK object | Where in the code | Why it matters for Benefits Marketplace |
|---|---|---|---|
| Versioned prompt agents | `project.agents.create_version`, `PromptAgentDefinition(model, instructions, tools)` | `stretch5_prompt_agents.py` build() | Instruction changes are versions: auditable, revertible in the portal, no container roll |
| Function tools from shared schemas | `FunctionTool(name, description, parameters, strict)` via `lab_helpers.function_tools` | `SPECS`, build() | One schema source for platform agents and the hosted @tool functions |
| Knowledge over MCP on a platform agent | `MCPTool(server_label, server_url, require_approval="never", project_connection_id)` | knowledge_tool() | Same governed knowledge base as the hosted agent, reached through the project connection |
| Client-side function-call loop | `responses.create` + `FunctionCallOutput` (in `lab_helpers.run_turn`) | demo(--concierge-turn) | Shows who runs the Python: the client, not the platform |
| Declarative workflow agent (preview) | `WorkflowAgentDefinition(workflow=yaml)`, `InvokeAzureAgent`, `ConditionGroup` | `benefits_triage_workflow.yaml`, render_workflow(), build() | Triage -> specialists -> compliance -> packet as a governed graph the portal draws |
| Streaming workflow actions | `responses.create(stream=True)` -> `workflow_action` items | run_case() | The action trail is the audit log of who touched the case |
| Hosted agent delegating to the platform | `@tool run_triage_workflow` -> `responses.create(..., extra_body=agent_reference)` | `hosted_tool_snippet.py` | Code agent owns the conversation; platform workflow owns the regulated hand-off |

## Teach (10 min)
- Two kinds of agents in one project. A **prompt agent** is data: model, instructions, tools; Foundry runs it, versions it, shows it in the portal. A **hosted agent** is code: your container, your dependencies, your session store. Both are invoked the same way (`agent_reference`), both are eval targets, both show traces.
- When a prompt agent fits: the behaviour is owned by the business (compliance reviewer wording, handoff packet fields), changes must be auditable without a deployment, and the tools are server-side (knowledge base over MCP) or simple. When hosted fits: custom Python around the model (session store, redaction middleware, in-process workflows), libraries the platform does not ship, or protocols like Invocations (Stretch 6).
- Workflows on the platform cannot answer a client-side `function_call`: nobody is there to run your Python. So the caller pre-fetches the facts from systems of record into a `TRIAGE CASE` header and the specialists work from that plus the knowledge base. The hosted agent is the natural caller: it already has the tools and the session.
- The YAML: `OnConversationStart`, `InvokeAzureAgent` per step, `ConditionGroup` on the triage route, `EndConversation`. Every `InvokeAzureAgent` names an agent that already exists; the workflow is one more versioned agent.
- Governance argument: compliance-reviewer and advisor-handoff instructions are regulated text. Keep them where compliance can read and change them (portal), not in a container image.
- Preview means: keep the YAML small, verify the Power Fx helpers against the docs before the day.

```
 hosted container (Lab 2)                          Foundry project (platform-managed, this stretch)
 +-------------------------------+   agent_ref   +----------------------------------------------------+
 | benefits-concierge-hosted          |-------------->| benefits-triage-workflow (WorkflowAgentDefinition)      |
 |  @tool run_triage_workflow    |  responses    |  triage -> [marketplace-guide] [accounts-assistant] |
 |  session store, message store |  .create      |         -> compliance-reviewer -> advisor-handoff  |
 +-------------------------------+               |  each a PromptAgentDefinition version               |
                                                 |  marketplace/accounts: MCPTool benefits-kb (Lab 2 KB)    |
 workstation notebook: build(), S1 run, portal   +----------------------------------------------------+
```

## Demo (10 min)
1. `python stretch5_prompt_agents.py --concierge-turn`. Point at six `created prompt agent ... vN` lines and `created workflow agent benefits-triage-workflow`.
2. The concierge turn: `tool get_participant(...)`, `tool get_enrollment_window(...)` printed by the client loop, then the answer. Say: "the platform asked us to run Python; a workflow cannot do that."
3. S1: `workflow_action` lines in order (triage, marketplace, compliance, handoff), messages, `saved artifacts/stretch5/handoff_packets/S1.json (lob=marketplace, flags=0)`.
4. Portal: Agents > benefits-triage-workflow shows the graph; open the conversation to see the actions. Agents > compliance-reviewer > edit instructions in the portal: a new version, no deployment.
5. Open `hosted_tool_snippet.py`: one function, one Responses call, `agent_reference`. That is the whole integration.

## Do (35 min)
1. `python stretch5_prompt_agents.py --build-only`. Checkpoint: `saved artifacts/stretch5/agents.json` with six agents and the workflow version.
2. `python stretch5_prompt_agents.py --demo-only --concierge-turn`. Checkpoint: the concierge answer names the AEP dates and `no_recommendation=OK`; S1 produces `handoff_packets/S1.json` with `lob=marketplace` and `problems=none`.
3. Open `S1.json`: check `options_discussed` has no preference, `facts_gathered` sources are tool names or KB ids, `recommended_next_step_for_advisor` is a process step.
4. YOUR TURN (5 min): change an instruction in the portal (benefits-concierge: "Always greet the participant by first name"), rerun step 2. Checkpoint: the greeting changed and `agents.json` still points at the workflow; agent_reference by name resolved to your new version.
5. YOUR TURN (5 min): break the router (solution in the script): force `ROUTE: accounts`, rerun S1, read `open_questions` in the packet. Restore with `build()`.
6. YOUR TURN (10 min): wire the hosted agent. Paste the block from `hosted_tool_snippet.py` into Lab 2 `hosted/main.py`, add the instruction line, set `BENEFITS_WORKFLOW_AGENT_NAME=benefits-triage-workflow` in the server env and restart `main.py`. Ask as P-1005 "Which ACA plan should I pick?" then accept the advisor. Checkpoint: the server log shows the tool call and the reply summarises a packet without internal fields.
7. Optional (5 min): `python hosted_tool_snippet.py --call` runs the tool from the workstation against the workflow, no container needed.

## Checkpoint (5 min)
Paste the `workflow_action` trail for S1 and the `lob=` line. `artifacts/stretch5/agents.json` must exist for the hosted tool to find the workflow name.

## If you're behind
`python catch_up.py --through 5` builds the agents and the workflow (no S1 run). Skip steps 5 and 7; do step 6.

## Stretch (only if you're done early)
Add a revise loop to the YAML: a `ConditionGroup` after `compliance` that, when the review says `verdict: revise`, replaces the drafts with `revised_reply` before `handoff`. Rebuild, rerun S1 with a specialist instruction that violates rule 1 on purpose.

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `create_version` 401/403 | user lacks Azure AI User on the project, or wrong tenant | role assignment (5 to 15 min); `az login --tenant $TENANT_ID` |
| `knowledge.json has no mcp_endpoint or connection` | Lab 2 ran with `--skip-connection` | rerun Lab 2 without it, or `python catch_up.py --through 2` |
| Workflow create fails on YAML | Power Fx helper or field name changed in the preview | compare with the base repo workflow sample; VERIFY link in the YAML header |
| `unanswered function_call` in errors | a specialist called a client tool inside the workflow | facts missing from the case header: extend gather_facts(); or remove the tool from the specialist |
| Packet has `problems` | model returned prose or an extra field | rerun; tighten the HANDOFF instructions; the strict schema is enforced by validate_packet() |
| Hosted tool returns `not available` | `agents.json` not vendored and `BENEFITS_WORKFLOW_AGENT_NAME` unset | set the env var on the server or copy `agents.json` next to `main.py` |
| Model or region errors | deployment not in the project region | match `AZURE_AI_MODEL_DEPLOYMENT_NAME` to the portal |

## References
- Learn: [Develop AI agents with Microsoft Foundry and Visual Studio Code](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/), [Integrate custom tools into your agent](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/), [Build agent-driven workflows using Microsoft Foundry](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/)
- Base repo notebooks reused: `azure-ai-agents/*prompt-agent*`, `azure-ai-agents/*workflow*` (WorkflowAgentDefinition sample)
- Workflows how-to: https://learn.microsoft.com/azure/foundry/agents/how-to/workflows (preview; VERIFY Power Fx helpers)
