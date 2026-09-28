# Infrastructure notes for the hosted-agent pipeline

What the pipeline expects to exist per environment (dev, test, prod), who creates it, and what `azd` creates on its own. No Bicep ships in this folder on purpose: the base repo's `AgentOps/` folder carries the reference Bicep for a Foundry project with Application Insights, and your organization's platform team will have its own landing zone. This file lists the contract the code has with the infrastructure.

## Per environment
| Resource | Created by | Used by | Notes |
|---|---|---|---|
| Foundry resource + project | platform team (Bicep in base repo `AgentOps/infra`) | every lab | `FOUNDRY_PROJECT_ENDPOINT`, `PROJECT_RESOURCE_ID` |
| Model deployment `gpt-5.4-mini` and `text-embedding-3-large` | platform team | hosted agents, judges, Lab 2 index | Names in `AZURE_AI_MODEL_DEPLOYMENT_NAME` / `EMBEDDING_MODEL_DEPLOYMENT_NAME`; raise TPM for the eval job (18 questions x up to 4 model calls) |
| Azure AI Search with Foundry IQ knowledge base `benefits-kb` + project connection | Lab 2 in dev; platform team in test/prod | hosted agent (`BENEFITS_KB_MCP_URL`) | Semantic ranker enabled; search service identity needs Cognitive Services OpenAI User + Cognitive Services User on the Foundry account |
| Redis (test, prod) | platform team: Azure Managed Redis, Entra auth | hosted agent message store + session map (`BENEFITS_REDIS_URL`) | dev uses the file store inside the container (fine for one replica, wrong for two) |
| Application Insights connected to the project | platform team | Lab 4 tracing, hosted agent spans | `APPLICATIONINSIGHTS_CONNECTION_STRING` on the hosted agent through `azd env set` |
| Hosted agent `benefits-concierge-hosted` | `azd ai agent init` + `azd up` in the deploy job | Labs 2 to 4 | One azd environment per target: `benefits-concierge-dev`, `-test`, `-prod`; every `azd up` is a new version |
| Entra app with GitHub OIDC federated credentials | platform team | `azure/login@v2` in every Azure job | One per environment; subject `repo:<org>/<repo>:environment:<env>` |

## Roles the pipeline identity needs
| Scope | Role | Why |
|---|---|---|
| Foundry project | Azure AI User | run the model and the judges in the evaluate job |
| Foundry project | Foundry Project Manager | `azd ai agent init` / `azd up` (deploy and rollback jobs) |
| Foundry project | Foundry Agent Consumer | `test_local.py --deployed` smoke test |
| Foundry account | Cognitive Services OpenAI User | azure-ai-evaluation judges, embeddings |
| Search service | Search Index Data Reader | the evaluate job's local hosted/main.py calls the knowledge base MCP endpoint |
| Search service (dev) | Search Service Contributor + Search Index Data Contributor | `catch_up.py --through 2` rebuilds indexes when they are missing |

## Roles the hosted agent's managed identity needs
| Scope | Role | Why |
|---|---|---|
| Foundry project | Azure AI User | `FoundryChatClient` model calls with `DefaultAzureCredential` |
| Search service | Search Index Data Reader | `MCPStreamableHTTPTool` to the knowledge base with the Entra bearer |
| Azure Managed Redis (test, prod) | Redis data access policy (Entra) | message store and session map |

Propagation takes 5 to 15 minutes. The first pipeline run after a role change usually fails with 403; re-run.

## Hosted agent environment variables
`azd ai agent init` writes `agent.yaml` next to `hosted/main.py`; do not check it in unless the extension needs it (document the choice). The container reads: `FOUNDRY_PROJECT_ENDPOINT` (injected by Foundry), `AZURE_AI_MODEL_DEPLOYMENT_NAME`, `BENEFITS_KB_MCP_URL`, optional `BENEFITS_REDIS_URL`, `BENEFITS_SESSION_TTL_SECONDS`, `BENEFITS_TODAY`, optional `APPLICATIONINSIGHTS_CONNECTION_STRING`, `ENABLE_SENSITIVE_DATA` (never true outside dev). VERIFY the `agent.yaml` environment block format and the `azd env set` to container-env mapping against the azd extension output before the workshop.

## Environments and promotion
- `envs/.env.dev.example`, `.env.test.example`, `.env.prod.example`: same variable names, different values (file store -> Redis; sensitive tracing true -> false).
- GitHub Environments `dev`, `test`, `prod` hold the values as variables (none are secrets). `test` and `prod` have required reviewers: that is the human approval for a deploy, the same idea as the advisor approval in Lab 3.
- Promotion is a `workflow_dispatch` with `target_environment`, or `python promote.py --to test --execute` from a laptop. Both require a passing `artifacts/lab4/gate_result.json`.
- Rollback is a `workflow_dispatch` with `rollback_to=<tag>`: checks out the tag and runs `azd up` again. Hosted agent versions in the portal are the second rollback path (delete the bad version; `agent_reference` by name resolves to the latest active one). Sessions survive both because history lives in Redis, not in the container.

## What is deliberately not here
- Networking (private endpoints, VNet injection for the hosted agent), Key Vault (nothing to store: Entra only), APIM in front of the agent endpoint. Your organization's landing zone owns these.
- Data pipelines for the knowledge base. The workshop uses `data/knowledge/*.md` checked in; production needs the SharePoint indexer or the Word-to-Markdown conversion job.
