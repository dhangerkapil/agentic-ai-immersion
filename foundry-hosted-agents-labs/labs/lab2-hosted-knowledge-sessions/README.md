# Lab 2: Hosted agent with Foundry IQ knowledge and external session state

| | |
|---|---|
| Goal | Give the hosted concierge a governed knowledge base over MCP and move its conversation history out of the container, so a restarted process, a new version or a second replica continues the participant's conversation. |
| Time | 60 min: teach 10, demo 10, do 35, checkpoint 5 |
| Starts from | artifacts/lab1/hosted.json (or `python catch_up.py --through 1`) |
| Produces | artifacts/lab2/knowledge.json, artifacts/lab2/hosted.json, artifacts/lab2/sessions/, artifacts/lab2/transcripts.md |
| Learn path modules | 4 Build knowledge-enhanced AI agents with Foundry IQ; 3 Integrate MCP Tools with Azure AI Agents; 7 Develop an AI agent with Microsoft Agent Framework |

**Where this runs:** both. `lab2_walkthrough.ipynb` / `lab2_hosted_knowledge.py` run on your workstation (build the knowledge base, start and kill the local server, call it, print the azd runbook). `hosted/main.py` is the container Foundry runs; locally it is the same file as a process on port 8088.

## What you'll learn
- Build a Foundry IQ knowledge base (two indexes, two knowledge sources, one KB) from Markdown documentation and expose it over MCP with a project connection, Entra only.
- Attach that knowledge base to an in-process Agent Framework agent with `MCPStreamableHTTPTool` and an httpx auth class that injects the container's own Entra token.
- Explain why a hosted agent container must be stateless, and what state has to live outside it (message history, the session map).
- Wire `common.message_store` (Redis or file) and `common.session_store` into the agent so history is keyed by session id, not by process.
- Prove resiliency: two turns, kill the process, restart, third turn depends on memory. Then explain why the same mechanism makes version rolls and scale-out safe.
- Deploy a new version of the hosted agent from source with `azd` and pass configuration through environment variables, never through code.

## Technical features taught

| Feature | Foundry / SDK object | Where in the code | Why it matters for Benefits Marketplace |
|---|---|---|---|
| Foundry IQ knowledge base from Markdown | `SearchIndex`, `SearchIndexKnowledgeSource`, `KnowledgeBase`, `create_or_update_knowledge_base` | `knowledge_base.py` build_index(), build_knowledge_sources(), build_knowledge_base() | The customer's Word-to-Markdown docs become one governed retrieval surface per bounded context (marketplace, accounts) |
| Vector + semantic index, Entra embeddings | `AzureOpenAIVectorizer`, `SemanticSearch`, `get_bearer_token_provider` | `knowledge_base.py` index_definition(), make_embedder() | No keys in the index pipeline; query-time embeddings by the search service identity |
| Project connection for the KB MCP endpoint | ARM PUT `.../connections/benefits-kb-connection` (authType ProjectManagedIdentity) | `knowledge_base.py` create_project_connection() | Platform agents and hosted agents call the same governed endpoint; the portal shows who may reach it |
| In-process MCP tool with Entra bearer | `MCPStreamableHTTPTool(name, url, http_client)`, `httpx.Auth` subclass | `hosted/main.py` EntraBearerAuth, knowledge_tool() | The container's managed identity reads the KB; Search Index Data Reader is the only grant needed |
| Function tools over systems of record | `@tool(approval_mode="never_require")`, `Annotated[..., Field]` | `hosted/main.py` get_participant .. compare_plans | Tools stay pure Python over benefits_data; swapping in the real systems is a one-file change |
| Stateless container, external history | `Agent(..., context_providers=[provider], default_options={"store": False})` | `hosted/main.py` build_message_store(), build_agent() | History travels with the session id: any replica or a restarted version continues the call |
| Message store backends | `common.message_store.get_message_store`, `as_history_provider`, `RedisHistoryProvider` | `common/message_store.py`, `hosted/main.py` | Redis for N replicas and TTL; files for one laptop; same code path |
| Session map | `common.session_store.get_session_store`, `SessionRecord` | `hosted/main.py` record_session(), `lab2_hosted_knowledge.py` record_turn() | The client's one fact to never lose: session -> conversation, last response id, turn count |
| Local run as a process, same file as the container | `ResponsesHostServer(agent).run()`, `subprocess.Popen` | `hosted/main.py` `__main__`, `lab2_hosted_knowledge.py` start_server(), stop_server() | The demo kills the process on purpose; Foundry does the same thing to you on every version roll |
| Deploy from source, env-driven config | `azd ai agent init --deploy-mode code --dep-resolution remote_build`, `azd env set`, `azd up` | `lab2_hosted_knowledge.py` azd_commands(), print_deploy() | No Dockerfile, no secrets: `BENEFITS_KB_MCP_URL` and `BENEFITS_REDIS_URL` arrive as container environment |

