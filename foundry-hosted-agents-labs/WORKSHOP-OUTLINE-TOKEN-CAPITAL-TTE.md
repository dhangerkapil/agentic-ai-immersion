# Workshop outline v2: Foundry Hosted Agents, Turing Team Engineering, Token Capital

Business concepts, then architecture concepts, then engineering, in every section. Four core sections
of 80 minutes (teach 15, lab 55, checkpoint and token readout 10), mapped one-to-one to
`labs/lab1-...` through `labs/lab4-...`. Two stretch sections keep the same shape.

Sources: `WORKSHOP-OUTLINE-TTE.md` (previous version), `TTE-PRINCIPLES-BY-LAB.md`, the
`turingteamengineering` repository (`TOKEN_CAPITAL_OUTLINE.MD`, `principles.md`,
`workshop/token-capital-workshop/outline.md`), and the lab READMEs under `labs/`.

---

## Part A: Evaluation of the proposed flow

### As a workshop facilitator

- The within-section order business -> architecture -> engineering works, and it is the right order
  for this room. Engineers accept a business framing when it arrives with the number the lab is
  about to produce. It fails when it arrives as preamble. Rule for every Token Capital slide: name
  the one number this section will measure (for Section 1: cost per gate-passing S1 answer).
- 15 minutes across three conceptual layers is dense. Use one recurring visual, a three-rung ladder
  (Token Capital objective, TTE principle, Foundry object), on every teach slide so the room
  recognizes the pattern by Section 2 and stops re-orienting.
- 80-minute sections times four is 320 minutes of core content. With a 30-minute opening, a
  20-minute closing, lunch and two breaks it is a 9:00 to 4:30 day. That is a full day with no
  slack; the stretch sections must be post-day or a second day, not "if we finish early."
- Four times 55 minutes of hands-on is the strength of this design. Protect it: the demo lives
  inside the 55 (10 minutes), and the facilitator does not add teach content during the demo.
- Remote attendees fall behind in the lab, not the teach. The 10-minute checkpoint at the end of
  each section is where proctors run `catch_up.py` for anyone who did not reach the artifact.

### As a curriculum designer for technical professionals

- The previous Token Capital workshop outline (`workshop/token-capital-workshop/outline.md`) and
  this workshop teach different skills. That outline is a software-delivery workshop: GitHub
  Copilot designs, red-teams, writes tests and code, and the Foundry Hosted Agent is the subject of
  the application being built. This workshop teaches building and operating the hosted agent
  itself. Both are valid; combining their labs doubles the scope and halves the depth. Keep the
  Copilot-SDLC labs as a companion day (or a pre-day for the Salt Lake tech leads), not as core
  sections here.
- The previous outline groups TTE principles by SDLC phase (P1, P5, P8; then P9, P10; then P6, P4,
  P2; then P3, P7). Our labs demonstrate them in a different order, and a principle should be
  taught in the section where the learner's hands touch it. Retrospectives (P10) in Section 2 would
  be taught before there is anything to score, and Human Review Gates (P7) in Section 4 would
  arrive one section after the learner built the approval gate. The new grouping below follows
  the labs.
- Bloom's levels by block: teach at understand (what and why), lab at apply and analyze (build it,
  break it, read the trace), checkpoint at evaluate (state a number, defend a trade-off). The
  retrospective question at each checkpoint is where P10 lives, kept light because the framework's
  own evidence for retrospectives is weak.
- Cap the conceptual load per section: three Token Capital methods, three TTE principles as
  headlines (others as one-line "also present" footnotes), two or three Foundry objects. The full
  mapping in `TTE-PRINCIPLES-BY-LAB.md` stays as reference, not as slide content.
- Evaluation-first is a curriculum design principle as much as a Token Capital one: the quality,
  cost and speed targets must be set in Section 1 so Section 4 can measure against them. That
  gives the day a spine the old outline lacked: establish the peak (1), detect and climb (2, 3),
  measure and climb again (4). It is the Hill Climbing Model applied to the workshop itself.

