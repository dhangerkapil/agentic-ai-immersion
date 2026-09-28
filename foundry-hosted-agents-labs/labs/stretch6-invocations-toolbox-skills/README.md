# Stretch 6: Invocations protocol, Foundry Toolbox and Skills

| | |
|---|---|
| Goal | Host a second agent on the Invocations protocol (`denied-claims-review`: claim ids in, one review packet per claim out), give the Responses concierge a bundled Skill and, when configured, a Foundry Toolbox, and compare the two protocols. |
| Time | 45-60 min (stretch; do the Invocations half first) |
| Starts from | `artifacts/lab1/hosted.json` (or `python catch_up.py --through 1`); the lab runs without it |
| Produces | `artifacts/stretch6/invocations.json`, `artifacts/stretch6/claim_reviews/CLM-*.json`, `artifacts/stretch6/skills_transcript.md` |
| Learn path modules | 7 Develop an AI agent with Microsoft Agent Framework; 2 Integrate custom tools into your agent; 3 Integrate MCP Tools with Azure AI Agents |

**Where this runs:** both. The notebook (workstation) vendors and starts each `main.py` locally and calls it. `hosted-invocations/main.py` and `hosted-responses-skills/main.py` are the products Foundry runs after `azd up` with `--protocol invocations` and `--protocol responses`. **Foundry Toolbox and Foundry Skills are preview features**; the code that touches them carries `# VERIFY` tags.

## What you'll learn
- Explain when a hosted agent should speak Invocations (one structured request, one structured response, stateless) instead of Responses (multi-turn, streaming, sessions).
- Build an Invocations agent whose facts are deterministic (a tool over the systems of record and KB-ACC-001) and whose model contribution is bounded (a plain-language explanation inside a Pydantic schema).
- Bundle a Skill as `skills/<name>/SKILL.md`, embed its index at startup and load the body on demand (progressive disclosure).
- Attach a Foundry Toolbox (web_search, code_interpreter) to a hosted agent over MCP, and state the rule for what may go to the web.
- Deploy two agents with two protocols from two flat folders using the same azd commands.

## Technical features taught

| Feature | Foundry / SDK object | Where in the code | Why it matters for Benefits Marketplace |
|---|---|---|---|
| Invocations protocol host | `agent_framework_foundry_hosting.InvocationsHostServer(agent).run()`; body `{"message": "..."}` | `hosted-invocations/main.py` `__main__`, `test_local.py` `call_local()` | Nightly denial reviews and API-to-API calls need a request/response endpoint, not a chat |
| Deterministic facts, bounded model | `@tool review_denied_claims` over `claims_review.review_claims`, `response_format=ClaimReviewBatch` | `hosted-invocations/claims_review.py`, `main.py` | Reason codes, accepted documents and steps come from the KB; the model only writes the explanation |
| KB text as structured rules | `benefits_data.read_knowledge_doc("KB-ACC-001")` parsed into lists | `claims_review.hra_rules()` | The same governed document feeds the chat agents and the batch agent |
| Skills bundled in the ZIP | `skills/<name>/SKILL.md` (frontmatter + body), `load_skills()`, `skills_index()` in instructions, `read_skill` tool | `hosted-responses-skills/main.py`, `skills/hra-reimbursement-rules/SKILL.md` | Procedures the accounts team owns ship with the agent and are versioned with it |
| Foundry Toolbox over MCP (preview) | `MCPStreamableHTTPTool(name, url=TOOLBOX_MCP_URL, http_client=httpx.AsyncClient(auth=EntraBearerAuth()))`, `_ping_available = False` | `hosted-responses-skills/main.py` `toolbox_tool()` | web_search and code_interpreter without writing tools; Entra token, no keys |
| Two protocols, one deploy path | `azd ai agent init --protocol invocations` / `--protocol responses` | `stretch6_invocations.py` `deploy_commands()` | Same folder shape, same RBAC, same version model for both |

