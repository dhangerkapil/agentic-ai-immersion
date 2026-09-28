# WRITER NOTES: Agent 1 (Hosted-Agents focus restructure)

Scope per BRIEF-hosted-focus: `tools/py_to_ipynb.py`, `labs/lab2-hosted-knowledge-sessions/`,
`labs/lab4-operate-hosted-agents/`, `labs/stretch5-prompt-agents-and-workflows/`, `labs/README.md`,
`labs/catch_up.py`, `labs/lab_helpers.py`, `labs/requirements.txt`, `labs/artifacts/README.md`, `SETUP.md`,
`USE-CASE.md`, `data/`, `common/` (docstrings only; no code changes), this file.

## What I verified (ran here)
- `python -m py_compile` on every `.py` I own: passes.
- `python -m json.tool` on every `.ipynb` and `data/*.json`; `golden_questions.jsonl` parses line by line.
- `tools/py_to_ipynb.py --check` on the three generated notebooks (and on Agent 2's `lab1_hosted_basics.py`
  as a smoke test of the converter against a script I did not write: 11 code + 3 markdown cells).
- `yaml.safe_load` on `agent-ci.yml` (jobs validate, evaluate, deploy, rollback) and on the rendered
  `benefits_triage_workflow.yaml` (kind workflow, 9 top-level actions).
- `python common/benefits_data.py` (ALL CHECKS PASSED), `python common/session_store.py` (PASS),
  `python common/message_store.py` (PASS), `python common/foundry_env.py`.
- `hosted/prepare.py` vendors `common/` (6 files incl. session_store and message_store) and `data/` (18 files),
  `--clean` removes them. `.vendored` marker deleted afterwards so the folder ships clean.
- `eval_gate.py` on a hand-written two-row results file: FAIL with exit 1 on the violation row, `gate_result.json`
  written; `promote.py --to test` refuses on a failed gate. `lab4_operate.write_pipeline_md()` generates
  `pipeline.md` from the workflow YAML.
- `catch_up.py --only 6` prints the friendly SKIP for a module that does not exist yet; `--only 2` reports
  SKIP (no Azure SDKs in this environment) instead of a traceback.
- `hosted_tool_snippet.py` imports and prints the tool name without agent_framework or pydantic installed.
- Emoji / em-dash scan over every owned file: 0 hits. No stale "Option A/B/C" or old folder-name references in
  owned files.
- Nothing installed. Nothing written into Agent 2's folders or into the old `WTW-Agentic-AI-Immersion-Labs`.
- Deleted from the new folder after reuse: `lab1-prompt-agent-tools/`, `lab2-knowledge-foundry-iq/`,
  `lab3-multi-agent-workflow/`, `stretch5-evaluate-and-observe/`.

## Not runnable here (no Azure, no SDKs): needs a live run before delivery
- Lab 2 end to end: knowledge base build (unchanged code from the earlier lab2 `knowledge_base.py`, only the
  chain check moved from `lab1/agent.json` to `lab1/hosted.json`), the subprocess start/kill/restart demo and
  the continuity check. Lab 4 evaluation against the local process. Stretch 5 agent creation and the S1 run.

## VERIFY tags (every one is a comment in the code at the call site)
| Where | What to verify | Docs |
|---|---|---|
| `lab2/hosted/main.py` EntraBearerAuth, knowledge_tool() | `MCPStreamableHTTPTool(name, url, http_client)` keyword names; that httpx runs the sync `auth_flow` for `AsyncClient`; the retrieval tool shows up as `knowledge_base_retrieve` | learn.microsoft.com/agent-framework (MCP tools) |
| `lab2/hosted/main.py` build_message_store() / agent_kwargs_for_store() | the history provider from `common.message_store` is accepted in `Agent(context_providers=[...])` and is keyed by the session id the host server passes | learn.microsoft.com/agent-framework/user-guide/agents/conversation-storage |
| `lab2/hosted/main.py` configure_tracing(), `lab4_operate.py` | `agent_framework.observability.configure_otel_providers` name and behaviour after `configure_azure_monitor` | learn.microsoft.com/agent-framework/user-guide/observability |
| `lab2/hosted/main.py` `__main__`, `lab2_hosted_knowledge.py` ask(), `hosted/test_local.py` call_local() | how `ResponsesHostServer` surfaces a session / conversation id: we send `conversation: <session id>` in the Responses body and, as fallback, `previous_response_id`; `run(port=...)` for a non-default port | learn.microsoft.com/azure/foundry/agents/how-to/hosted-agents |
| `lab2_hosted_knowledge.py` azd_commands(), `lab4/infra/README.md` | `azd env set` values become container environment through the `agent.yaml` environment block | same |
| `lab4_operate.py` build_judges() | `AzureOpenAIModelConfiguration` without `api_key` authenticates with `DefaultAzureCredential` | learn.microsoft.com/python/api/azure-ai-evaluation |
| `lab4_operate.py` foundry_eval() | a hosted (Responses) agent as an `azure_ai_agent` eval target by name | learn.microsoft.com/azure/foundry/how-to/develop/agent-evaluate-sdk |
| `lab4_operate.py` print_version_operations() | the `azd` azure.ai.agents subcommand that lists versions (`azd ai agent show` is a guess, marked) | hosted-agents how-to |
| `lab4_operate.py` tracing_config() | `project.telemetry.get_application_insights_connection_string()` | trace-agents-sdk how-to |
| `knowledge_base.py` (moved, unchanged) | `vectorizer_name` / `algorithm_configuration_name` keywords on 11.7.0b2; `create_or_update_knowledge_source` method name | azure-search-documents reference |
| `stretch5_prompt_agents.py` knowledge_tool(), `benefits_triage_workflow.yaml` | `project_connection_id` accepts the connection resource id; Power Fx helpers in the workflow YAML (preview) | workflows how-to |