## Teach (10 min)
- Lab 1 gave you a hosted agent that answers from tools. Two things are missing for a call center: governed knowledge (the rules text, cited) and memory that survives the container.
- Foundry IQ: index per bounded context, knowledge sources on top, one knowledge base that plans and synthesises retrieval across them. It is exposed over MCP; the retrieval tool the model sees is `knowledge_base_retrieve`. Instruction rule: call it first, cite the doc id.
- Two ways to reach it. A platform prompt agent uses `MCPTool` + project connection (Stretch 5). An in-process Agent Framework agent uses `MCPStreamableHTTPTool` and must bring its own token: an `httpx.Auth` that asks `DefaultAzureCredential` for `https://search.azure.com/.default` on every request. Locally that is your `az login`; in the container it is the hosted agent's managed identity.
- Hosted agents are containers Foundry builds and scales. Containers are stateless by design: Foundry may restart one for a version roll, start a second replica under load, or move it. If the conversation history lives in a Python list inside the process, the participant is greeted with "how can I help?" halfway through a denied-claim call.
- So state lives outside: the **message store** (Redis when `BENEFITS_REDIS_URL` is set, files on one laptop) holds the history keyed by session id; the **session map** (`common.session_store`) holds the small record the client must never lose (session -> conversation id, last response id, turn count). `default_options={"store": False}` tells the model service to keep nothing; we own the transcript and its retention.
- Why this makes version rolls and scale-out safe: version N+1 boots, reads the same Redis key, continues the same participant. Replica 2 does the same. Rollback is the same story backwards. Nothing is copied between containers, because nothing lives in them.
- Configuration is environment: `BENEFITS_KB_MCP_URL`, `BENEFITS_REDIS_URL`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, later `APPLICATIONINSIGHTS_CONNECTION_STRING`. `azd env set` puts them on the hosted agent. Code never changes between dev, test and prod.

```
 workstation (notebook)                       Azure
 +---------------------------+     +------------------------------+
 | knowledge_base.py         | --> | Azure AI Search              |
 |  indexes, KS, KB, ARM PUT |     |  benefits-kb-marketplace/accounts |
 +---------------------------+     |  benefits-kb  --MCP--+   |
 | lab2_hosted_knowledge.py  |     +--------------------------|---+
 |  start -> ask x2 -> KILL  |                                |
 |  start -> ask (memory?)   |     +------------------------------+
 +------------+--------------+     | Foundry project               |
              | POST /responses    |  FoundryChatClient (model)    |
              v                    +------------------------------+
 +---------------------------+  Entra bearer (search.azure.com)   ^
 | hosted/main.py :8088      |------------------------------------+
 |  Agent + 5 tools + benefits-kb |
 |  history -> message store |----> Redis (BENEFITS_REDIS_URL) or files
 |  session map -> store     |----> artifacts/lab2/sessions/
 +---------------------------+
   same file, same behaviour when Foundry runs it as a container
```

## Demo (10 min)
1. `python lab2_hosted_knowledge.py` (or run the notebook top to bottom). While the indexes build (1 to 2 min), show data/knowledge/hra-reimbursement-rules.md and its frontmatter: this is the customer's documentation shape.
2. Point at `[lab2] knowledge base benefits-kb with sources ['marketplace-ks', 'accounts-ks']` and `[lab2] project connection ...`. In the portal: Azure AI Search > Knowledge bases; Foundry > Management center > Connections.
3. Watch the server log: `[hosted] knowledge: MCP https://...`, `[hosted] history: file (...)`, `[hosted] agent benefits-concierge-hosted v2: ... tools=6`.
4. Turn 1 and 2 print with citations ([KB-MKT-001] on the enrollment answer). Then `[lab2] killed main.py pid ...`, `[lab2] restarting main.py`, and turn 3 answered by a different pid still says "atorvastatin". Read `[lab2] continuity check: OK` aloud. Say: "that restart is what a version roll looks like from the participant's chair."
5. Open `artifacts/lab2/sessions/S1-evelyn.json` and `artifacts/lab2/message_store/`: this is everything the container did not keep.
6. `python lab2_hosted_knowledge.py --deploy`: read the azd runbook. Explain `azd env set BENEFITS_KB_MCP_URL` and where the container's identity needs Search Index Data Reader.

