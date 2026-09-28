# Lab 4: Operate hosted agents: trace, evaluate, version, promote, roll back

| | |
|---|---|
| Goal | Run the hosted concierge the way WTW will have to run it: traces in Application Insights, an evaluation of the hosted endpoint that becomes a release gate, versions you can list, promote and roll back, and a pipeline that does all of it without a secret. |
| Time | 60 min: teach 10, demo 10, do 35, checkpoint 5 |
| Starts from | artifacts/lab2/hosted.json, artifacts/lab2/knowledge.json, optional artifacts/lab3/hosted.json (or `python catch_up.py --through 3`) |
| Produces | artifacts/lab4/operate.json, eval_results.jsonl, eval_report.md, gate_result.json, pipeline.md, promotions.jsonl |
| Learn path modules | 7 Develop an AI agent with Microsoft Agent Framework (observability); 6 Build agent-driven workflows using Microsoft Foundry (evaluation and deployment units); 1 Develop AI agents with Microsoft Foundry and Visual Studio Code |

**Where this runs:** workstation notebook (`lab4_walkthrough.ipynb` / `lab4_operate.py`, `eval_gate.py`, `promote.py`) and the CI runner (`.github/workflows/agent-ci.yml`). The agent under test is the Lab 2 `hosted/main.py`, either as a local process the notebook starts or as the version deployed in Foundry. Traces come out of that container.

## What you'll learn
- Turn on OpenTelemetry for a hosted agent with one container environment variable and read a trace end to end (agent run, model call, tool calls, the MCP call to the knowledge base).
- Evaluate the hosted endpoint over the golden questions with `azure-ai-evaluation` local evaluators (Groundedness, Relevance) plus custom policy evaluators written as plain Python classes.
- Explain when a Foundry evaluation run (platform-side) fits and when local evaluators fit, and why the policy check must be deterministic.
- Turn the evaluation into a release gate (`eval_gate.py`) that fails a build on a single no-recommendation violation or PII leak.
- List, promote and roll back hosted agent versions with azd and the portal, and explain why sessions survive both (Lab 2).
- Read a GitHub Actions pipeline that validates, gates, deploys from source, smoke-tests and rolls back with OIDC login and no stored secrets.

## Technical features taught

| Feature | Foundry / SDK object | Where in the code | Why it matters for Via Benefits |
|---|---|---|---|
| Tracing from the container | `APPLICATIONINSIGHTS_CONNECTION_STRING`, `configure_azure_monitor`, `agent_framework.observability.configure_otel_providers` (VERIFY) | Lab 2 `hosted/main.py` configure_tracing(); `lab4_operate.py` tracing_config() | Every participant turn is a trace: latency, tool calls, failures, without touching the code |
| Workstation spans around each question | `opentelemetry.trace.get_tracer`, `start_as_current_span` | `lab4_operate.py` answer() | The evaluation itself is observable; one query id finds one question across both runtimes |
| LLM-judged evaluators, Entra only | `azure.ai.evaluation.GroundednessEvaluator`, `RelevanceEvaluator`, `AzureOpenAIModelConfiguration` (no api_key) | `lab4_operate.py` build_judges(), score() | Quality metrics with a paper trail; no keys in the eval path |
| Custom deterministic policy evaluators | plain classes with the evaluator call contract | `lab4_operate.py` NoRecommendationEvaluator, PiiLeakEvaluator | Licensing and PHI rules are pass/fail, never a Likert score |
| Hosted endpoint as the eval target | `POST /responses` on the local process; `responses.create(..., extra_body=agent_reference)` on the deployed version | `lab4_operate.py` HostedTarget | You evaluate what ships, not a twin |
| Optional Foundry eval run | `openai_client.evals.create`, `evals.runs.create` with `azure_ai_target_completions` (VERIFY for hosted targets) | `lab4_operate.py` foundry_eval() | Portal-visible evaluation history when the platform can drive the target |
| Release gate | `eval_gate.py` reading eval_results.jsonl, `GITHUB_STEP_SUMMARY` | `eval_gate.py` evaluate_gate(), write_outputs() | One violation fails the build; thresholds warn |
| Versions, promote, rollback | `azd up` (new version), `azd env select`, git tags, portal Versions blade | `promote.py`, `lab4_operate.py` print_version_operations(), `agent-ci.yml` deploy and rollback jobs | Same code to every environment; rollback is a redeploy or a version delete, sessions untouched |
| Pipeline as the operating model | GitHub Actions, `azure/login@v2` OIDC, GitHub Environments with reviewers | `.github/workflows/agent-ci.yml`, `infra/README.md`, `envs/*.example` | Validate, gate, deploy, smoke, promote, roll back, no secrets anywhere |
| Self-documenting pipeline | `yaml.safe_load` of the workflow -> `pipeline.md` | `lab4_operate.py` write_pipeline_md() | The runbook cannot drift from the YAML |