### As the content expert

- Token Capital and TTE are complementary, not overlapping. Token Capital states business
  objectives and methods (why and what to optimize); TTE states operating commitments with
  measured verdicts (how, and what the evidence says). The Foundry layer is the mechanism. The
  cleanest bridge per section is: Token Capital method -> TTE principle that operationalizes it ->
  Foundry object that implements it -> the number the lab produces.
- Two places where Token Capital and the TTE evidence pull in different directions, and the
  workshop should say so rather than smooth it over:
  - Token Capital's Model Routing (stage-based routing, cheapest capability) versus TTE a02
    (orchestration lost on cost, reliability and latency). Resolution: routing tiers by stage is a
    model choice inside a workflow you already have a governance reason to build; it is not a
    reason to split one agent into many. Section 3 teaches both sentences together.
  - Token Capital's Compounding Intelligence (retain improvements, organizational memory) versus
    TTE a07 (feed-forward not supported live) and a03 (stale artifacts fail). Resolution: the
    asset compounds only when it is evaluated and kept fresh; an unevaluated lesson or a stale index
    is a liability that looks like an asset. Section 4 teaches this as the honest version of
    compounding.
- The delivery guardrails from the previous outline are correct and should carry over verbatim,
  especially "unknown token usage remains unknown; never convert missing telemetry to zero." That
  rule decides how the cost ledger below is filled in.
- One addition the labs need for this outline to work: a cost ledger. Sections 1 to 3 currently
  log tokens only where the SDK surfaces usage; Section 4 reads `est_cost` from spans. Add a small
  `common/cost_ledger.py` that appends one line per scenario run (section, scenario, agent version,
  input tokens, cached tokens, output tokens, api calls, wall time, gate pass, est_cost or
  "unknown") to `labs/artifacts/cost_ledger.jsonl`, and have each lab driver call it. That file is
  the Token Capital thread through the day and the thing the closing session reads.

### What changed from the previous outline, in one table

| Previous (token-capital-workshop) | This version | Why |
|---|---|---|
| Labs build an app with GitHub Copilot (design, red team, TDD, enhance) | Labs build and operate the hosted agent (`labs/lab1-4`) | Different skill; this room asked for hosted agents |
| Principles grouped by SDLC phase | Principles grouped by what each lab makes concrete | Teach where the hands are |
| Token consumption reviewed at the end of each lab | Cost per outcome ledger with targets set in Section 1 and measured in Section 4 | Evaluation-first and hill climbing need a baseline |
| One slide per principle | Teach = 1 Token Capital slide, 1-2 TTE slides, 1-2 Foundry slides; 15 minutes | Fits the requested flow and time |
| 60-minute sections | 80-minute sections (15 / 55 / 10) | More hands-on time; the labs are already sized for it |
| Copilot-SDLC content | Moved to a companion day or optional 20-minute warm-up in the opening (Copilot critiques `USE-CASE.md`) | Preserves P1/P5 skill practice without doubling scope |

---

## Part B: The outline

### Conventions

- Each section: Teach 15 (slide 1 Token Capital, slides 2-3 TTE, slides 4-5 Foundry), Lab 55
  (demo 10, do 45), Checkpoint and token readout 10.
- Every section ends by appending to `labs/artifacts/cost_ledger.jsonl` and reading one number
  aloud. Unknown stays unknown.
- Continuity chain: `USE-CASE.md` and the Section 1 targets -> `artifacts/lab1/hosted.json` ->
  `artifacts/lab2/knowledge.json`, `hosted.json`, `sessions/` -> `artifacts/lab3/handoff_packets/`,
  `hosted.json` -> `artifacts/lab4/eval_report.md`, `gate_result.json`, `pipeline.md` ->
  `artifacts/stretch5/agents.json` -> `artifacts/stretch6/invocations.json`. Behind: `python
  labs/catch_up.py --through N`.