## Do (35 min)
1. Confirm `.env` has `AZURE_AI_SEARCH_ENDPOINT`, `AZURE_OPENAI_ENDPOINT`, `PROJECT_RESOURCE_ID`, `EMBEDDING_MODEL_DEPLOYMENT_NAME`. Run `python lab2_hosted_knowledge.py --build-only`. You should see two `[lab2] index ...: N chunks from M docs` lines, the knowledge base line, the connection line, `vendored common/`, `vendored data/`, and `saved artifacts/lab2/hosted.json`.
2. `python knowledge_base.py --demo-only`: three hits per index with doc ids. Checkpoint: the accounts query returns KB-ACC-001 first.
3. `python lab2_hosted_knowledge.py --demo-only`. Checkpoint: three turns, two pids, `continuity check: OK`, `saved artifacts/lab2/transcripts.md`. Open the transcript and confirm turn 2 carries a [KB-MKT-001] citation and turn 3 repeats the drug and the plan ids.
4. Keep a server running yourself: `cd hosted && python main.py` in terminal A, `python test_local.py --session S2-harold` in terminal B. The third question ("which plan is best") must get a refusal and an advisor offer; `PASS` at the end.
5. YOUR TURN (5 min): scale out. Start Redis (`docker run -d -p 6379:6379 redis:latest`), `export BENEFITS_REDIS_URL=redis://localhost:6379/0`, start two servers on 8088 and 8089, send turn 1 to one and turn 3 to the other with the same session id. Solution in the script's YOUR TURN cell. Checkpoint: the 8089 answer names atorvastatin; `[hosted] history: redis (...)` in both logs.
6. YOUR TURN (5 min): break it. Point `BENEFITS_MESSAGE_STORE_DIR` for the restarted process at an empty folder (or rename `hosted/common/message_store.py`) and rerun the demo. Checkpoint: `continuity check: FAIL` and the warning line explaining why. Restore.
7. YOUR TURN (5 min): knowledge on and off. Ask the running server "What proof of payment do you accept for a premium claim?" and check for [KB-ACC-001]. Restart the server without `BENEFITS_KB_MCP_URL` and ask again: the agent must say the rule text is not at hand (rule 4), not invent a list.
8. Optional (10 min, needs Foundry Project Manager): deploy. Run the `--deploy` commands from `hosted/`. Wait for version status `active`, then `python hosted/test_local.py --deployed`. Change the greeting line in main.py, `azd up` again, run the deployed test with the same `--session`: the new version continues the session.

## Checkpoint (5 min)
Paste the `[lab2] continuity check:` line with both pids, and one citation from turn 2. `artifacts/lab2/knowledge.json` (with `connection.connection_id`) and `artifacts/lab2/hosted.json` must exist: Lab 3 puts the specialists behind the same knowledge base, Lab 4 evaluates and traces this hosted agent.

## If you're behind
`python catch_up.py --through 2` builds the knowledge base, vendors the hosted folder and writes hosted.json; it does not run the kill-and-restart demo. Skip steps 5 and 8; do step 3.

## Stretch (only if you're done early)
Add an OData `filter="context eq 'accounts'"` knowledge source and a third index so the accounts assistant in Lab 3 never sees marketplace text; compare the citations before and after.

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| 403 from Azure AI Search on index create | user lacks Search Service Contributor / Search Index Data Contributor | assign both on the search service; wait 5 to 15 min |
| `connection PUT failed 403` | user cannot write project connections | Azure AI Owner or Contributor on the Foundry account; or `--skip-connection` and let a proctor create it |
| Vectorizer or KB answers fail with 401 | search service identity lacks Cognitive Services OpenAI User + Cognitive Services User on the Foundry account | assign both; propagation 5 to 15 min |
| No `[KB-...]` citations, server log shows MCP errors | container/user identity lacks Search Index Data Reader, or `BENEFITS_KB_MCP_URL` unset | assign the role to your user (local) or the hosted agent identity (cloud); check `knowledge.json` `mcp_endpoint` |
| `main.py exited early` | `FOUNDRY_PROJECT_ENDPOINT` unset or `az login` expired | fill `.env` at the base repo root; `az login --tenant $TENANT_ID` |
| `port 8088 is already in use` | a previous main.py still running | stop it, or `--port 8089` |
| `continuity check: FAIL` | history stayed in memory (message_store missing, or the server ignored the session id) | read `[hosted] history:` and `[hosted] WARNING` lines; confirm `hosted/common/message_store.py` exists after prepare.py |
| `ModuleNotFoundError: agent_framework_foundry_hosting` | package missing in the venv | it is in `labs/requirements.txt` and `hosted/requirements.txt` |
| `azd ai agent init` 403 | missing Foundry Project Manager | ask the proctor; wait for propagation |
| 424 `session_not_ready` after deploy | container still starting | read the logstream in the portal, retry after a minute |
| Model or region errors | deployment name mismatch, region without Agent Service or Foundry IQ | match `AZURE_AI_MODEL_DEPLOYMENT_NAME` to the portal; use a tested region |

## References
- Learn: [Build knowledge-enhanced AI agents with Foundry IQ](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/), [Integrate MCP Tools with Azure AI Agents](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/), [Develop an AI agent with Microsoft Agent Framework](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/)
- Base repo notebooks reused: `agent-framework/threads/2-redis-chat-message-store-thread.ipynb` (Redis history provider), `hosted-agents/benefits-advisor-responses/main.py` (ResponsesHostServer shape), `azure-ai-agents/*foundry-iq*` (knowledge base over MCP)
- Hosted agents how-to: https://learn.microsoft.com/azure/foundry/agents/how-to/hosted-agents (VERIFY request shape and session handling before delivery)
