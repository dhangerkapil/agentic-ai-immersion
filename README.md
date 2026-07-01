# 🚀 Agentic AI Immersion Workshop

[![Microsoft Foundry](https://img.shields.io/badge/Microsoft-Foundry-blue?style=for-the-badge&logo=microsoft)](https://ai.azure.com)
[![Python](https://img.shields.io/badge/Python-3.12+-green?style=for-the-badge&logo=python)](https://python.org)
[![Jupyter](https://img.shields.io/badge/Jupyter-Lab-orange?style=for-the-badge&logo=jupyter)](https://jupyter.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**Comprehensive Microsoft Foundry & Agents Development Workshop**

*Master AI agents, workflows, observability, and enterprise patterns through hands-on experimentation with real-world use cases.*

---

## 📑 Table of Contents

- [🎯 Mission Statement](#-mission-statement)
- [📁 Repository Structure](#-repository-structure)
- [🚀 Getting Started](#-getting-started)
  - [Required Azure RBAC Roles](#step-6-required-azure-rbac-roles--storage-access)
- [📚 Learning Path](#-learning-path)
- [💼 Industry Use Cases](#-industry-use-cases)
- [🛠️ Bring Your Own Use Case](#️-bring-your-own-use-case)
- [🛠️ Troubleshooting & Support](#️-troubleshooting--support)
- [🤝 Community & Contributions](#-community--contributions)

---

## 🎯 Mission Statement

This comprehensive workshop transforms you from an AI enthusiast into a Microsoft Foundry expert. Through progressive, hands-on modules, you'll master:

| Module | Topics | Technology |
|--------|--------|------------|
| **Foundation** | Setup, Authentication, Quick Start | Azure AI Foundry, Azure AI Agents v2 |
| **Agents** | File Search, Web Search, Azure Functions, Multi-Agent | Code Interpreter, WebSearchTool, Multi-Agent Workflows |
| **Foundry IQ** | Revolutionary agentic retrieval with knowledge bases | Foundry IQ, Knowledge Bases |
| **Advanced** | MCP Integration, Red Teaming, Agent Framework | Foundry MCP Server, Microsoft Agent Framework |
| **Operations** | Observability, Evaluation, Fine-Tuning | OpenTelemetry, Azure Monitor, Built-in Evaluators |
| **Hosted Agents** | Deploy agents as managed containers (Invocations + Responses protocols) | Azure Developer CLI (azd), Foundry Hosted Agents |
| **AgentOps** | GitOps CI/CD for agents — build, deploy, promote, rollback | GitHub Actions, Bicep, pytest |
| **Enterprise** | Responsible AI | Red Team Testing, Content Safety |

> **🎓 Format**: Intensive hands-on experience  
> **🎯 Audience**: Developers, AI practitioners, and solution architects  
> **💡 Approach**: Progressive complexity with real-world business use cases

---

## 📁 Repository Structure

```
agentic-ai-immersion-day/
│
├── 🤖 azure-ai-agents/                        # Azure AI Agents SDK
│   ├── 1-basics.ipynb                         # Agent fundamentals
│   ├── 2-code-interpreter.ipynb               # Code execution
│   ├── 3-file-search.ipynb                    # Document Q&A
│   ├── 4-web-search.ipynb                      # Web search integration (WebSearchTool)
│   ├── 5-agents-aisearch.ipynb                # Enterprise search
│   ├── 6-multi-agent-solution-with-workflows.ipynb
│   ├── 7-mcp-tools.ipynb                      # MCP integration
│   ├── 8-foundry-IQ-agents.ipynb              # 🧠 Foundry IQ - Agentic retrieval
│   ├── 9-agent-memory-search.ipynb            # Memory patterns
│   ├── 10-hosted-agent-with-skills.ipynb      # 🏦 Hosted agent + Skills (FSI)
│   ├── 11-routines.ipynb                      # 🔁 Routines — schedule an agent (preview)
│   ├── 12-agent-memory.ipynb                  # 🧠 Memory stores (preview)
│   ├── 13-model-router.ipynb                  # 🔀 Cost-optimized model routing
│   ├── 14-agent-to-agent-a2a.ipynb            # 🤝 Agent-to-Agent (A2A) (preview)
│   └── 15-managed-mcp-connectors.ipynb        # 🔌 Managed MCP connectors (preview)
│
├── 🤖⚙️ agent-framework/                       # Microsoft Agent Framework (Business use cases)
│   ├── agents/azure-ai-agents/                # 9 agent notebooks (1-9)
│   ├── context-providers/                     # 2 context/memory notebooks (1-2)
│   ├── middleware/                            # 9 interception patterns (1-9)
│   ├── observability/                         # 3 telemetry notebooks (1-3)
│   ├── skills/                                # Agent Skills (FSI: credit risk, compliance)
│   ├── threads/                               # 3 persistence notebooks (1-3)
│   └── workflows/                             # 9 orchestration notebooks (1-9)
│
├── 📊 observability-and-evaluations/          # Evaluation & Security
│   ├── 1-telemetry.ipynb                      # Azure Monitor telemetry
│   ├── 2-agent-evaluation.ipynb               # Built-in evaluators
│   ├── 3-agent-evaluation-with-function-tools.ipynb
│   ├── 4-tool-call-accuracy-evaluation.ipynb  # Tool accuracy
│   └── 5-red-team-security-testing.ipynb      # Security testing
│
├── 🚀 hosted-agents/                          # Hosted Agents — two hosting protocols (FSI: employee benefits)
│   ├── README.md                              # Protocol comparison + setup
│   ├── benefits-review-invocations/           # Invocations protocol (structured request → response)
│   └── benefits-advisor-responses/            # Responses protocol + Foundry Toolbox + Skills
│
├── 🔧 AgentOps/                                # GitOps deployment example (CI/CD, IaC, tests)
│   ├── .github/workflows/                     # validate / build-deploy / rollback
│   ├── src/                                    # agent, prompts, toolbox-as-code
│   ├── infra/                                  # Bicep + per-environment params
│   └── tests/                                  # unit / integration / smoke
│
├── 🧩 byouc/                                   # Bring Your Own Use Case
│   ├── Agentic_UseCase_Spec.md                # Use case spec template (Markdown)
│   └── Agentic_UseCase_Spec.docx              # Use case spec template (Word)
│
├── 🐳 .devcontainer/                          # Dev Container configuration
│   └── devcontainer.json                      # Container settings
│
├── 🔐 scripts/                                # Setup automation
│   └── setup-permissions.ps1                  # One-shot RBAC + storage access (Entra, idempotent)
│
├── .env.example                               # Environment template
├── requirements.in                            # Unpinned dependencies
├── requirements.txt                           # Pinned dependencies (pip-compile)
└── README.md                                  # This file
```

---

## 📖 Key Concepts (30-second glossary)

| Term | Definition |
|------|-----------|
| **Microsoft Foundry** | Azure's platform for building, deploying, and managing AI agents |
| **Agent** | An AI that uses tools (code, search, APIs) to complete tasks |
| **Foundry IQ** | Knowledge Bases — agentic retrieval where the agent decides what to search |
| **MCP** | Model Context Protocol — a standard for connecting agents to external tools |
| **Hosted Agent** | An agent packaged as a container and run/scaled by Foundry |
| **Managed Identity** | An Azure-managed credential (no API keys) used by services |
| **FSI** | Financial Services Industry — the example domain throughout |

## �🚀 Getting Started

### Option A: Dev Container (Recommended) 🐳

For a consistent, pre-configured environment with all dependencies:

1. **Prerequisites**: Install [Docker](https://docker.com) and [VS Code](https://code.visualstudio.com) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Open in Container**:
   - Clone the repo and open in VS Code
   - Press `F1` → **Dev Containers: Reopen in Container**
   - Wait for the container to build (first time takes ~5 minutes)

3. **Ready to go!** All dependencies are pre-installed including:
   - Python 3.14 with all packages (pinned versions)
   - Azure CLI and Azure Developer CLI (azd)
   - Jupyter notebooks support
   - GitHub Copilot extensions

> 💡 **Tip:** Your Azure credentials are automatically mounted from your local machine.

### Option B: Local Setup

#### Step 1: Repository Setup

```powershell
# Clone the repository
git clone https://github.com/dhangerkapil/agentic-ai-immersion-day.git
cd agentic-ai-immersion-day

# Verify Python version
python --version  # Python 3.12+ (3.14 recommended — matches the pinned lock & Dev Container)
```

#### Step 2: Environment Setup

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies (versions are pinned for consistency)
pip install -r requirements.txt
```

#### Step 3: Sign in to Azure

```powershell
az login           # opens a browser; pick the subscription that has your Foundry project
az account show    # confirm the right subscription is active
```

> 🔐 This workshop is **Entra-only**: every notebook authenticates with `DefaultAzureCredential` (your `az login` session) — **no API keys**. Stay signed in for all later steps.

#### Step 4: Create your Foundry project & deploy models

1. **Create a Foundry resource** — [ai.azure.com](https://ai.azure.com) → **Create project** (creates the account + a project + default storage); pick a region like East US 2.
2. **Deploy models** — project → **Models + endpoints** → **Deploy** each of `gpt-5.4`, `gpt-5.4-mini`, `text-embedding-3-large` (status “Succeeded” after a few minutes).
3. **Connect services** — add Azure AI Search + Application Insights connections (project → **Connections**) for the search/observability notebooks.

For detailed setup, see [Microsoft Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/).

#### Step 5: Configure Environment Variables

1. Copy `.env.example` to `.env` **at the repo root** (`cp .env.example .env`)
2. Fill in the values from the project you just created. **`.env.example` is the annotated source of truth** for every variable — the essentials are:

```env
# Microsoft Foundry project (azure-ai-agents/ + observability notebooks)
AI_FOUNDRY_PROJECT_ENDPOINT=https://<your-foundry>.services.ai.azure.com/api/projects/<your-project>
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5.4
EMBEDDING_MODEL_DEPLOYMENT_NAME=text-embedding-3-large

# Agent Framework Foundry client convention (agent-framework/ notebooks)
FOUNDRY_PROJECT_ENDPOINT=https://<your-foundry>.services.ai.azure.com/api/projects/<your-project>
FOUNDRY_MODEL=gpt-5.4

# Azure OpenAI v1 surface (agent-framework workflows / middleware / threads)
AZURE_OPENAI_ENDPOINT=https://<your-foundry>.openai.azure.com/openai/v1
AZURE_OPENAI_API_KEY=        # leave BLANK — this workshop uses Entra ID (az login), not keys

# Azure AI Search (notebooks 5 & 8, context-providers/2)
AZURE_AI_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
```

> 🔐 **Entra-only auth:** every notebook authenticates with `DefaultAzureCredential` (`az login`) — **no API keys**. Leave `AZURE_OPENAI_API_KEY` blank; if your account has `disableLocalAuth=true`, keys won't work at all.

**Where to find these values:** Foundry portal ([ai.azure.com](https://ai.azure.com)) → your project → **Overview/Settings** has the project endpoint; **Deployments** lists your model names; the AI Search URL is on the Search resource **Overview** in the Azure portal.

### Step 6: Required Azure RBAC Roles & Storage Access

> ⚡ **Fastest path — run the setup script** (idempotent, Entra-only). It assigns every role below to your user, the project managed identity, **and** the AI Search managed identity, and opens storage networking:
>
> ```powershell
> ./scripts/setup-permissions.ps1 -SubscriptionId "<sub-id>" -ResourceGroup "<rg>" `
>     -AccountName "<foundry-account>" -ProjectName "<project>" `
>     -SearchServiceName "<search-service>" -StorageAccountName "<storage>" -OpenStoragePublicAccess
> ```
>
> Prefer to assign roles by hand? The full breakdown — and the exact `az` commands the script runs — follow.

Authentication is **Entra-only** (`az login` — no API keys). Roles go to one of three identities: **your user**, the **Project Managed Identity** (the project's own identity, under *Foundry project → Identity*), or the **AI Search service Managed Identity**. Foundry resources use the `Microsoft.CognitiveServices/accounts/<account>` scope (not ML workspaces).

#### 🔑 Core Roles (Required for All Notebooks)

| Role | Assignee | Resource | Purpose |
|------|----------|----------|---------|
| **Foundry User** | User **and** Project MI | Foundry account | Data-plane build access. ⚠️ SDK/CLI-created projects don't grant this to the project MI automatically — the #1 cause of `ProjectMIUnauthorized` |
| **Cognitive Services OpenAI User** | User, Project MI, Search MI | Foundry account | Access OpenAI model deployments (chat + embeddings) |
| **Cognitive Services User** | Project MI **and** Search MI | Foundry account | Foundry IQ agentic-retrieval reasoning model (notebook 8) |

#### 📁 File Search & Storage Roles

| Role | Assignee | Resource | Purpose | Notebooks |
|------|----------|----------|---------|-----------|
| **Storage Blob Data Contributor** | User | Project Storage Account | Upload files for agent file search | `3-file-search.ipynb`, `6-azure-ai-with-file-search.ipynb` |

#### 🔍 Azure AI Search Roles

| Role | Assignee | Resource | Purpose | Notebooks |
|------|----------|----------|---------|-----------|
| **Search Index Data Contributor** | User | AI Search Resource | Create indexes, upload documents | `5-agents-aisearch.ipynb`, `8-foundry-IQ-agents.ipynb` |
| **Search Index Data Reader** | User | AI Search Resource | Query search indexes | `5-agents-aisearch.ipynb`, `8-foundry-IQ-agents.ipynb` |
| **Search Service Contributor** | User | AI Search Resource | Manage search service, create knowledge bases | `8-foundry-IQ-agents.ipynb` |
| **Search Index Data Reader** | Managed Identity | AI Search Resource | ⚠️ **CRITICAL**: Agent runtime access to knowledge bases | `8-foundry-IQ-agents.ipynb` |

#### ️ Role Assignment Commands (the same set the script runs)

```powershell
# ── Fill in your resource names ──
$SUB = "<sub-id>"; $RG = "<rg>"; $ACCOUNT = "<foundry-account>"; $PROJECT = "<project>"
$SEARCH = "<search-service>"; $STORAGE = "<storage-account>"

# Scopes — the Foundry account uses Microsoft.CognitiveServices (NOT ML workspaces)
$ACCOUNT_SCOPE = "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.CognitiveServices/accounts/$ACCOUNT"
$STORAGE_SCOPE = "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$STORAGE"
$SEARCH_SCOPE  = "/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Search/searchServices/$SEARCH"

# Identities
$USER_ID    = az ad signed-in-user show --query id -o tsv
$PROJECT_MI = az rest --method get --url "https://management.azure.com$ACCOUNT_SCOPE/projects/$PROJECT?api-version=2025-04-01-preview" --query identity.principalId -o tsv
$SEARCH_MI  = az search service show -n $SEARCH -g $RG --query identity.principalId -o tsv

# Foundry User role ID (use the GUID — the role was renamed from "Azure AI User")
$FOUNDRY_USER = "53ca6127-db72-4b80-b1b0-d745d6d5456d"

# ── YOU (user) ──
az role assignment create --role $FOUNDRY_USER --assignee-object-id $USER_ID --assignee-principal-type User --scope $ACCOUNT_SCOPE
az role assignment create --role "Cognitive Services OpenAI User" --assignee-object-id $USER_ID --assignee-principal-type User --scope $ACCOUNT_SCOPE
az role assignment create --role "Storage Blob Data Contributor" --assignee-object-id $USER_ID --assignee-principal-type User --scope $STORAGE_SCOPE
az role assignment create --role "Search Index Data Contributor" --assignee-object-id $USER_ID --assignee-principal-type User --scope $SEARCH_SCOPE
az role assignment create --role "Search Index Data Reader" --assignee-object-id $USER_ID --assignee-principal-type User --scope $SEARCH_SCOPE
az role assignment create --role "Search Service Contributor" --assignee-object-id $USER_ID --assignee-principal-type User --scope $SEARCH_SCOPE

# ── PROJECT managed identity (⚠️ SDK/CLI-created projects don't get Foundry User automatically) ──
az role assignment create --role $FOUNDRY_USER --assignee-object-id $PROJECT_MI --assignee-principal-type ServicePrincipal --scope $ACCOUNT_SCOPE
az role assignment create --role "Cognitive Services OpenAI User" --assignee-object-id $PROJECT_MI --assignee-principal-type ServicePrincipal --scope $ACCOUNT_SCOPE
az role assignment create --role "Cognitive Services User" --assignee-object-id $PROJECT_MI --assignee-principal-type ServicePrincipal --scope $ACCOUNT_SCOPE
az role assignment create --role "Storage Blob Data Contributor" --assignee-object-id $PROJECT_MI --assignee-principal-type ServicePrincipal --scope $STORAGE_SCOPE
az role assignment create --role "Search Index Data Reader" --assignee-object-id $PROJECT_MI --assignee-principal-type ServicePrincipal --scope $SEARCH_SCOPE

# ── AI SEARCH managed identity (Foundry IQ — embeddings + reasoning model) ──
az role assignment create --role "Cognitive Services OpenAI User" --assignee-object-id $SEARCH_MI --assignee-principal-type ServicePrincipal --scope $ACCOUNT_SCOPE
az role assignment create --role "Cognitive Services User" --assignee-object-id $SEARCH_MI --assignee-principal-type ServicePrincipal --scope $ACCOUNT_SCOPE

# ── Storage networking — let the managed Foundry services reach the account (RBAC still enforced) ──
az storage account update -n $STORAGE -g $RG --public-network-access Enabled
```

> **⚠️ Critical Notes:**
> - **`Foundry User` on the project MI is the #1 gotcha.** Projects created via SDK/CLI don't get it automatically, which causes `ProjectMIUnauthorized` in the evaluation notebooks (2–4) and 401s in Foundry IQ (8). The setup script assigns it for you.
> - **`Cognitive Services User` on the AI Search MI** is required for the Foundry IQ reasoning model (notebook 8) — the narrower `Cognitive Services OpenAI User` alone is **not** enough for agentic retrieval.
> - **Storage networking:** evaluations (2–4) and agent file search (6) need the managed services to reach the project storage. If it's private-only you'll see `AuthorizationFailure` 403s — enable public network access (RBAC still applies) or use private endpoints reachable by Foundry.
> - **Redis (notebook `threads/2`):** start a local Redis first — `docker run -d --name redis-workshop -p 6379:6379 redis:7-alpine`.
> - **Azure Developer CLI (`azd`)** is needed for the hosted-agent deploy walkthrough (notebook 10, `hosted-agents/`, `AgentOps/`) — [install azd](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd).
> - **Role propagation:** Entra data-plane assignments take **5–15 minutes**. If a notebook returns 401/403 right after setup, wait and retry.

---

### Step 7: Verify your setup ✅

```powershell
python -c "from dotenv import load_dotenv; load_dotenv(); import os; from azure.identity import DefaultAzureCredential; from azure.ai.projects import AIProjectClient; AIProjectClient(endpoint=os.environ['AI_FOUNDRY_PROJECT_ENDPOINT'], credential=DefaultAzureCredential()); print('✅ Connected to Foundry')"
```

Then open `azure-ai-agents/1-basics.ipynb` and run the first cell — clean output means you're ready. A `401/403` means roles are still propagating; wait 5–10 min and retry.

---

## 📚 Learning Path

Follow this structured learning path to master Microsoft Foundry and AI Agents:

### 🤖 Phase 1: Azure AI Agents SDK
**Location:** `azure-ai-agents/`

| # | Notebook | Description |
|---|----------|-------------|
| 1 | [Agent Basics](azure-ai-agents/1-basics.ipynb) | Fundamental agent concepts and lifecycle |
| 2 | [Code Interpreter](azure-ai-agents/2-code-interpreter.ipynb) | Python code execution capabilities |
| 3 | [File Search](azure-ai-agents/3-file-search.ipynb) | Document processing and Q&A |
| 4 | [Web Search](azure-ai-agents/4-web-search.ipynb) | WebSearchTool for real-time market data |
| 5 | [Agents + AI Search](azure-ai-agents/5-agents-aisearch.ipynb) | Enterprise search integration |
| 6 | [Multi-Agent Workflows](azure-ai-agents/6-multi-agent-solution-with-workflows.ipynb) | Collaborative AI systems |
| 7 | [MCP Tools](azure-ai-agents/7-mcp-tools.ipynb) | Model Context Protocol integration |
| 8 | [🧠 Foundry IQ Agents](azure-ai-agents/8-foundry-IQ-agents.ipynb) | **Revolutionary agentic retrieval** - Knowledge-grounded agents |
| 9 | [Agent Memory Search](azure-ai-agents/9-agent-memory-search.ipynb) | Persistent memory patterns |
| 10 | [🏦 Hosted Agent + Skills](azure-ai-agents/10-hosted-agent-with-skills.ipynb) | Skills (`beta.skills` SDK) + hosted-agent deploy walkthrough (FSI) |
| 11 | [🔁 Routines](azure-ai-agents/11-routines.ipynb) | Schedule an agent to run on a cron (preview) |
| 12 | [🧠 Agent Memory](azure-ai-agents/12-agent-memory.ipynb) | Memory stores — long-term memory across sessions (preview) |
| 13 | [🔀 Model Router](azure-ai-agents/13-model-router.ipynb) | Cost-optimized routing across model deployments |
| 14 | [🤝 Agent-to-Agent (A2A)](azure-ai-agents/14-agent-to-agent-a2a.ipynb) | Expose & call agents over the A2A protocol (preview) |
| 15 | [🔌 Managed MCP Connectors](azure-ai-agents/15-managed-mcp-connectors.ipynb) | Connect agents to managed MCP servers (preview) |

### 🤖⚙️ Phase 2: Microsoft Agent Framework
**Location:** `agent-framework/`

The **Microsoft Agent Framework** is an open-source SDK that unifies Semantic Kernel and AutoGen into the next-generation foundation for AI agent development. It offers **AI Agents** for autonomous decision-making with tool integration, and **Workflows** for orchestrating complex multi-agent processes with type safety and checkpointing.

📖 [Official Documentation](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview) • 🔗 [GitHub Repository](https://github.com/microsoft/agent-framework) • 📚 [Complete Guide](agent-framework/README.md)

#### 🤖 Azure AI Agents (`agents/azure-ai-agents/`)

| # | Notebook | Description |
|---|----------|-------------|
| 1 | [Basic Agent](agent-framework/agents/azure-ai-agents/1-azure-ai-basic.ipynb) | Fundamental agent concepts with automatic lifecycle management |
| 2 | [Explicit Settings](agent-framework/agents/azure-ai-agents/2-azure-ai-with-explicit-settings.ipynb) | Agent creation with explicit configuration patterns |
| 3 | [Existing Agent](agent-framework/agents/azure-ai-agents/3-azure-ai-with-existing-ai-agent.ipynb) | Working with pre-existing agents using agent IDs |
| 4 | [Function Tools](agent-framework/agents/azure-ai-agents/4-azure-ai-with-function-tools.ipynb) | Comprehensive function tool integration patterns |
| 5 | [Code Interpreter](agent-framework/agents/azure-ai-agents/5-azure-ai-with-code-interpreter.ipynb) | Python code execution and mathematical problem solving |
| 6 | [File Search](agent-framework/agents/azure-ai-agents/6-azure-ai-with-file-search.ipynb) | Document-based question answering with file uploads |
| 7 | [Web Search](agent-framework/agents/azure-ai-agents/7-azure-ai-with-web-search.ipynb) | Web search integration using WebSearchTool |
| 8 | [Hosted MCP](agent-framework/agents/azure-ai-agents/8-azure-ai-with-hosted-mcp.ipynb) | Model Context Protocol server integration |
| 9 | [Multi-turn Threads](agent-framework/agents/azure-ai-agents/9-azure-ai-with-existing-multi-turn-thread.ipynb) | Managing multi-turn conversation threads |

#### 🧠 Context Providers (`context-providers/`)

| # | Notebook | Use Case |
|---|----------|----------|
| 1 | [Simple Context Provider](agent-framework/context-providers/1-simple-context-provider.ipynb) | Customer Profile Collection |
| 2 | [Azure AI Search Context](agent-framework/context-providers/2-azure-ai-search-context-agentic.ipynb) | Document-Based Decisions with RAG |

#### 🎯 Skills (`skills/`)

| # | Notebook | Use Case |
|---|----------|----------|
| 1 | [Agent with Skills](agent-framework/skills/1-agent-with-skills.ipynb) | FSI Credit Risk + Compliance (file-based & code-defined skills) |

#### 🛡️ Middleware (`middleware/`)

| # | Notebook | Use Case |
|---|----------|----------|
| 1 | [Agent & Run Level](agent-framework/middleware/1-agent-and-run-level-middleware.ipynb) | Middleware scoping fundamentals |
| 2 | [Function-Based](agent-framework/middleware/2-function-based-middleware.ipynb) | Function-based patterns |
| 3 | [Class-Based](agent-framework/middleware/3-class-based-middleware.ipynb) | Class-based with inheritance |
| 4 | [Decorator Middleware](agent-framework/middleware/4-decorator-middleware.ipynb) | Resource Rebalancing |
| 5 | [Chat Middleware](agent-framework/middleware/5-chat-middleware.ipynb) | Content Filtering |
| 6 | [Exception Handling](agent-framework/middleware/6-exception-handling-with-middleware.ipynb) | Data Recovery |
| 7 | [Termination](agent-framework/middleware/7-middleware-termination.ipynb) | Compliance Screening |
| 8 | [Result Override](agent-framework/middleware/8-override-result-with-middleware.ipynb) | Data Enrichment |
| 9 | [Shared State](agent-framework/middleware/9-shared-state-middleware.ipynb) | Activity Audit Trail |

#### 📊 Observability (`observability/`)

| # | Notebook | Use Case |
|---|----------|----------|
| 1 | [Foundry Tracing](agent-framework/observability/1-agent-with-foundry-tracing.ipynb) | Execution Monitoring |
| 2 | [Agent Observability](agent-framework/observability/2-azure-ai-agent-observability.ipynb) | Service Monitoring |
| 3 | [Workflow Observability](agent-framework/observability/3-workflow-observability.ipynb) | Pipeline Monitoring |

#### 🧵 Threads (`threads/`)

| # | Notebook | Use Case |
|---|----------|----------|
| 1 | [Custom Message Store](agent-framework/threads/1-custom-chat-message-store-thread.ipynb) | Audit Trail Storage |
| 2 | [Redis Message Store](agent-framework/threads/2-redis-chat-message-store-thread.ipynb) | Distributed Sessions |
| 3 | [Suspend/Resume Thread](agent-framework/threads/3-suspend-resume-thread.ipynb) | Long-Running Requests |

#### 🔄 Workflows (`workflows/`)

| # | Notebook | Use Case | Pattern |
|---|----------|----------|---------|
| 1 | [Azure AI Streaming](agent-framework/workflows/1-azure-ai-agents-streaming.ipynb) | Real-time Data Updates | Streaming |
| 2 | [Chat Streaming](agent-framework/workflows/2-azure-chat-agents-streaming.ipynb) | Customer Support Chat | Streaming |
| 3 | [Sequential Application](agent-framework/workflows/3-sequential-agents-loan-application.ipynb) | Application Processing | Sequential |
| 4 | [Custom Executors](agent-framework/workflows/4-sequential-custom-executors-compliance.ipynb) | Approval with Compliance | Sequential |
| 5 | [Limit Approval](agent-framework/workflows/5-credit-limit-with-human-input.ipynb) | Limit Approval Workflow | Human-in-the-loop |
| 6 | [Transaction Review](agent-framework/workflows/6-workflow-as-agent-human-in-the-loop-transaction-review.ipynb) | High-Value Authorization | Workflow-as-agent |
| 7 | [Compliance Review](agent-framework/workflows/7-magentic-compliance-review-with-human-input.ipynb) | Plan Compliance Review | Magentic |
| 8 | [Research Analysis](agent-framework/workflows/8-magentic-investment-research.ipynb) | Multi-Agent Research | Magentic |
| 9 | [Reflection Pattern](agent-framework/workflows/9-workflow-as-agent-reflection-pattern.ipynb) | Communication Quality | Reflection |

### 📊 Phase 3: Observability & Evaluations
**Location:** `observability-and-evaluations/`

Comprehensive evaluation, observability, and security testing for AI agents.

| # | Notebook | Use Case | Key Concepts |
|---|----------|----------|--------------|
| 1 | [Telemetry](observability-and-evaluations/1-telemetry.ipynb) | Advisory Agent Monitoring | Azure Monitor, custom spans, Application Insights |
| 2 | [Agent Evaluation](observability-and-evaluations/2-agent-evaluation.ipynb) | Advisory Agent Quality | Built-in evaluators (violence, fluency, task_adherence) |
| 3 | [Function Tools Evaluation](observability-and-evaluations/3-agent-evaluation-with-function-tools.ipynb) | Business Assistant | FunctionTool evaluation, strict mode |
| 4 | [Tool Call Accuracy](observability-and-evaluations/4-tool-call-accuracy-evaluation.ipynb) | Operations Tooling | `builtin.tool_call_accuracy`, JSONL data sources |
| 5 | [Red Team Security](observability-and-evaluations/5-red-team-security-testing.ipynb) | AI Security Testing | RedTeam, AttackStrategy, RiskCategory |

📖 [Complete Guide](observability-and-evaluations/README.md)

### 🚀 Phase 4: Hosted Agents (Deployment)
**Location:** `hosted-agents/`

Two production-ready hosted-agent projects (FSI: employee benefits) demonstrating the two Foundry hosting protocols. Each is self-contained — `README.md`, `Dockerfile`, `requirements.txt`, and a `test_local.py` you can run against your Foundry project **before** deploying.

| Project | Protocol | What it shows |
|---------|----------|---------------|
| [benefits-review-invocations](hosted-agents/benefits-review-invocations/) | Invocations | Structured request → response agent on `InvocationsHostServer` |
| [benefits-advisor-responses](hosted-agents/benefits-advisor-responses/) | Responses | `ResponsesHostServer` + Foundry Toolbox (web search + code interpreter) + Skills |

```powershell
# Smoke-test either agent locally (no deploy needed — uses your Foundry project)
cd hosted-agents/benefits-review-invocations
python test_local.py
```

📖 [Hosting protocol comparison + deploy steps](hosted-agents/README.md)

### 🔧 Phase 5: AgentOps (GitOps for Agents)
**Location:** `AgentOps/`

A reference CI/CD pipeline for shipping a Foundry hosted agent the GitOps way — agent + prompts + toolbox-as-code, Bicep infrastructure, per-environment parameters, and unit/integration/smoke tests wired into GitHub Actions (validate → build-deploy → rollback).

```powershell
# Run the test suite locally
cd AgentOps
pip install -r requirements.txt
python -m pytest tests/unit tests/integration -q
```

📖 [Architecture + pipeline guide](AgentOps/README.md)

---

## 💼 Industry Use Cases

For 57 real-world FSI use cases (banking, insurance, investment) mapped to each notebook, see [💼 USE-CASES.md](USE-CASES.md).

---

## 🛠️ Bring Your Own Use Case

**Location:** `byouc/`

Have your own agent idea? Use the **Agentic Use Case Spec** template to define your use case, then let GitHub Copilot scaffold the entire agent MVP for you.

### How It Works

| Step | What You Do | What Copilot Does |
|------|-------------|-------------------|
| **Fill** | Complete the spec template (~10 min) — describe your agent's inputs, steps, outputs, rules, and test data | — |
| **Plan** | Paste the spec into Copilot **Plan mode** with the provided prompt | Generates a detailed implementation plan: folder structure, modules, agent definitions, workflow design |
| **Build** | Paste the plan into Copilot **Agent mode** with the provided prompt | Implements all code, tests, and documentation matching existing repo patterns |

### The Spec Template Covers

1. **Use Case Summary** — what the agent does and what problem it solves
2. **Input** — data type, structure, and size
3. **Agent Steps** — the tools your agent will use (step-by-step)
4. **Output** — expected format and severity/category levels
5. **Behavior Rules** — MUST and MUST NOT constraints
6. **Domain Context** — key terms and agent persona
7. **Preferences** — Notebook or Web app UI
8. **Synthetic Data Requirements** — test data spec (Copilot generates the data)

### Get Started

- 📄 **Markdown** → [byouc/Agentic_UseCase_Spec.md](byouc/Agentic_UseCase_Spec.md)
- 📝 **Word** → [byouc/Agentic_UseCase_Spec.docx](byouc/Agentic_UseCase_Spec.docx)

> **Includes a complete example** (Loan Application Risk Reviewer) so you can see exactly what a filled-out spec looks like.

---

## 🛠️ Troubleshooting & Support

### ⚡ Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| **Kernel Issues** | `python -m ipykernel install --user --name=ai-foundry-lab` then reload VS Code |
| **Environment Activation** | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| **Azure Authentication** | `az login --tenant YOUR_TENANT_ID` (Azure CLI preferred over VS Code extension) |
| **Package Import Errors** | Ensure `agent-framework` packages installed in same interpreter as Jupyter |
| **Redis Connectivity** | Update connection string and confirm service is reachable |
| **Application Insights Delay** | Use Live Metrics Stream for real-time debugging |

### 📚 Additional Resources

| Resource | Link |
|----------|------|
| **Microsoft Foundry Docs** | [learn.microsoft.com/azure/ai-foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/) |
| **Agent Framework Docs** | [learn.microsoft.com/agent-framework](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview) |
| **Agent Framework GitHub** | [github.com/microsoft/agent-framework](https://github.com/microsoft/agent-framework) |
| **Azure AI Services** | [learn.microsoft.com/azure/ai-services](https://learn.microsoft.com/azure/ai-services/) |
| **Video Tutorials** | [AI Show](https://learn.microsoft.com/en-us/shows/ai-show/) |
| **GitHub Issues** | [Report bugs or request features](https://github.com/dhangerkapil/agentic-ai-immersion/issues) |

---

## 🤝 Community & Contributions

| Contribution Type | Description |
|-------------------|-------------|
| 📝 **Documentation** | Improve clarity and add examples |
| 🐛 **Bug Reports** | Help identify and fix issues |
| 💡 **Feature Requests** | Suggest new capabilities |
| 🔄 **Pull Requests** | Contribute code and enhancements |

Please review our [Contributing Guide](CONTRIBUTING.md) for code style, testing requirements, and PR process.

---

## 📄 License

**License:** MIT License  
**Repository:** [github.com/dhangerkapil/agentic-ai-immersion](https://github.com/dhangerkapil/agentic-ai-immersion)

---

<div align="center">

**Built with ❤️ for the AI Developer Community**

*Happy Learning! 🚀*

</div>