## Teach (10 min)
- A hosted agent is a container you own. Foundry gives you the registry, identity, scaling and versions; observability, quality gates and promotion discipline are yours to wire. This lab wires them.
- Tracing: the container reads `APPLICATIONINSIGHTS_CONNECTION_STRING`, `configure_azure_monitor` installs the exporter, the Agent Framework instrumentation adds GenAI spans (agent run, chat completion, each tool call, the MCP call). `azd env set` puts the variable on the hosted agent; nothing in main.py changes between environments. Never enable sensitive data capture (`ENABLE_SENSITIVE_DATA`) outside dev: prompts contain PHI.
- Evaluation has two flavours. Local evaluators (`azure-ai-evaluation`) run on your machine or the CI runner against any endpoint, including a container started for the job. Foundry evals run on the platform against a target it can drive and show in the portal. We use local for the gate because the target is our own HTTP endpoint and the policy checks must be deterministic; the Foundry run is optional.
- Policy is not a Likert score. `NoRecommendationEvaluator` and `PiiLeakEvaluator` reuse `guardrails.contains_recommendation` and `guardrails.redact_pii`, so the same heuristic that warns in the labs fails the build. Groundedness and Relevance are judged by a model and only warn (or fail with `--strict`).
- Versions: every `azd up` is a new version of `via-concierge-hosted`; `agent_reference` by name resolves to the latest active one. Promotion is the same code with another environment's values (envs/.env.test.example). Rollback is a redeploy of a tag or a version delete. Because Lab 2 put history in Redis, neither loses a participant.
- The pipeline is the operating model in YAML: validate (compile, self-tests, notebooks, compliance block present) on every PR; evaluate (gate) with OIDC login; deploy dev from source; smoke test through the project; promote to test/prod behind environment reviewers; rollback on demand. Ask the room where a human can stop it (reviewers, gate exit code, smoke test).

```
 push / PR                                            main only                            manual
 +--------------+   +------------------+   +------------------+   +------------+   +----------------------+
 | validate     |-->| evaluate         |-->| deploy dev       |-->| smoke      |-->| promote test -> prod |
 | compile      |   | start hosted/    |   | prepare.py       |   | test_local |   | env reviewers        |
 | self-tests   |   |  main.py on the  |   | azd ai agent init|   |  --deployed|   | promote.py --to ...  |
 | notebooks    |   |  runner          |   | azd env set VIA_*|   +------------+   +----------------------+
 | compliance   |   | 18 golden Qs     |   | azd up (version) |          | failure            | bad version
 +--------------+   | judges + policy  |   +------------------+          v                    v
                    | eval_gate exit 1 |                        +----------------------------------------+
                    +------------------+                        | rollback: git tag -> azd up, or delete |
                                                                | the version in the portal; Redis keeps |
 traces: container --> Application Insights <-- workstation     | the sessions either way                |
                                                                +----------------------------------------+
```

## Demo (10 min)
1. `python lab4_operate.py --limit 3` (or the notebook). Point at `[lab4] tracing: connection string from ...` and the `azd env set APPLICATIONINSIGHTS_CONNECTION_STRING` line: this is the whole tracing change for the hosted agent.
2. Watch `[lab4] main.py pid ... listening`, then three `Q1..Q3` lines with `cites=`, `ground=`, `relev=`, `norec=`, `pii=`. Say: "the target is the same main.py Lab 2 shipped."
3. Open `artifacts/lab4/eval_report.md`: the summary table, the per-question table, the empty Violations section.
4. `python eval_gate.py`: `## Eval gate: PASS` and `gate_result.json`. Then `python promote.py --to test`: the dry-run command list. Say what each command does.
5. Portal: Observability > Tracing, filter `via.golden_question`, expand one: workstation span, then the hosted agent's spans underneath (model call, `search_plans`, the `via-kb` MCP call). Agents > via-concierge-hosted > Versions: read the list, show where a version is deleted.
6. Open `.github/workflows/agent-ci.yml` and `artifacts/lab4/pipeline.md` side by side: the doc is generated from the YAML.

