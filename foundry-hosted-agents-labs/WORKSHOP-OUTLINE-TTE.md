# Workshop outline: Foundry Hosted Agents with Turing Team Engineering

One-day, pro-code workshop for engineers building benefits-marketplace agents. Each section maps to one lab
folder under `labs/`. Every section runs teach, demo, do, checkpoint (10 / 10 / 35 / 5). The teach
block is about the Turing Team Engineering (TTE) principles the lab makes concrete; the demo shows the
lab's code doing them; the lab is the learners' hands. Section N produces the artifact Section N+1
reads.

Continuity chain: `USE-CASE.md` (brief) -> Section 1 `artifacts/lab1/hosted.json` -> Section 2
`artifacts/lab2/knowledge.json`, `hosted.json`, `sessions/` -> Section 3
`artifacts/lab3/handoff_packets/`, `hosted.json` -> Section 4 `artifacts/lab4/eval_report.md`,
`gate_result.json`, `pipeline.md` -> Stretch 5 `artifacts/stretch5/agents.json` -> Stretch 6
`artifacts/stretch6/invocations.json`. Anyone behind runs `python labs/catch_up.py --through N`.

Reference material: `README.md` (where things run), `TTE-PRINCIPLES-BY-LAB.md` (the full
principle-to-feature mapping and the evidence behind each claim), `SETUP.md` (environment).

---

## Section 0: Opening (30 min, before the first breakout)

- Purpose of the day
  - Build the Benefits Marketplace Concierge as Foundry Hosted Agents: your code, run and scaled by Foundry, with the platform's identity, versions, knowledge and evaluation around it
  - Leave with a deployable, tested, observable agent and an operating model for it
- Where things run (from `README.md`)
  - Learner workstation: VS Code + the base repo dev container; notebooks (`labN_walkthrough.ipynb`) and `.py` drivers are the cockpit
  - Microsoft Foundry: hosted agents as containers Foundry builds from the ZIP `azd` uploads; `hosted/main.py` is the product
  - State outside the container: Redis or files; never inside
- The one use case (from `USE-CASE.md`)
  - Two lines of business, one participant journey: Marketplace (plans, carriers) and Accounts (HRA, claims, cards)
  - The rule that shapes everything: only a licensed benefit advisor recommends or enrolls
  - Three scenarios everyone runs: S1 Evelyn (AEP shopper), S2 Harold (denied claim), S3 Rosa (pre-Medicare, both LOBs)
- Turing Team Engineering in five minutes (from `TTE-PRINCIPLES-BY-LAB.md`)
  - Four objectives: Cost, Quality, Governance (control and evidence), Human-Agent Collaboration
  - Ten principles, two pillars: what people own (P1-P5), how agents run (P6-P10)
  - The framework's own rule: measured findings decide what a principle claims; several are conditional or refuted, and the day says so
  - The day's spine: P1 brief (Section 1), P3 files and freshness (Section 2), P2 and P7 architecture and gates (Section 3), P4 and P6 acceptance and cost (Section 4)
- Setup check (`SETUP.md` five-minute verification)
  - `az account show`, `python common/benefits_data.py`, `BENEFITS_TODAY=2026-10-06`, `.env` filled
  - Proctors confirm remote attendees can reach the project

---

## Section 1: Hosted agent basics (lab folder `labs/lab1-hosted-agent-basics/`)

- Teach (10 min): principles
  - P1 Concepts Defined by People: the complete brief up front
    - The agent's instructions plus `guardrails.COMPLIANCE_INSTRUCTIONS` are one written brief, versioned with the agent
    - Evidence: a complete brief beat vague prompting plus clarification turns by 51-70% (t10); live, 0% to 92% gate-pass on a moderately specified task (a01)
    - The brief is the unit of delegation, not the chat scrollback
  - P2 Architecture: default to one capable generalist
    - Lab 1 is one agent with three tools, on purpose
    - Evidence: orchestration cost 54-63% more with no crossover (t14, t22); live, the single agent won cost, reliability and latency (a02). Multi-agent is bought later, for a reason
  - P2 Architecture: staged adoption
    - Local process on 8088, then a dev deployment, then promotion in Section 4
  - P6 Token Resources Management: model right-sizing
    - `gpt-5.4-mini` is the default deployment; live, the cheap model held 100% on hard work at -73% and the stronger model failed a routine contract (a04). Requalify tiers on real tasks
  - P7 Human Review Gates: least privilege from the first deploy
    - Per-agent Entra identity; Foundry Project Manager deploys, Foundry Agent Consumer invokes; `approval_mode` on tools is where autonomy is granted per action
  - P8 Agent-Friendly Languages
    - Python hosted runtime (t13); typed `Annotated[..., Field]` tool schemas state the contract in few tokens
