# Lab 3: Hosted multi-agent handoff

| | |
|---|---|
| Goal | Run the Benefits Marketplace triage workflow (intake, two specialists in parallel, compliance review, advisor handoff packet) inside a hosted agent, and let the licensed advisor approve, revise or decline the packet on the next HTTP turn. |
| Time | 60 min: teach 10, demo 10, do 35, checkpoint 5 |
| Starts from | `artifacts/lab2/hosted.json` (or `python catch_up.py --through 2`; `--standalone` skips the check) |
| Produces | `artifacts/lab3/handoff_packets/S1.json`, `S2.json`, `S3.json`, `artifacts/lab3/hosted.json`, `artifacts/lab3/sessions/` |
| Learn path modules | 8 Orchestrate a multi-agent solution using the Microsoft Agent Framework; 6 Build agent-driven workflows using Microsoft Foundry; 7 Develop an AI agent with Microsoft Agent Framework |

**Where this runs:** both. The notebook (workstation) plays participant and advisor against `hosted/main.py` on port 8088 and writes the final packets. `hosted/main.py` (container) runs the `WorkflowBuilder` graph and pauses at `request_info`; Foundry runs it as `benefits-triage-hosted` after `azd up`.

## What you'll learn
- Build an explicit `WorkflowBuilder` graph with custom executors: fan-out to two specialists, fan-in by counting, a compliance gate that sends a draft back once, and a coordinator that asks a human.
- Produce a strict JSON handoff packet with Pydantic `response_format` and carry compliance flags through it.
- Explain how `ctx.request_info` pauses a workflow and how to resume it with `workflow.run(responses={request_id: ...})`.
- Move human-in-the-loop from a terminal `input()` to HTTP turns: the packet comes back `pending_advisor_approval`, the decision arrives as the next `POST /responses`.
- Keep the paused case in `common.session_store` so a restarted container or another replica can still finish it.
- Route every Responses turn through agent middleware that short-circuits the model when the turn is a case or a decision.

## Technical features taught

| Feature | Foundry / SDK object | Where in the code | Why it matters for Benefits Marketplace |
|---|---|---|---|
| Explicit workflow graph | `WorkflowBuilder(start_executor=...).add_edge(a, b).build()` | `hosted/benefits_workflow.py` `build_workflow()` | The triage path is a reviewed graph, not a prompt; edges are auditable |
| Custom executors | `Executor`, `@handler async def h(self, msg: T, ctx: WorkflowContext[Out])` | `IntakeExecutor`, `SpecialistMerge`, `ComplianceGate`, `AdvisorCoordinator` | Intake, merge, gate and coordinator are plain Python you can unit test |
| Fan-out / fan-in | `ctx.send_message(..., target_id=...)` + a counting merge | `IntakeExecutor.start`, `SpecialistMerge.collect` | Marketplace and Accounts answer in parallel for "both LOB" participants |
| Agents as workflow nodes | `AgentExecutor(agent, id=...)`, `AgentExecutorRequest/Response` | `build_workflow()` | Specialists are ordinary `Agent`s reused from any lab |
| Structured outputs | `Agent(..., default_options={"response_format": ReviewVerdict / HandoffPacket})` | `hosted/benefits_specialists.py` builders, `parse_structured()` | The advisor gets a schema-checked packet, not prose |
| Reflection with a bound | `ComplianceGate.decide` (revise once, then flag) + `guardrails.contains_recommendation` | `hosted/benefits_workflow.py` | A bad prompt cannot loop forever; unresolved drafts are flagged for the human |
| Human in the loop | `ctx.request_info(request_data=..., response_type=str)`, `@response_handler`, `workflow.run(responses={...})` | `AdvisorCoordinator`, `start_case()`, `resume_case()` | Only a licensed advisor closes a case |
| HITL across HTTP turns | Agent middleware `triage_router(context, call_next)` sets `context.result` | `hosted/main.py` `triage_router`, `TriageService.start/decide` | A web chat has no `input()`; the decision is simply the next turn |
| Durable pending state | `common.session_store` (`SessionRecord.notes["packet"]`), Redis when `BENEFITS_REDIS_URL` | `TriageService.store_pending/store_final/decide` | Restart or scale-out mid-case, the packet is still there (`resume_path=session_store`) |
| Knowledge for specialists | local `search_knowledge` over `data/knowledge`, or `MCPStreamableHTTPTool` to Lab 2's KB when `BENEFITS_KB_MCP_URL` | `hosted/benefits_specialists.py` `knowledge_tool()` | Same container, two knowledge backends; citations either way |

