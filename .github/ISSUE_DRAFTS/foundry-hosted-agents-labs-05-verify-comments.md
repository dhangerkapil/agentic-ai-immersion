---
title: "foundry-hosted-agents-labs: resolve every # VERIFY comment against current Foundry / Agent Framework docs"
labels: enhancement, foundry-hosted-agents-labs, needs-azure-access
---

## Context

Part of the Foundry Hosted Agents labs merge (`foundry-hosted-agents-labs/`). Issues are
disabled on this repo, so this is filed as a drafted issue instead; open a real issue from this
file's content once issues are available, then delete this file.

## Gap

Nothing in this lab sequence ran against a live Foundry project during authoring. Every uncertain
API call is marked with a `# VERIFY` comment at the call site, and both writer-notes files
(`WRITER-NOTES-agent1.md`, `WRITER-NOTES-agent2.md` — kept outside the repo, in the OneDrive source
folder, not copied in) list them. This merge PR ran everything that does not need Azure (data/store
self-tests, `py_compile`, notebook regeneration) but did **not** validate any of the items below
against a live project or current docs.

## Ask

Grep `VERIFY` across `foundry-hosted-agents-labs/` and confirm each item against current
learn.microsoft.com Foundry / Agent Framework docs (or a live project), fixing the call site if the
API differs from what's assumed:

**From WRITER-NOTES-agent1.md:**
- `lab2/hosted/main.py` `EntraBearerAuth`, `knowledge_tool()` — `MCPStreamableHTTPTool(name, url, http_client)` keyword names; sync `auth_flow` under `httpx.AsyncClient`; tool surfaces as `knowledge_base_retrieve`
- `lab2/hosted/main.py` `build_message_store()` / `agent_kwargs_for_store()` — history provider from `common.message_store` accepted via `Agent(context_providers=[...])`, keyed by session id
- `lab2/hosted/main.py` `configure_tracing()`, `lab4_operate.py` — `agent_framework.observability.configure_otel_providers` name/behavior after `configure_azure_monitor`
- `lab2/hosted/main.py` `__main__`, `lab2_hosted_knowledge.py` `ask()`, `hosted/test_local.py` `call_local()` — how `ResponsesHostServer` surfaces a session id (`conversation: <session id>` vs `previous_response_id`); `run(port=...)` for non-default port
- `lab2_hosted_knowledge.py` `azd_commands()`, `lab4/infra/README.md` — `azd env set` values flow into the container via the `agent.yaml` environment block
- `lab4_operate.py` `build_judges()` — `AzureOpenAIModelConfiguration` without `api_key` authenticates via `DefaultAzureCredential`
- `lab4_operate.py` `foundry_eval()` — a hosted (Responses) agent as an `azure_ai_agent` eval target by name
- `lab4_operate.py` `print_version_operations()` — the actual `azd` `azure.ai.agents` subcommand that lists versions (`azd ai agent show` is a guess, marked as such)
- `lab4_operate.py` `tracing_config()` — `project.telemetry.get_application_insights_connection_string()`
- `knowledge_base.py` — `vectorizer_name` / `algorithm_configuration_name` keywords on `azure-search-documents` 11.7.0b2; `create_or_update_knowledge_source` method name
- `stretch5_prompt_agents.py` `knowledge_tool()`, `benefits_triage_workflow.yaml` — `project_connection_id` accepts a connection resource id; Power Fx helpers in the workflow YAML (preview)

**From WRITER-NOTES-agent2.md:**
- `common/message_store.py` `message_from_dict` — `Message.from_dict` existence (SerializationMixin); text-only fallback
- `common/message_store.py` `as_history_provider` — `BaseHistoryProvider` as base class of `RedisHistoryProvider` with async `get_messages`/`add_messages`/`clear` keyed by `session_id`; `BaseContextProvider` fallback import
- `common/message_store.py` `build_history_provider` — `RedisHistoryProvider(key_prefix=...)` key format `<prefix>:<session_id>`; whether `max_messages` exists on it
- `common/session_store.py` Cosmos store — `CosmosClient(url, credential=TokenCredential)`, `query_items(enable_cross_partition_query=True)`
- Lab 1 / 3 / S6 `post_responses`, `call_local` — `POST /responses` path; session id surfacing; `run(port=...)` for non-default port
- Lab 3 `hosted/main.py` `triage_router` — agent middleware signature `(context, call_next)`, `context.messages`, `context.session.session_id`; short-circuit via `context.result` without `await call_next()`
- Lab 3 `hosted/benefits_workflow.py` — `AgentExecutorResponse.executor_id`; `AgentExecutor(agent, id=...)`; `FileCheckpointStorage`/`with_checkpointing` (only if Stretch attempted)
- Lab 3 `hosted/benefits_specialists.py` `knowledge_tool` — `MCPStreamableHTTPTool(name, url, http_client=httpx.AsyncClient(auth=...))` for Lab 2's KB when `BENEFITS_KB_MCP_URL` is set
- S6 `hosted-invocations/test_local.py`, `stretch6_invocations.py` — the path `InvocationsHostServer` serves (`/invocations` assumed; `/invoke`, `/` tried); response envelope shape
- S6 `hosted-responses-skills/main.py` `toolbox_tool` — Toolbox MCP URL (`TOOLBOX_MCP_URL`, never derived), token scope `https://ai.azure.com/.default`, `_ping_available` attribute name; Foundry Toolbox and Skills are preview and the README must keep saying so

## Note

Keep every preview feature (Toolbox, Skills, Power Fx workflow helpers) labeled preview in
READMEs/comments even after verification, per the workshop's existing convention.