- Delivery guardrails (carried over): humans own decisions, approvals and accountability; fictional
  data only; no lab action authorizes real claims, payments, production changes or customer
  communication; unknown token usage remains unknown; every participant artifact is reviewable by
  a human before it feeds the next step.

---

### Section 0: Opening (30 min, plus optional 20-minute warm-up)

- Purpose of the day
  - Build the Benefits Marketplace Concierge as Foundry Hosted Agents and leave with a
    deployable, tested, observable agent and the operating model around it
  - Learn to read the day as a hill climb: set the peak, detect the valley, climb, keep climbing
- Business frame (Token Capital, one slide)
  - Token Capital: AI reasoning capacity as organizational capital, not only a technology expense
  - Cost per Outcome: spend measured against successful business results, not raw usage
  - Human Capital and Token Capital: human judgment where it creates distinctive value (the
    licensed advisor), scalable reasoning where it does not (lookup, summary, comparison, routing)
  - The number the day produces: cost per gate-passing scenario, per agent version, in
    `cost_ledger.jsonl`
- Architecture frame (TTE, one slide)
  - Four objectives: Cost, Quality, Governance, Human-Agent Collaboration
  - Ten principles; the day's spine: P1 brief (1), P3 files and freshness (2), P2 and P7 shape and
    gates (3), P4 and P6 acceptance and cost (4)
  - The framework's rule: measured findings decide the claims; the day quotes the conditional and
    refuted ones too
- Engineering frame (Foundry, one slide)
  - Where things run: workstation notebook is the cockpit; `hosted/main.py` is the product; state
    lives outside the container
  - Hosted agent lifecycle: flat ZIP, `azd ai agent init`, `azd up`, version, identity, endpoint
- The use case (`USE-CASE.md`)
  - Two LOBs, one participant journey; the licensed-advisor rule; scenarios S1, S2, S3
- Setup check (`SETUP.md`)
- Optional warm-up (20 min, from the previous outline, P1 and P5 practice)
  - Have GitHub Copilot critique `USE-CASE.md` for gaps and buildability; each learner writes the
    brief for a fourth scenario in the S1-S3 format; keep it for Section 4's golden set
  - Evidence to cite: a specification checklist moved a deceptively simple task from 0% to 90%
    gate-pass (a09)

---

### Section 1: Set the peak. Hosted agent basics (`labs/lab1-hosted-agent-basics/`)