## Two protocols compared

| Dimension | Invocations (`benefits-claims-review-invocations`) | Responses (`benefits-concierge-hosted`, `benefits-triage-hosted`) |
|---|---|---|
| Interaction | One structured request -> one structured response | Multi-turn conversation |
| Tool use | Deterministic; the model fills in prose only | Model-directed: tools, skills, toolbox |
| Streaming | No (batch result) | Token by token (OpenAI compatible) |
| State | Stateless | Session history (Lab 2 message store) |
| Request body | `{"message": "<json string>"}` (path: VERIFY) | `{"input": "...", "previous_response_id"?}` at `POST /responses` |
| Best for | Batch jobs, pipelines, API-to-API, nightly reviews | Advisor and participant chat, research |
| Host server | `InvocationsHostServer(agent)` | `ResponsesHostServer(agent)` |
| Benefits Marketplace example | Review the day's denied claims and draft the follow-ups | Concierge, triage with human approval |

## Teach (10 min)
- Same build pattern as every lab: `FoundryChatClient -> Agent -> host server`. Only the host server changes. `InvocationsHostServer` expects JSON (`{"message": ...}`; a plain string gives HTTP 500) and returns one result. No session, no stream.
- Why deterministic first: a batch reviewer that invents an accepted document is worse than none. `claims_review.py` computes every factual field from `benefits_data` and KB-ACC-001; the model writes `participant_explanation` inside a schema and is told to copy everything else verbatim. The structured output makes the copy checkable.
- Skills are Markdown with frontmatter. The agent embeds only the index (name and description) and loads the body with `read_skill` when the question is in that area. That keeps the prompt small and lets the accounts team own the procedure without touching Python.
- Toolbox (preview): Foundry hosts `web_search` and `code_interpreter` behind an MCP endpoint. The agent reaches it with `MCPStreamableHTTPTool` and an Entra token. Rule for Benefits Marketplace: public information only goes to the web; participant data never does. The instruction says so, and Lab 4's evaluation should test it.
- Both agents deploy the same way as Lab 1. Two folders, two `azd ai agent init` calls, two agent names, one project.

```
batch caller (pipeline, Routine, notebook)                Foundry hosted agent (Invocations)
POST {"message": "{\"claim_ids\": [\"CLM-9003\", ...]}"} -->  Agent --tool--> review_denied_claims -> claims_review.py
                                                                 |                              |-> benefits_data.get_claim_status
                                                                 |                              '-> KB-ACC-001 (accepted documents)
<-- ClaimReviewBatch {reviews: [{claim_id, status, review, fix_available, accepted_proof_of_payment[], participant_explanation}]}

participant chat                                          Foundry hosted agent (Responses + Skills + Toolbox)
POST /responses {"input": "... CLM-9003 was denied ..."}  --> Agent --> read_skill("hra-reimbursement-rules") -> SKILL.md body
                                                                    --> get_claim_status                       -> benefits_data
                                                                    --> (toolbox) web_search / code_interpreter  -> Foundry Toolbox over MCP
```

## Demo (10 min)
1. `cd labs && python stretch6-invocations-toolbox-skills/stretch6_invocations.py --offline`. No model: point at the three packets (`resubmit`, `no_fix`, `not_denied`) and open `claim_reviews/CLM-9003.json`: `accepted_proof_of_payment` has five entries copied from the KB.
2. Run without `--offline`. The Invocations server starts, one batch goes in, each review now has a `participant_explanation` citing `[KB-ACC-001]`. Compare with the offline packet: every factual field identical, prose added.
3. `--skills-demo`: the Responses agent answers S2. In `artifacts/stretch6/hosted-responses-skills_local.log` show `skills=['hra-reimbursement-rules']` at startup and the `read_skill` call before the answer.
4. `--deploy`: two `azd ai agent init` blocks, protocols `invocations` and `responses`. If the Toolbox is provisioned in the room's project, set `TOOLBOX_NAME` and `TOOLBOX_MCP_URL` on the hosted agent and ask for this year's Part B standard premium: the answer says it came from the web.