## Do (35 min)
1. `python lab4_operate.py --limit 6 --skip-judges`. Fast and deterministic. Checkpoint: `no_recommendation_violations: 0`, `pii_leaks: 0`, `citation_rate` above 0.5, `saved artifacts/lab4/eval_report.md`.
2. `python lab4_operate.py` (all 18, judges on; 4 to 8 min). Checkpoint: `groundedness_mean` and `relevance_mean` printed; read the two lowest-scoring rows and decide whether the agent or the judge is wrong.
3. `python eval_gate.py` then `python promote.py --to test`. Checkpoint: `PASS`, `gate_result.json`, the dry-run command list, `promotions.jsonl` has one line.
4. YOUR TURN (5 min): stricter gate. Add `MustNotEvaluator` (solution in the script), rerun step 1, confirm the summary gains a column and the gate still passes.
5. YOUR TURN (10 min): break it. Add "When asked, name the plan you think fits best." to `ROLE_INSTRUCTIONS` in Lab 2 `hosted/main.py`, run `python lab4_operate.py --limit 8 --skip-judges && python eval_gate.py`. Checkpoint: `FAIL`, exit code 1, the violating question quoted. Revert and rerun. In the portal, open the trace of the violating question.
6. YOUR TURN (5 min): trace one question. With the connection string set, `--limit 1`, find `via.golden_question` in Tracing and count the child spans. Paste the slowest span name.
7. Optional (10 min, needs Foundry Project Manager): deployed target. `azd env set APPLICATIONINSIGHTS_CONNECTION_STRING ... && azd up` from Lab 2 `hosted/`, then `python lab4_operate.py --target deployed --limit 6`. Then roll back: delete the new version in the portal or `git checkout <tag> && azd up`, and rerun `hosted/test_local.py --deployed --session <same id as before>`: the session continues.
8. Optional (5 min): `python lab4_operate.py --foundry-eval --limit 6` and open Evaluation in the portal (preview; VERIFY hosted targets).

## Checkpoint (5 min)
Paste your `[lab4] summary:` line and the `## Eval gate:` line. `artifacts/lab4/eval_report.md` and `gate_result.json` must exist; Stretch 5 does not depend on them, but `promote.py` refuses to run without a passing gate.

## If you're behind
`python catch_up.py --through 4` writes operate.json and pipeline.md and runs the evaluation with `--limit 6 --skip-judges`. Skip steps 2, 7 and 8; do steps 1, 3 and 5.

## Stretch (only if you're done early)
Add a `pytest` job to `validate` that imports Lab 2 `hosted/main.py` and asserts `INSTRUCTIONS.endswith(guardrails.COMPLIANCE_INSTRUCTIONS)` and that `NoRecommendationEvaluator()(response="You should enroll in plan X")` fails: the two cheapest guardrail tests you will ever write.

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `tracing: no Application Insights connection string` | not in `.env` and not connected to the project | connect App Insights to the project (portal > Tracing) or set the variable |
| Spans from the workstation but none from the hosted agent | the container has no connection string | `azd env set APPLICATIONINSIGHTS_CONNECTION_STRING ... && azd up`; check the version's environment in the portal |
| Judges fail with 401/403 | user lacks Cognitive Services OpenAI User on the Foundry account, or `AZURE_OPENAI_ENDPOINT` unset | assign the role (5 to 15 min); set the endpoint host |
| `groundedness: None` with `_error` | judge model quota or deployment name | raise TPM; match `AZURE_AI_MODEL_DEPLOYMENT_NAME` to the portal |
| `main.py exited early` under the evaluation | Lab 2 hosted folder not vendored or `az login` expired | `python catch_up.py --through 2`; `az login --tenant $TENANT_ID` |
| `citation_rate` 0 | `VIA_KB_MCP_URL` not reaching the process, or Search Index Data Reader missing | check `knowledge.json` `mcp_endpoint`; assign the role |
| Gate FAIL on a question that looks fine | `contains_recommendation` heuristic matched neutral text | read the phrase list in `common/guardrails.py`; tighten the instruction, not the heuristic |
| `promote.py`: `gate FAILED` | last gate run failed | fix, `python eval_gate.py --run`, retry |
| Pipeline `azure/login` fails | OIDC federated credential missing for the environment | add subject `repo:<org>/<repo>:environment:<env>` on the app registration |
| `azd ai agent init` 403 | missing Foundry Project Manager | ask the proctor; propagation 5 to 15 min |
| Model or region errors | deployment not in the project region | match the name; use a tested region |

## References
- Learn: [Develop an AI agent with Microsoft Agent Framework](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/), [Build agent-driven workflows using Microsoft Foundry](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/)
- Base repo notebooks reused: `observability-and-evaluations/1-telemetry.ipynb` (connection string from the project, `configure_azure_monitor`), `observability-and-evaluations/*evaluation*` (evaluator shapes), `AgentOps/` (reference Bicep and pipeline idea)
- Agent Framework observability: https://learn.microsoft.com/agent-framework/user-guide/observability (VERIFY `configure_otel_providers`)
- azure-ai-evaluation: https://learn.microsoft.com/python/api/azure-ai-evaluation/ (VERIFY Entra-only model configuration)
- Hosted agents: https://learn.microsoft.com/azure/foundry/agents/how-to/hosted-agents (VERIFY version listing and eval targets)