- Teach (15 min)
  - Slide 1, Token Capital: Evaluation-First Development and Human Capital with Token Capital
    - Set the Quality Target: no plan recommendation, no PHI beyond participant id and ZIP, enrollment
      window named when an advisor is offered (these become Section 4's deterministic evaluators)
    - Set the Cost Target and Speed Target: a placeholder the room fills (cost per gate-passing S1
      answer, p95 latency); recorded now, measured in Section 4
    - Preserve Human Judgment: the advisor decides; the agent looks up, explains, hands off
    - The number this section produces: baseline cost and latency for S1 and S2 on v1
  - Slide 2, TTE: P1 Concepts Defined by People
    - The instructions plus `guardrails.COMPLIANCE_INSTRUCTIONS` are one complete written brief,
      versioned with the agent; the brief is the unit of delegation, not the chat
    - Evidence: complete brief beat vague prompting by 51-70% (t10); live, 0% to 92% gate-pass on a
      moderately specified task (a01)
  - Slide 3, TTE: P2 Architecture (one generalist, staged adoption) and P6 right-sizing
    - Default to one capable agent: live, the single agent won cost, reliability and latency
      against orchestration (a02); multi-agent is bought in Section 3 for a stated reason
    - Local process, then dev deployment, then promotion (Section 4): prove each rung
    - `gpt-5.4-mini` by default: the cheap model held 100% on hard work at -73% and the stronger
      model failed a routine contract (a04). Requalify tiers, do not assume
    - Also present: P7 least privilege (Project Manager deploys, Agent Consumer invokes), P8 typed
      tools in Python
  - Slide 4, Foundry: the hosted agent
    - `Agent` + `FoundryChatClient` + `@tool` functions over `benefits_data`; `ResponsesHostServer`;
      `default_options={"store": False}`
    - Flat deployable: `hosted/main.py`, `requirements.txt`, vendored `common/` and `data/`
  - Slide 5, Foundry: deploy and call
    - `azd ai agent init --protocol responses --deploy-mode code --dep-resolution remote_build`,
      `azd up`; version status `active`; per-agent Entra identity
    - `POST /responses` locally; `responses.create(..., agent_reference)` against the deployed
      version; 424 `session_not_ready` and where to read logs
- Lab (55 min)
  - Demo (10): `lab1_hosted_basics.py`: vendoring, `hosted.json`, server on 8088, S1 and S2; read S1
    turn 2 aloud (refusal plus advisor offer, `no_recommendation=OK`); `--deploy` runbook and the
    version in the portal; `test_local.py --deployed`
  - Do (45), `lab1_walkthrough.ipynb` or the driver
    - Run locally; open `transcripts.md`; confirm S1 turn 2 names no plan
    - Write the targets: fill the Quality, Cost and Speed rows in `artifacts/targets.md` (new,
      three lines) from the Slide 1 discussion
    - Keep a server running; call it from the notebook with `post_responses`
    - YOUR TURN: add `get_sponsor` as a fourth tool; restart; ask as P-1001
    - Deploy; wait for `active`; record the version
    - YOUR TURN: tighten one instruction so the advisor offer always names the enrollment window;
      `azd up` a new version; the old version stays
    - YOUR TURN: call the deployed endpoint from the notebook; regenerate transcripts from the cloud
    - Ledger: append S1 and S2 rows for v1 and v2 (tokens where reported, wall time, gate pass;
      unknown stays unknown)
- Checkpoint and token readout (10 min)
  - Paste S1 turn 2 and the `deployed` block of `artifacts/lab1/hosted.json`
  - Read one number: wall time and reported tokens for S1 on v2 versus v1. This is the peak
  - Retrospective question: which instruction change moved the answer, and how would you know
    without reading it?
  - Section 2 reads `artifacts/lab1/hosted.json` and `artifacts/targets.md`

---

### Section 2: Build the asset, watch for the valley. Knowledge and session storage (`labs/lab2-hosted-knowledge-sessions/`)

- Teach (15 min)
  - Slide 1, Token Capital: Build Reusable Intelligence and Convert Consumption into a Durable Asset
    - Reusable Knowledge: the knowledge base is paid for once and consumed by every agent and every
      turn; Controlled Retrieval governs how
    - Organizational Memory: session history and the session map are the participant's continuity
      across restarts, replicas and version rolls
    - Detect the Valley: a stale knowledge base is a durable wrong answer; freshness is part of the
      asset, not an afterthought
    - The number this section produces: prompt tokens per turn with retrieval versus without, and
      continuity across a kill and restart
  - Slide 2, TTE: P3 File-Based Inputs, Evidence and Outputs
    - The prebuilt index: -52/-53% cheaper than re-injecting docs (a03, t11); the reversal: stale
      index failed freshness 0/25 while re-retrieval passed 18/25. Cheaper until it is wrong
    - Per-agent slice: marketplace and accounts sources plus universal docs (t04); scoping pays when
      there is noise to scope out (t03)
    - Freshness duty: `last_reviewed` frontmatter, rebuild schedule, named owner
  - Slide 3, TTE: P6 cache-aware cost and P9 bounded, resumable state
    - Without retrieval, prompt tokens balloon 3,392 to 14,937 as the KB grows; with it they stay
      flat (a03). About 96% of input is cached (H16): report dollars, not tokens
    - State outside the container makes the loop resumable; but durable hand-off machinery cost
      about 2x with no measured reliability gain (a11): keep the session record small and measure
    - Also present: P7 managed identity with Search Index Data Reader only; P1 intent can change
      (stored history must not anchor)
  - Slide 4, Foundry: Foundry IQ knowledge base
    - AI Search index (vector, semantic, Entra embeddings), knowledge sources, knowledge base,
      project connection with `ProjectManagedIdentity`, MCP endpoint
    - `MCPStreamableHTTPTool` with an Entra bearer inside the hosted agent
  - Slide 5, Foundry: session storage for resiliency
    - `common.message_store` (Redis or file) as history provider; `common.session_store` map
    - Kill, restart, resume; `azd env set BENEFITS_KB_MCP_URL`, `BENEFITS_REDIS_URL`; new version, live
      sessions
- Lab (55 min)
  - Demo (10): indexes build while showing `hra-reimbursement-rules.md` and its frontmatter; portal
    knowledge base and connection; server log `knowledge: MCP`, `history:`; turns 1-2 with
    `[KB-MKT-001]`; kill; restart; turn 3 remembers atorvastatin; `continuity check: OK`; open the
    session and message store files
  - Do (45), `lab2_walkthrough.ipynb` or the driver
    - `--build-only`; `knowledge_base.py --demo-only` returns KB-ACC-001 first for the accounts query
    - `--demo-only`; three turns, two pids, `continuity check: OK`
    - Keep a server running; `test_local.py --session S2-harold`; the "best plan" turn refuses
    - YOUR TURN: scale out with Redis and two servers, same session id
    - YOUR TURN: break continuity by pointing the restarted process at an empty store; read the
      warning; restore
    - YOUR TURN: knowledge on and off; without `BENEFITS_KB_MCP_URL` the agent must say the rule text is
      not at hand
    - YOUR TURN (Token Capital addition): detect the valley. Edit `last_reviewed` on one doc to a
      date before today and change one accepted-document line; do not rebuild; ask the question;
      then rebuild and ask again. Write down which answer a participant would have received
    - Ledger: append S1 rows for v2 with and without knowledge; note prompt tokens per turn
  - Optional: deploy v2; `azd up` after a greeting change; sessions survive
- Checkpoint and token readout (10 min)
  - Paste the `continuity check` line with both pids and one citation
  - Read one number: prompt tokens per turn with retrieval versus without
  - Retrospective question: which knowledge doc goes stale first in production, and who owns it?
  - Section 3 reads `artifacts/lab2/knowledge.json` and `hosted.json`

---

### Section 3: Pay for governance, knowingly. Multi-agent triage with advisor handoff (`labs/lab3-hosted-multi-agent-handoff/`)

- Teach (15 min)
  - Slide 1, Token Capital: Human Capital with Token Capital, Model Routing, Secure
    - Combine Rather than Replace: agents gather facts, compare, draft; the licensed advisor decides
    - Stage-Based Routing: intake (cheapest capability), specialists (grounded reasoning), handoff
      packet (best model where the judgment-intensive summary matters). Routing is a model choice
      per stage inside a workflow you already have a reason to build
    - Agent Accountability, Policy Adherence, Tool Permissions: a reviewer with no tools, a packet
      writer with no tools, every action in the log
    - The number this section produces: cost and latency of S1 through the single agent versus the
      workflow, side by side with gate pass
  - Slide 2, TTE: P2 Architecture, orchestration bought for control
    - The framework's biggest reversal: live, the single agent won cost (-45 to -49%), reliability
      (100% vs 68-76%) and latency (-32 to -37%) (a02); no cost crossover as tiers grow (t22)
    - What survives: auditability and role-separated review. The licensed-advisor rule is a
      segregation-of-duties requirement, so we pay, and Slide 1's routing keeps the price down
    - Say it plainly: this section buys governance and the lab measures the price
  - Slide 3, TTE: P7 Human Review Gates and P4 validity versus quality
    - Hard limit: only a licensed advisor closes a case; approve / revise / decline is the gate
    - Stop when confused: revise once, then flag (P9 bounded loop)
    - Externally verified: `contains_recommendation` runs in deterministic Python; a gate the agent
      can influence is not a control. Live, the code gate did not separate from the prompt gate
      (a05): keep it as the backstop, do not credit it for what the prompt already holds
    - `response_format=HandoffPacket` answers "is it a packet"; whether it is good is a separate
      graded question; validity 100% while graded quality 0% happened in one live run (a07)
    - Also present: P8 structured output where it counts (a08); P3 the packet as evidence; P10 the
      reviewer is for segregation, not defect finding (t15, t17)
  - Slide 4, Foundry: the workflow inside the container
    - `WorkflowBuilder` graph; custom `Executor` + `@handler`; fan-out with
      `ctx.send_message(target_id=...)`, counting fan-in; `AgentExecutor` nodes; Pydantic
      `response_format`; per-stage model selection via `FoundryChatClient(model=...)`
  - Slide 5, Foundry: human approval across HTTP turns
    - `ctx.request_info` + `@response_handler` + `workflow.run(responses=...)`; agent middleware
      routes a turn to "start case" or "decision"; pending packet in `common.session_store`;
      `resume_path`
- Lab (55 min)
  - Demo (10): S3 with `--auto-approve`; tail the server log (`intake ... lob=both`, both
    specialists, compliance gate, packet writer); `pending_advisor_approval`, `revise`, `attempts=2`,
    `approve`; open `S3.json`; `--restart-between-turns` on S2 shows `resume_path=session_store`
  - Do (45), `lab3_walkthrough.ipynb` or the driver
    - Run all three scenarios; S1 marketplace, S2 accounts, S3 both; no `options_discussed` names a
      preference
    - YOUR TURN: revise instead of approve on S3; compare `packet_attempts` with a neighbor
    - YOUR TURN: lose the process, keep the case; then with Redis
    - YOUR TURN: make the reviewer earn its keep; add "finish with the single plan you would pick";
      watch `compliant=False` and the send-back
    - YOUR TURN (Token Capital and TTE addition): the price of governance. Run S1 through Section 2's
      single agent and through this workflow; record tokens, api calls, wall time and gate pass for
      both in the ledger; write one sentence on why the workflow is still worth it here
    - YOUR TURN (Token Capital addition): route by stage. Set the intake and specialist model to
      `gpt-5.4-nano` or `-mini` and the packet writer to `gpt-5.4` via env; rerun S1; compare the
      ledger row and the compliance flags with the all-mini run. Cheaper only counts if the gate
      still passes
    - Optional: deploy `benefits-triage-hosted`; `test_local.py --deployed`
- Checkpoint and token readout (10 min)
  - Paste `S3.json`'s `open_questions`, `compliance_flags`, `advisor_decision`
  - Read one number: workflow cost divided by single-agent cost for S1, and the gate pass for each
  - Retrospective question: which step would you remove if the advisor rule did not exist, and what
    would that save?
  - Section 4 reads `artifacts/lab3/hosted.json` and at least one packet

---

### Section 4: Climb. Operate hosted agents (`labs/lab4-operate-hosted-agents/`)

- Teach (15 min)
  - Slide 1, Token Capital: Cost per Outcome, Control, Managed Intelligence, the Hill Climbing Model
    - Measure Successful-Outcome Cost: cost per gate-passing answer, per scenario, per version, from
      the ledger and the spans; compare with the Section 1 targets
    - Usage Visibility, Cost Attribution, Outcome Attribution: per session, per participant, per
      agent version
    - Monitor Performance and Tune Agent Behavior: the evaluation is how you see the valley and how
      you climb; versions, promote and rollback are the climb made safe
    - Compounding Intelligence, the honest version: an improvement compounds only if it is
      evaluated and kept fresh; an unevaluated lesson or a stale index is a liability that looks
      like an asset
    - The number this section produces: cost per successful outcome for the current version against
      the Section 1 target, and the gate result
  - Slide 2, TTE: P4 Acceptance Criteria
    - Deterministic checkers first (no recommendation, PII leak): pass/fail, they gate the release.
      LLM judges (groundedness, relevance) warn; the framework rates the judge a prior (a12)
    - Evidence: a deterministic checker held 25/25 vs 8/25 at scale (t07); stern prompt wording
      caught nothing at +37-44% (t20). Harden the gate, not the prompt
    - Report validity and graded quality as two numbers (a07)
  - Slide 3, TTE: P6 cost observability, P7 verified promotion, P10 honest retrospectives
    - `est_cost` from spans with cache reads and writes priced separately (H16); requalify the model
      tier against the golden set before changing it (a04); backpressure over naive retry against a
      shared quota (a10)
    - The eval gate runs in CI outside the agent's reach; promotion is a human-approved GitHub
      Environment; staged dev, test, prod with rollback (P2)
    - The promising form of a retrospective is exactly this lab: evaluation over logged outcomes
      feeding the next instruction version. Live, feed-forward was not supported (a07, t23): "earn
      it with a graded metric", not "learning loop"
    - Also present: P3 `eval_report.md`, `gate_result.json`, `pipeline.md` as audit evidence
  - Slide 4, Foundry: observe and evaluate the hosted agent
    - `APPLICATIONINSIGHTS_CONNECTION_STRING` on the hosted agent, `configure_azure_monitor`; spans
      from workstation into the container; `azure-ai-evaluation` evaluators plus custom deterministic
      ones; hosted endpoint as the target; optional Foundry eval
  - Slide 5, Foundry: release the hosted agent
    - `eval_gate.py`, `promote.py`, `.github/workflows/agent-ci.yml` (validate, gate, deploy dev,
      smoke, manual promote, rollback); versions blade; rollback by redeploy or version delete
- Lab (55 min)
  - Demo (10): `lab4_operate.py --limit 3`; the tracing env line; Q1-Q3 with `cites`, `ground`,
    `relev`, `norec`, `pii`; `eval_report.md`; `eval_gate.py` PASS; `promote.py --to test` dry run;
    portal Tracing span tree and Versions blade; `agent-ci.yml` beside `pipeline.md`
  - Do (45), `lab4_walkthrough.ipynb` or the driver
    - `--limit 6 --skip-judges`: zero violations, zero PII leaks, citation rate above 0.5
    - Full run with judges; read the two lowest rows; decide whether the agent or the judge is wrong
    - `eval_gate.py`, `promote.py --to test`
    - YOUR TURN: stricter gate with `MustNotEvaluator`
    - YOUR TURN: break it; add "name the plan you think fits best" to the Section 2 instructions;
      `FAIL`, exit 1; revert
    - YOUR TURN: trace one question; count child spans; paste the slowest
    - YOUR TURN (Token Capital addition): cost per outcome. From spans and the ledger, compute
      `est_cost` per gate-passing scenario for the Section 2 agent and the Section 3 workflow; write
      both against the Section 1 cost target in `artifacts/targets.md`; state whether you are at,
      above or below the peak
    - YOUR TURN (Token Capital addition): climb once. Pick the lowest-scoring golden question,
      change one instruction, rerun `--limit 8 --skip-judges`, redeploy as a new version if the gate
      passes, and record the before and after in the ledger. If it did not improve, roll back and
      record that too
    - Optional: deployed target with tracing; `--foundry-eval`
- Checkpoint and token readout (10 min)
  - Paste the `[lab4] summary:` line and the `## Eval gate:` line
  - Read one number: cost per successful outcome for the version you would ship, against the target
  - Retrospective question: which graded metric would prove your instruction change helped, and how
    often would you run it?

---

### Closing (20 min)

- Walk the chain: brief and targets (1), knowledge and memory (2), governed workflow (3), evaluated
  and released (4); one lineage `benefits-concierge-hosted` v1 to vN plus `benefits-triage-hosted`
- Read the ledger as a hill climb: where the peak was set, where the valley appeared (stale
  knowledge, the governance cost), where the climb happened (retrieval, routing, the instruction
  change that passed the gate)
- Token Capital roll-up: which assets now exist (brief, knowledge base with freshness owner, agent
  patterns, shared evaluations, cost ledger) and which Three Strategic Moves the room can make
  Monday (visibility, model tiering, outcome-linked optimization)
- TTE roll-up: what held (P1, P3, P4, P6), what was conditional (P3 freshness, P9 durable state),
  what was a paid trade-off (P2), what remains to be earned (P10)
- Stretch sections and the companion Copilot-SDLC day

---

### Stretch 5: Deploy reasoning across functions. Prompt agents and workflow agents (`labs/stretch5-prompt-agents-and-workflows/`)

- Teach (15 min)
  - Slide 1, Token Capital: Deploy Reasoning Across Functions, Agent Patterns, Prevent Agent Sprawl
    - Business-owned prompt agents let functions deploy reasoning without engineering releases;
      ownership, naming and versioning prevent sprawl
    - Open Architecture: hosted code and platform agents interoperate through `agent_reference`
  - Slides 2-3, TTE: P2 people choose the shape (platform-managed versus hosted, with owners; the
    orchestration caveat repeated for the YAML workflow); P1 the portal instruction history as a
    decision ledger with the override caveat (t01); P8 declarative over imperative as a rule of
    thumb, not harness-measured; P3 the `workflow_action` trail as evidence; P5 configured
    vocabulary (t05)
  - Slides 4-5, Foundry: `PromptAgentDefinition`, `FunctionTool`, `MCPTool`, client-side
    function-call loop; `WorkflowAgentDefinition` YAML, streaming `workflow_action`; the hosted
    `run_triage_workflow` tool
- Lab (55 min): the existing demo and do steps; add a ledger row for S1 through the platform
  workflow to compare with Sections 2 and 3
- Checkpoint and token readout (10 min): the `workflow_action` trail; cost of the platform workflow
  versus the hosted one; which agents the business should own

---

### Stretch 6: Cheapest capability, reusable intelligence. Invocations, Toolbox, Skills (`labs/stretch6-invocations-toolbox-skills/`)

- Teach (15 min)
  - Slide 1, Token Capital: Model Routing (Cheapest Capability for high-volume, limited-judgment
    work), Shared Prompts and Reusable Knowledge as Skills, Stage-Based Routing for batch
  - Slides 2-3, TTE: P2 toolsets, deterministic over clever (t09, t07); P4 schema gate; P8
    structured in and out (a08); P3 `SKILL.md` as a Team Brain artifact with a freshness duty (a03);
    P6 progressive disclosure, measured not assumed (t02); P7 the web_search boundary; P9 bounded,
    stateless loop
  - Slides 4-5, Foundry: `InvocationsHostServer`, `response_format=ClaimReviewBatch`,
    `claims_review.py`; `skills/<name>/SKILL.md`, `read_skill`; Toolbox over MCP (preview); two
    protocols, one deploy path
- Lab (55 min): the existing demo and do steps; add a ledger row for the batch run per claim
- Checkpoint and token readout (10 min): CLM-9003 explanation; cost per reviewed claim; which
  facts must never come from the model

---

## Part C: Build list before delivery

- `common/cost_ledger.py` and a `ledger` call in each lab driver; `labs/artifacts/cost_ledger.jsonl`
- `labs/artifacts/targets.md` template (Quality, Cost, Speed rows) written in Section 1, read in
  Section 4
- Per-stage model selection via env in Section 3's `hosted/benefits_specialists.py`
  (`BENEFITS_MODEL_INTAKE`, `BENEFITS_MODEL_SPECIALIST`, `BENEFITS_MODEL_HANDOFF`)
- The four Token Capital YOUR TURN items added to the Section 2, 3 and 4 READMEs
- Slide deck: 5 teach slides per section on the three-rung ladder visual, one demo/lab slide per
  section, opening and closing decks; the deck follows the previous outline's rule that slides
  guide the conversation and speaker notes guide the facilitator
- Run the `SETUP.md` smoke test the day before; check the `# VERIFY` list in the writer-notes files