- Demo (10 min): the code doing it
  - `python lab1-hosted-agent-basics/lab1_hosted_basics.py`: vendoring, `hosted.json`, server on 8088, S1 and S2 through `POST /responses`
  - Read S1 turn 2 aloud: "just tell me which plan I should pick" gets a refusal and an advisor offer; point at `checks: no_recommendation=OK` (P1 brief holding, P4 gate reading it)
  - `--deploy`: walk the `azd ai agent init --protocol responses --deploy-mode code --dep-resolution remote_build` and `azd up` lines; in the portal, the version, its status and logs (P2 staged adoption; P7 identity)
  - `hosted/test_local.py --deployed`: same questions, same checks, against the version Foundry runs (P4 externally checked gate)
- Lab (35 min): `lab1_walkthrough.ipynb` or the driver
  - Run it locally; open `artifacts/lab1/transcripts.md`; confirm S1 turn 2 offers an advisor and names no plan
  - Keep a server running; call it from the notebook with `post_responses`
  - YOUR TURN: add `get_sponsor` as a fourth `@tool`; restart; ask as P-1001 (P8 typed tools)
  - Deploy; wait for `active`; record the version in `hosted.json` (P2 staged adoption)
  - YOUR TURN: tighten one instruction so the advisor offer always names the enrollment window; test locally; `azd up` a new version; the old version stays (P1 written intent, versioned)
  - YOUR TURN: call the deployed endpoint from the notebook; regenerate transcripts from the cloud version and compare (P4 gate on what ships)
- Checkpoint (5 min)
  - Paste S1 turn 2 and the `deployed` block of `artifacts/lab1/hosted.json`
  - Section 2 reads `artifacts/lab1/hosted.json`
  - Retrospective question (P10, lightweight): which instruction change moved the answer, and how would you know without reading it?

---

## Section 2: Knowledge and session storage (lab folder `labs/lab2-hosted-knowledge-sessions/`)

- Teach (10 min): principles
  - P3 File-Based Inputs: the prebuilt index that must stay fresh
    - The Foundry IQ knowledge base is a prebuilt index over the customer's Word-to-Markdown docs, split by bounded context
    - Evidence: -52/-53% cheaper than re-injecting docs (a03, t11); the reversal: a stale index failed freshness 0/25 while re-retrieval passed 18/25. The durable artifact is cheaper until it is wrong
    - Freshness is a governance duty: `last_reviewed` frontmatter, a rebuild schedule, an owner
  - P3 and P5: per-agent slice and scoping judgement
    - Two knowledge sources (marketplace, accounts) plus universal docs; each agent gets its slice (t04); scope pays when there is noise to scope out (t03)
  - P6 Token Resources Management: cache-aware cost and reuse
    - Without retrieval, prompt tokens balloon 3,392 to 14,937 as the KB grows; with it they stay flat (a03). About 96% of input is cached (H16): budget in dollars, not tokens
  - P7 Human Review Gates: workspace-enforced policy
    - The container's managed identity holds Search Index Data Reader only; the knowledge base is reached through a governed project connection, not a key
  - P9 Loops: bounded, resumable state
    - Hosted containers restart on every version roll and scale to N replicas; conversation history and the session map live outside
    - Evidence to read honestly: durable hand-off machinery cost about 2x with no measured reliability gain (a11). Keep the session record small and measure what it saves
  - P1: intent can change
    - Stored history must not anchor a participant to an earlier request (t01, a06)