## Teach (10 min)
- Lab 1 and 2 hosted one agent. Lab 3 hosts a **workflow**: the container still speaks Responses, but a turn now runs a graph of four agents and three pure-Python executors and returns a packet.
- Fan-out and fan-in are explicit edges plus a counter. Intake decides which specialists are in scope for this participant (marketplace, accounts, both) and sends one request per specialist; the merge waits for all of them.
- Reflection: the compliance reviewer returns a structured verdict. If it (or the cheap heuristic) flags a recommendation, the gate sends the offending section back once. Once. Then it forwards the draft with the flag attached so the human sees it.
- `request_info` is how Agent Framework asks a human. The workflow yields a `request_info` event with a `request_id` and goes idle. In a terminal you call `input()` and resume with `workflow.run(responses={request_id: answer})`. A web chat cannot block on `input()`.
- So the hosted agent returns the packet with `status: pending_advisor_approval` and remembers two things: the paused workflow (in memory, this replica) and the packet (in `common.session_store`, shared). The advisor's next turn resumes the workflow if it is still here; if not (restart, new version, another replica), approve and decline finish from the stored packet and revise re-runs only the packet writer. No case is lost either way.
- The middleware trick: every turn passes through `triage_router` before the outer model is called. A case envelope or a decision is handled deterministically and the model never runs; anything else falls through to the outer agent, which explains the format. Deterministic routing is what you want in front of a compliance process.
- Same deploy story as Lab 1: flat folder, `azd up`, `benefits-triage-hosted` version 1. Set `BENEFITS_REDIS_URL` on the hosted agent when you want the session map shared across replicas, `BENEFITS_KB_MCP_URL` to use Lab 2's knowledge base instead of the local search.

```
POST /responses  {"input": "{\"session_id\":\"S3-..\",\"participant_id\":\"P-1005\",\"message\":\"...\"}"}
   |
   v  triage_router (middleware)
 intake --lob=both--> marketplace-guide --+
        \-----------> accounts-assistant -+--> merge --> compliance-reviewer --> gate --(revise once)--> specialist
                                                                                   |
                                                                                   v
                                                        advisor-coordinator --> advisor-handoff (HandoffPacket)
                                                                 |
                                            request_info: PAUSE  |  session_store[S3-..] = packet, status pending
   <-- {"status":"pending_advisor_approval","packet":{...},"next":"approve | revise: .. | decline: .."}

POST /responses  {"input": "{\"session_id\":\"S3-..\",\"advisor\":\"revise: add the IEP dates\"}"}
   -> resume_case(request_id, feedback) -> advisor-handoff again -> PAUSE again (packet_attempts 2)
POST /responses  {"input": "approve"}  (session id from the Responses session or the envelope)
   -> yield_output -> {"status":"approved","packet":{...,"advisor_decision":"approve"}}
```

## Demo (10 min)
1. `cd labs && python lab3-hosted-multi-agent-handoff/lab3_hosted_multi_agent.py --auto-approve --scenario S3`. While it runs, tail `artifacts/lab3/hosted_local.log` in a second terminal: `intake CASE-S3-...: lob=both, specialists=['accounts-assistant', 'marketplace-guide']`, two `merge: got ...` lines, `compliance: compliant=True`, then the pause.
2. Point at the client output: `status=pending_advisor_approval lob=both attempts=1`, then `advisor> revise: add the IEP dates for turning 65 to open_questions`, then `attempts=2`, then `advisor> approve`, then `wrote artifacts/lab3/handoff_packets/S3.json (decision approve ...)`.
3. Open `S3.json`. Read `open_questions` (the "which one should I pick" request is there for the advisor, not answered), `facts_gathered` with sources, `compliance_flags`, `advisor_decision`, `packet_attempts`.
4. Run `--auto-approve --scenario S2 --restart-between-turns`. The server dies after the pending packet and comes back before `approve`; the reply shows `resume_path=session_store`. Open `artifacts/lab3/sessions/S2-*.json`: this is what survived.
5. `--deploy`, then in the portal show `benefits-triage-hosted` version 1 and its logs carrying the same `[benefits-triage]` lines.