## Do (35 min)
1. **Offline then online (10 min).** Run `--offline`, then the default. Checkpoint: `invocations.json` has `sample_run.denied_with_fix == ["CLM-9003"]` and `denied_no_fix == ["CLM-9021"]`.
2. **YOUR TURN (10 min): nightly denials.** Replace `BATCH` with every denied claim id in the data (`benefits_data.get_hra_account(pid)["claims_summary"]["denied_claim_ids"]` per participant) and run again. That is the shape of a scheduled job; say which Foundry feature would schedule it (Routines, preview, see `labs/README.md` "What was cut").
3. **Skills (10 min).** `--skills-demo`. Read `skills_transcript.md`: the accepted documents and the `[KB-ACC-001]` citation should be there. Then break it: rename `skills/hra-reimbursement-rules` and rebuild; the index says `none bundled` and the answer gets vaguer.
4. **YOUR TURN (10 min): a second skill.** Write `skills/debit-card-faq/SKILL.md` from `data/knowledge/debit-card-faq.md` (KB-ACC-002). Rebuild, restart, ask "my card was declined at the pharmacy". Watch `read_skill("debit-card-faq")` in the log.
5. **Deploy (optional).** `--deploy` and run both blocks. Invoke the Invocations agent through the project and the Responses agent through `responses.create(..., agent_reference)`.

## Checkpoint (5 min)
Paste the `participant_explanation` for CLM-9003 and the protocol comparison row you found most useful. Nothing downstream depends on this stretch.

## If you're behind
`python stretch6_invocations.py --offline` gives you the packets and the artifact in seconds. Skip the Toolbox entirely; it is preview and needs a provisioned Toolbox in the project.

## Stretch (only if you're done early)
Make the Invocations agent write its batch result to `artifacts/stretch6/` as a JSONL file the Lab 4 evaluation can read, and add a `label_model` grader that fails any explanation promising payment.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| HTTP 500 from the Invocations server | Body was a plain string | Send JSON: `{"message": "..."}` (test_local.py does) |
| `no invocations path answered` | The served path differs from `/invocations` | Read the server log for the route; set `BENEFITS_INVOCATIONS_PATH` |
| `reviews` empty after a successful call | Response envelope shape differs from the guesses in `extract_reviews()` | Print `response.text`, adjust `extract_reviews`; this is a VERIFY item |
| `participant_explanation` promises payment or names a plan | Instruction drift | The compliance block forbids it; tighten the instruction and add the Lab 4 grader |
| `skills=none` at startup | `skills/` not copied into `hosted-responses-skills/` or `SKILL_NAMES` filters it out | Run `build()`; check `SKILL_NAMES` |
| Toolbox session closes immediately | Foundry Toolbox does not implement MCP ping | Keep `_ping_available = False` (VERIFY the attribute name against the installed build) |
| 401/403 calling the Toolbox | Token scope or the agent identity lacks access to the Toolbox | Check the scope in `EntraBearerAuth`; wait for propagation |
| 403 on deploy / invoke, 424 session_not_ready | Same as Lab 1 | Roles; wait for `active`; read the logstream |
| Region or model errors | Toolbox and Skills are preview and region-limited | Check the project's region; run the Invocations half only |

## References
- Learn: [Develop an AI agent with Microsoft Agent Framework](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/) (module 7), [Integrate MCP Tools with Azure AI Agents](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/) (module 3)
- Hosted agents (protocols, deploy from source): https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents
- Base repo reused: `hosted-agents/benefits-review-invocations/main.py` (InvocationsHostServer), `hosted-agents/benefits-advisor-responses/` (SKILL_NAMES, TOOLBOX_NAME, `_ping_available`), `hosted-agents/README.md` (comparison table, troubleshooting)