- Demo (10 min): the code doing it
  - `python lab2_hosted_knowledge.py`: indexes build; show `data/knowledge/hra-reimbursement-rules.md` and its frontmatter (P3 input artifact with `last_reviewed`)
  - Portal: AI Search knowledge base and sources; Foundry Management center connection with `ProjectManagedIdentity` (P7)
  - Server log: `knowledge: MCP ...`, `history: file (...)`, `benefits-concierge-hosted v2 tools=6`
  - Turns 1 and 2 with `[KB-MKT-001]` citations (P3 evidence); kill the process; restart; turn 3 by a different pid still remembers atorvastatin; read `continuity check: OK` (P9)
  - Open `artifacts/lab2/sessions/S1-evelyn.json` and `message_store/`: everything the container did not keep
  - `--deploy`: `azd env set BENEFITS_KB_MCP_URL`, where the identity needs Search Index Data Reader
- Lab (35 min): `lab2_walkthrough.ipynb` or the driver
  - `--build-only`: two indexes, knowledge sources, knowledge base, connection; `python knowledge_base.py --demo-only` returns KB-ACC-001 first for the accounts query (P3)
  - `--demo-only`: three turns, two pids, `continuity check: OK`; confirm the citation and the memory in `transcripts.md`
  - Keep a server running; `test_local.py --session S2-harold`; the "which plan is best" turn must refuse (P1 brief, P4 check)
  - YOUR TURN: scale out. Start Redis, set `BENEFITS_REDIS_URL`, run two servers on 8088 and 8089, send turn 1 to one and turn 3 to the other with the same session id (P9 state outside the container)
  - YOUR TURN: break it. Point the restarted process at an empty message store; `continuity check: FAIL` with the warning that explains why; restore
  - YOUR TURN: knowledge on and off. Ask for accepted proof of payment with and without `BENEFITS_KB_MCP_URL`; without it the agent must say the rule text is not at hand (P1 rule 4: tools and knowledge only)
  - Optional: deploy v2, `azd up` again after a greeting change, sessions survive the version roll
- Checkpoint (5 min)
  - Paste the `continuity check` line with both pids and one citation from turn 2
  - Section 3 reads `artifacts/lab2/knowledge.json` (connection id) and `hosted.json`
  - Retrospective question: which knowledge doc would go stale first in production, and who owns rebuilding it?

---

## Section 3: Multi-agent triage with advisor handoff (lab folder `labs/lab3-hosted-multi-agent-handoff/`)

- Teach (10 min): principles
  - P2 Architecture: orchestration is bought for control, not efficiency
    - The framework's biggest reversal: live, the single agent won cost (-45 to -49%), reliability (100% vs 68-76%) and latency (-32 to -37%) against orchestrator plus specialists (a02); no cost crossover as tiers grow (t22)
    - What survives: auditability and role-separated review. Here that means a compliance reviewer with no tools and a packet writer with no tools, because a licensed-advisor rule needs segregation of duties
    - Say it plainly: we are paying for governance, and Section 4 will measure the price
  - P7 Human Review Gates: hard limit, stop when confused, externally verified
    - Only a licensed advisor closes a case: approve / revise / decline is the human review gate
    - Revise once, then flag: "when confused, stop" as code
    - `guardrails.contains_recommendation` runs in deterministic Python outside the model; the harness-audit lesson: a gate the agent can influence is not a control
    - Evidence to read honestly: the code-enforced gate did not separate from the prompt-enforced one live (a05); keep the code gate as the backstop, do not credit it for what the prompt already holds
  - P4 Acceptance Criteria: validity versus graded quality
    - `response_format=HandoffPacket` answers "is it a packet"; whether the packet is good is a separate graded question. In one live run validity read 100% while graded quality read 0% (a07)
  - P9 Loops: bounded iterations and a defined exit
    - A retry cap and a finish test, not an open loop
  - P8 Agent-Friendly Languages: structured where it counts
    - Structured output on the complex, error-prone step (a08); prose elsewhere
  - P3 File-Based Evidence: the packet is the record
    - Facts with source citations, compliance flags, advisor decision, attempts; written to `artifacts/lab3/handoff_packets/`
  - P10 Retrospectives: the reviewer is not a defect finder
    - Fresh-eyes critics found no more defects than self-review (t15, t17). The compliance reviewer exists for licensing segregation, not for quality; say so