## Do (35 min)
1. **Run all three scenarios (10 min).** `python lab3-hosted-multi-agent-handoff/lab3_hosted_multi_agent.py --auto-approve`. You should see three packets written. Checkpoint: S1 is `lob=marketplace`, S2 `lob=accounts`, S3 `lob=both`; no packet's `options_discussed` names a plan to pick.
2. **YOUR TURN (10 min): revise instead of approve.** Run without `--auto-approve` and `--scenario S3`. At the prompt type `revise: add the IEP dates for turning 65 to open_questions`, then `approve`. Compare `packet_attempts` and `open_questions` with a neighbour who approved first time. Then run S2 again and `decline: duplicate of a case already with an advisor`; check `status: declined` in `S2.json`.
3. **YOUR TURN (10 min): lose the process, keep the case.** `--auto-approve --scenario S2 --restart-between-turns`. Confirm `resume_path=session_store`. Start Redis (`docker run -d -p 6379:6379 redis:latest`), set `BENEFITS_REDIS_URL=redis://localhost:6379/0`, run again: the session map is now in Redis (`redis-cli keys 'benefits:session:*'`). Say why this is the difference between one container and N replicas.
4. **YOUR TURN (5 min): make the reviewer earn its keep.** In `hosted/benefits_specialists.py` add "Finish with the single plan you would pick." to `MARKETPLACE_INSTRUCTIONS`. Run S1. In the log you should see `compliant=False`, `sending marketplace-guide back for one revision`, then a clean pass. Remove the line.
5. **Deploy (optional in the room, 10 min).** `--deploy`, run the commands from `hosted/`, wait for `active`, `python hosted/test_local.py --deployed`. Record the version with `--record-version`.

## Checkpoint (5 min)
Paste `S3.json`'s `open_questions`, `compliance_flags` and `advisor_decision` in the room chat. Lab 4 needs `artifacts/lab3/hosted.json` and at least one packet in `artifacts/lab3/handoff_packets/`.

## If you're behind
`cd labs && python catch_up.py --through 3` (vendors and writes `hosted.json`; the packets need a model run: `python lab3-hosted-multi-agent-handoff/lab3_hosted_multi_agent.py --auto-approve --standalone`). Skip the deploy and the Redis step.

## Stretch (only if you're done early)
Enable `build_workflow(..., checkpoint_dir=...)` (VERIFY tag in `benefits_workflow.py`) so the paused workflow itself, not only the packet, survives a restart, then make `TriageService.decide` resume from the checkpoint instead of re-running `advisor-handoff` on `revise`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Missing artifact artifacts/lab2/hosted.json` | Lab 2 not run | `python catch_up.py --through 2`, or add `--standalone` (local knowledge search) |
| Reply `status: no_pending_case` on an advisor turn | Session id in the decision does not match the envelope's, or the case was already closed | Reuse the exact `session_id`; one case per session id; start a new session for a new case |
| Reply `status: error` with `AgentExecutorResponse` or `executor_id` in the text | Framework build differs from the VERIFY notes in `benefits_workflow.py` | Check the two VERIFY tags (`executor_id`, `AgentExecutor(agent, id=)`) against the installed version |
| Turn takes 60-120 s | Two specialists, a reviewer and the packet writer run per case | Expected; the driver uses a 600 s timeout. Watch the log for progress |
| `resume_path=session_store` without a restart | The replica that took turn 2 is not the one that ran turn 1 (or the server restarted) | Expected behaviour; nothing to fix. With one local process it means the server crashed between turns: read the log |
| Packet `compliance_flags` contains `heuristic: ...` on every run | A specialist instruction invites recommendation language | Read the flagged section; tighten the instruction; the gate revises once and then flags |
| 401/403 on deploy or invoke | Roles (Project Manager to deploy, Agent Consumer or User to invoke) | Same as Lab 1; wait for propagation |
| Version `failed`, `ModuleNotFoundError: common` in the error | `prepare.py` not run before `azd up` | Run it, `azd up` again |
| `424 session_not_ready` | Container still starting (four agents build at startup) | Read the version logstream; wait for `agent benefits-triage-hosted: ...` before invoking |
| Wrong LOB for a message | Keyword classifier | YOUR TURN 3 in the script: model-based classification with the keyword list as fallback |

## References
- Learn: [Orchestrate a multi-agent solution using the Microsoft Agent Framework](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/) (module 8), [Build agent-driven workflows using Microsoft Foundry](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/) (module 6)
- Agent Framework workflows, request_info and checkpoints: https://learn.microsoft.com/en-us/agent-framework/workflows/
- Base repo reused: `agent-framework/workflows/5-credit-limit-with-human-input.ipynb` (request_info loop), `agent-framework/workflows/6-*` (executor shapes), `hosted-agents/README.md` (deploy, RBAC)