## Design decisions the orchestrator should know
- **Lab 2 message store**: coded against Agent 2's actual `common/message_store.py` (landed while I was writing):
  `get_message_store(dir)` + `as_history_provider(store)` for the file store, `build_history_provider(dir)` for
  Redis (returns the framework's `RedisHistoryProvider`). If the module is missing at import, `main.py` prints a
  WARNING and runs with in-process memory, so the continuity check fails visibly instead of crashing.
- **Session id over HTTP**: the local demo sends the session id as the OpenAI `conversation` field. If the host
  server ignores it the continuity check fails and the script says why. The client-side session map records
  whatever `conversation` / `id` the server returns, so a server-generated id would also be picked up.
- **Notebook generation**: `py_to_ipynb.py` rewrites `Path(__file__)` to a cwd-based fallback and guards
  `if __name__ == "__main__":` so the kernel does not run argparse; a closing Markdown cell tells the learner to
  call `build()` / `demo()`. `--keep-script-semantics` disables both. Module docstrings inside a Markdown cell
  render as a fenced text block so the aligned Goal / Inputs / Outputs layout survives. Agent 2 can regenerate
  their notebooks with the same command: `python tools/py_to_ipynb.py <script.py> --name labN_walkthrough`.
- **Lab 4 pipeline order** follows the brief (validate -> eval gate -> deploy dev -> smoke -> promote -> rollback):
  the evaluate job starts Lab 2 `hosted/main.py` on the runner (`--target local`) so the gate runs before any
  deployment. `pipeline.md` is generated from the YAML by `lab4_operate.build()` so it cannot drift.
- **Lab 4 chain check** on `artifacts/lab3/hosted.json` is soft (Lab 3 is Agent 2's; Lab 4 targets the Lab 2
  agent). Hard requirement is `artifacts/lab2/hosted.json` + `knowledge.json`.
- **Stretch 5 line budget**: 319 lines by moving the workflow YAML into `benefits_triage_workflow.yaml` (96 lines,
  brace placeholders rendered by `render_workflow()`) and shortening the instruction strings. All six agents still
  end with `guardrails.COMPLIANCE_INSTRUCTIONS` (asserted in `build()`).
- **Lab 4 line count** is 409 (brief says 150-400 for core labs); the extra is the optional Foundry eval block and
  the version-operations print. Trim `foundry_eval()` if the budget is strict.
- `labs/stretch6-agentops-hosted/` (Agent 2's earlier in-progress folder) contained only two empty directories
  (`envs/`, `infra/`) when I read it; Lab 4 was adapted from the old option-B `stretch6-agentops` and option-C
  `stretch5-hosted-and-agentops` instead. The empty folder is Agent 2's to remove.
- `common/__init__.py` `__all__` now lists `session_store` and `message_store` (docstring/metadata only).

## Open risks
- The `hosted/requirements.txt` for Lab 2 includes `redis` and `azure-monitor-opentelemetry` so the same image
  serves the Redis YOUR TURN and Lab 4 tracing; confirm `remote_build` accepts unpinned names on the day.
- Judges: 18 questions x (1 agent call + 2 judge calls) on `gpt-5.4-mini`; raise TPM before the room runs Lab 4.
- The `ruff` step in `agent-ci.yml` lints the whole folder, including Agent 2's files; expect E402 noise is
  already suppressed with `# noqa` in my files.
- The Lab 4 evaluate job rebuilds `artifacts/lab2` with `catch_up.py --through 2`, which re-runs the knowledge
  base build (idempotent create_or_update, 1 to 2 min, embeddings cost) on every push. Cache or gate it if that
  is too much.