- Demo (10 min): the code doing it
  - `lab3_hosted_multi_agent.py --auto-approve --scenario S3`; tail the server log: `intake ... lob=both`, both specialists, the compliance gate, the packet writer (P2 graph)
  - Client output: `status=pending_advisor_approval`, `advisor> revise: ...`, `attempts=2`, `advisor> approve`, packet written (P7 gate across HTTP turns; P9 bounded)
  - Open `S3.json`: `open_questions` carries "which one should I pick" for the advisor, unanswered; `facts_gathered` with sources; `compliance_flags`; `advisor_decision` (P3 evidence, P4 schema)
  - `--restart-between-turns` on S2: the server dies after the pending packet and comes back before approve; `resume_path=session_store` (P9 state outside)
  - `--deploy`: `benefits-triage-hosted` version 1 and its logs
- Lab (35 min): `lab3_walkthrough.ipynb` or the driver
  - Run all three scenarios with `--auto-approve`; S1 marketplace, S2 accounts, S3 both; no `options_discussed` names a preference (P1 rule 1)
  - YOUR TURN: revise instead of approve on S3; compare `packet_attempts` and `open_questions` with a neighbor (P7 human gate)
  - YOUR TURN: lose the process, keep the case; `--restart-between-turns`; then with Redis (P9)
  - YOUR TURN: make the reviewer earn its keep. Add "finish with the single plan you would pick" to the marketplace instructions; watch `compliant=False` and the send-back; the packet carries the flag (P7 externally verified gate; P4)
  - YOUR TURN (TTE addition): the cost of governance. Run S1 through Section 2's single agent and through this workflow; compare tokens, calls and latency in the logs; write one sentence on why the workflow is still worth it here (P2, a02 made local)
  - Optional: deploy and `test_local.py --deployed`
- Checkpoint (5 min)
  - Paste `S3.json`'s `open_questions`, `compliance_flags`, `advisor_decision`
  - Section 4 reads `artifacts/lab3/hosted.json` and at least one packet
  - Retrospective question: which step would you remove if the advisor rule did not exist, and what would that save?

---

## Section 4: Operate hosted agents (lab folder `labs/lab4-operate-hosted-agents/`)

- Teach (10 min): principles
  - P4 Acceptance Criteria: deterministic checkers first, judges second
    - `NoRecommendationEvaluator` and `PiiLeakEvaluator` are pass/fail; Groundedness and Relevance are LLM judges. The framework rates the judge as a prior, not live evidence (a12). The release gate fails on the deterministic checks; judged scores warn
    - Evidence: a deterministic checker held 25/25 vs 8/25 at scale (t07); stern prompt wording caught nothing at +37-44% (t20). Harden the gate, not the prompt
    - Report validity ("responded and parsed") and graded quality ("met the bar") as two numbers (a07)
  - P3 File-Based Evidence and Outputs
    - Traces are the per-run compliance record; `eval_report.md`, `gate_result.json`, `pipeline.md` are audit artifacts; `pipeline.md` is generated from the YAML so the runbook cannot drift
  - P6 Token Resources Management: cost observability, attribution, right-sizing
    - Read `est_cost` from spans with cache reads and writes priced separately (H16); attribute per session and participant; requalify `gpt-5.4-mini` against the golden set before any tier change (a04)
    - Backpressure over naive retry against a shared deployment quota: under 2-3x overload naive retry congestion-collapsed, backpressure served 2.2-3.8x more (a10)
  - P7 Human Review Gates: verified outside the agent, approved by a person
    - The eval gate runs in CI, outside the agent's reach; promotion to test and prod is a GitHub Environment with reviewers
  - P2 Architecture: staged adoption as a pipeline
    - dev, test, prod with per-environment configuration; rollback is a redeploy or a version delete; gate each level on evidence
  - P10 Retrospectives: the honest framing
    - The promising operational form is exactly this lab: evaluation over real logged outcomes feeding the next instruction version. The live result was not supported (a07, t23). Teach "earn it with a graded metric", not "learning loop"
- Demo (10 min): the code doing it
  - `python lab4_operate.py --limit 3`: tracing connection string, `azd env set APPLICATIONINSIGHTS_CONNECTION_STRING` (the whole tracing change for the hosted agent)
  - Q1-Q3 with `cites=`, `ground=`, `relev=`, `norec=`, `pii=` against the same `main.py` Section 2 shipped (P4 two kinds of check)
  - `artifacts/lab4/eval_report.md`: summary, per-question table, empty Violations (P3 evidence)
  - `python eval_gate.py` PASS and `gate_result.json`; `python promote.py --to test` dry run (P7 gate, P2 staged)
  - Portal Tracing: `via.golden_question` span, hosted agent spans underneath (model call, `search_plans`, the `benefits-kb` MCP call); Versions blade (P6 observability)
  - `.github/workflows/agent-ci.yml` beside `pipeline.md` (P3 generated evidence)
- Lab (35 min): `lab4_walkthrough.ipynb` or the driver
  - `--limit 6 --skip-judges`: `no_recommendation_violations: 0`, `pii_leaks: 0`, citation rate above 0.5 (P4 deterministic)
  - Full run with judges: read the two lowest rows and decide whether the agent or the judge is wrong (P4 judge as prior)
  - `eval_gate.py` then `promote.py --to test`; `promotions.jsonl` has a line (P7, P2)
  - YOUR TURN: stricter gate. Add `MustNotEvaluator`; the summary gains a column; the gate still passes (P4)
  - YOUR TURN: break it. Add "name the plan you think fits best" to the Section 2 instructions; `FAIL`, exit 1, the violating question named; revert (P4 gate stops what the prompt allowed)
  - YOUR TURN: trace one question; count child spans; paste the slowest (P6 observability)
  - YOUR TURN (TTE addition): price it. From the spans, compute `est_cost` per scenario for Section 2's agent and Section 3's workflow; write both next to their gate-pass rates. Cheaper only counts among gate-passers (P6 with P4)
  - Optional: deployed target, `azd up` with the connection string, roll back by deleting the new version (P2)
  - Optional: `--foundry-eval` and the Evaluation blade (preview)
- Checkpoint (5 min)
  - Paste the `[lab4] summary:` line and the `## Eval gate:` line
  - `eval_report.md` and `gate_result.json` must exist; `promote.py` refuses without a passing gate
  - Retrospective question: which instruction change would you make from the lowest-scoring question, and which graded metric would prove it helped?

---

## Closing for the core day (20 min)

- Walk the chain end to end: brief, knowledge, triage, gate, pipeline; one hosted agent lineage `benefits-concierge-hosted` v1 to vN, plus `benefits-triage-hosted`
- TTE roll-up: which principles the room saw hold (P1 brief, P3 files, P4 gates, P6 right-sizing), which it saw as conditional (P3 freshness, P9 durable state), which it saw as a paid trade-off (P2 orchestration), and which remains to be earned (P10)
- What to take back: the `hosted/` folder shape, `eval_gate.py`, the freshness owner list, the session store, the questions in each checkpoint
- Stretch sections for fast finishers or follow-up

---

## Stretch 5: Prompt agents and workflow agents (lab folder `labs/stretch5-prompt-agents-and-workflows/`)

- Teach (10 min): principles
  - P2 Architecture: people choose the shape
    - Platform-managed prompt agent versus hosted code is a decision with owners: business-owned instructions and portal governance versus engineering-owned code, tests and CI
    - Repeat the orchestration caveat (t14, t22, a02) for the YAML workflow agent
  - P1 Concepts Defined by People
    - A prompt agent's instructions are a written, versioned brief a business owner can review in the portal; version history is the decision ledger, with the override caveat (t01)
  - P8 Agent-Friendly Languages: declarative over imperative
    - The YAML workflow says what the result should be. The framework marks this a practitioner rule of thumb, not harness-measured; say so
  - P3 File-Based Evidence
    - The streamed `workflow_action` trail is the audit log of who touched the case
  - P5 Skills for People: configured vocabulary (t05)
    - Shared agent names, scenario ids and knowledge doc ids are a checked-in vocabulary both platform and hosted agents understand
- Demo (10 min)
  - `stretch5_prompt_agents.py --concierge-turn`: six prompt agents and `benefits-triage-workflow` created; the client-side function-call loop prints the tools it ran ("the platform asked us to run Python; a workflow cannot do that")
  - S1 through the workflow: `workflow_action` lines in order, packet saved (P3 trail)
  - Portal: the workflow graph; edit `compliance-reviewer` instructions in the portal, a new version, no deployment (P1 business-owned brief)
  - `hosted_tool_snippet.py`: one function, one Responses call with `agent_reference`; the hosted agent delegating to the platform
- Lab (35 min)
  - `--build-only`; `agents.json` with six agents and the workflow version
  - `--demo-only --concierge-turn`; AEP dates named, `no_recommendation=OK`; S1 packet `lob=marketplace`
  - YOUR TURN: change an instruction in the portal; rerun; `agent_reference` by name resolved to the new version (P1 versioned intent)
  - YOUR TURN: break the router (`ROUTE: accounts`); read `open_questions`; restore (P4 schema still holds while quality drops: validity versus graded)
  - YOUR TURN: wire the hosted agent. Paste the `run_triage_workflow` tool into Section 2's `hosted/main.py`; set `BENEFITS_WORKFLOW_AGENT_NAME`; ask as P-1005 (P2 chosen shape: code owns the conversation, platform owns the regulated hand-off)
- Checkpoint (5 min)
  - Paste the `workflow_action` trail for S1 and the `lob=` line
  - Retrospective question: which of the five agents should the business own, and which should engineering own?

---

## Stretch 6: Invocations protocol, Toolbox, Skills (lab folder `labs/stretch6-invocations-toolbox-skills/`)

- Teach (10 min): principles
  - P2 Architecture, toolsets: deterministic over clever
    - `claims_review.py` computes the facts (reason codes, accepted documents, steps) from the knowledge doc; the model writes only the participant explanation
    - Evidence: a codified module beat restated requirements 25/25 vs 12/25 (t09); a deterministic checker held where reasoning did not (t07)
  - P4 Acceptance Criteria
    - `response_format=ClaimReviewBatch` is the schema gate; the deterministic facts are checkable against the source doc
  - P8 Agent-Friendly Languages: structured in, structured out
    - Invocations is the protocol for batch and API-to-API work; the format facet transfers (a08)
  - P3 File-Based Inputs: the Team Brain
    - `SKILL.md` is a versioned, reusable artifact that ships with the agent; same freshness duty as the knowledge base (a03)
  - P6 Token Resources Management: context management
    - Progressive disclosure (skill index in instructions, body on demand); compaction only pays when aggressive (t02), so measure rather than assume
  - P7 Human Review Gates: workspace-enforced policy
    - The Toolbox rule for what may go to `web_search`; PHI never leaves
  - P9 Loops: bounded and stateless
    - One request, one response, no session; the exit is the schema
- Demo (10 min)
  - `stretch6_invocations.py --offline`: three packets with no model; `CLM-9003.json` carries the five accepted proof-of-payment documents copied from KB-ACC-001 (P2 deterministic facts)
  - Online: same factual fields, prose `participant_explanation` added with `[KB-ACC-001]` (P8 bounded model contribution)
  - `--skills-demo`: `skills=['hra-reimbursement-rules']` at startup, `read_skill` before the answer (P3, P6)
  - `--deploy`: two `azd ai agent init` blocks, `invocations` and `responses`; Toolbox question if provisioned
- Lab (35 min)
  - Offline then online; `denied_with_fix == ["CLM-9003"]`, `denied_no_fix == ["CLM-9021"]`
  - YOUR TURN: nightly denials. Replace `BATCH` with every denied claim id; say which Foundry feature would schedule it (P9 bounded batch loop)
  - Skills: read `skills_transcript.md`; break it by renaming the skill folder; the answer loses the accepted-document list (P3 artifact dependency)
  - YOUR TURN: a second skill from `debit-card-faq.md`; watch `read_skill("debit-card-faq")` (P3, P6)
  - Optional: deploy both protocols
- Checkpoint (5 min)
  - Paste the `participant_explanation` for CLM-9003 and the protocol comparison row you found most useful
  - Retrospective question: which facts in the review should never come from the model, and how does the schema enforce that?

---

## Facilitator notes

- Pace is set by the room; remote proctors unblock stragglers with `catch_up.py --through N` at the top of each hour
- Every Teach block quotes the framework's verdicts including the conditional and negative ones (a02, a05, a07, a11). That is the framework working, not a caveat to skip
- The two TTE additions (Section 3 cost-of-governance comparison, Section 4 price-it exercise) are the only new lab steps beyond the existing READMEs; add them to the lab READMEs before delivery
- Nothing here ran against a live Foundry project during authoring; run the `SETUP.md` smoke test the day before, and check the `# VERIFY` list in the two writer-notes files
