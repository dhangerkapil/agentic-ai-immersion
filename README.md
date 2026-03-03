# 🚀 Agentic AI Immersion Workshop

[![Microsoft Foundry](https://img.shields.io/badge/Microsoft-Foundry-blue?style=for-the-badge&logo=microsoft)](https://ai.azure.com)
[![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python)](https://python.org)
[![Jupyter](https://img.shields.io/badge/Jupyter-Lab-orange?style=for-the-badge&logo=jupyter)](https://jupyter.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**Comprehensive Microsoft Foundry & Agents Development Workshop**

*Master AI agents, workflows, observability, and enterprise patterns through hands-on experimentation with real-world use cases.*

---

## 📑 Table of Contents

- [🎯 Mission Statement](#-mission-statement)
- [📁 Repository Structure](#-repository-structure)
- [🚀 Getting Started](#-getting-started)
  - [Required Azure RBAC Roles](#step-5-required-azure-rbac-roles)
- [📚 Learning Path](#-learning-path)
- [🛠️ Troubleshooting & Support](#️-troubleshooting--support)
- [🤝 Community & Contributions](#-community--contributions)

---

## 🎯 Mission Statement

This comprehensive workshop transforms you from an AI enthusiast into a Microsoft Foundry expert. Through progressive, hands-on modules, you'll master:

| Module | Topics | Technology |
|--------|--------|------------|
| **Foundation** | Setup, Authentication, Quick Start | Azure AI Foundry, Azure AI Agents v2 |
| **Core AI** | Prompting, Embeddings, RAG | Azure OpenAI, Azure AI Search |
| **Agents** | File Search, Bing, Azure Functions, Multi-Agent | Code Interpreter, Bing Grounding, Multi-Agent Workflows |
| **Foundry IQ** | Revolutionary agentic retrieval with knowledge bases | Foundry IQ, Knowledge Bases |
| **Advanced** | MCP Integration, Red Teaming, Agent Framework | Foundry MCP Server, Microsoft Agent Framework |
| **Operations** | Observability, Evaluation, Fine-Tuning | OpenTelemetry, Azure Monitor, Built-in Evaluators |
| **Deployment** | Hosted Agents with Azure Developer CLI | Azure Developer CLI (azd), Hosted Agents |
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
│   ├── 4-bing-grounding.ipynb                 # Web search integration
│   ├── 5-agents-aisearch.ipynb                # Enterprise search
│   ├── 6-multi-agent-solution-with-workflows.ipynb
│   ├── 7-mcp-tools.ipynb                      # MCP integration
│   ├── 8-foundry-IQ-agents.ipynb              # 🧠 Foundry IQ - Agentic retrieval
│   └── 9-agent-memory-search.ipynb            # Memory patterns
│
├── 🤖⚙️ agent-framework/                       # Microsoft Agent Framework (Business use cases)
│   ├── agents/azure-ai-agents/                # 9 agent notebooks (1-9)
│   ├── context-providers/                     # 2 context/memory notebooks (1-2)
│   ├── middleware/                            # 9 interception patterns (1-9)
│   ├── observability/                         # 3 telemetry notebooks (1-3)
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
├── 🚀 hosted-agents/                          # Hosted Agent Deployment
│   ├── azure.yaml                             # azd project configuration
│   ├── README.md                              # Deployment guide
│   └── src/WebSearchAgent/                    # Web search agent
│       ├── agent.yaml                         # Agent definition
│       ├── main.py                            # Agent implementation
│       ├── Dockerfile                         # Container definition
│       └── requirements.txt                   # Agent dependencies
│
├── 🐳 .devcontainer/                          # Dev Container configuration
│   └── devcontainer.json                      # Container settings
│
├── .env.example                               # Environment template
├── requirements.in                            # Unpinned dependencies
├── requirements.txt                           # Pinned dependencies (pip-compile)
└── README.md                                  # This file
```

---

## 🚀 Getting Started

### Option A: Dev Container (Recommended) 🐳

For a consistent, pre-configured environment with all dependencies:

1. **Prerequisites**: Install [Docker](https://docker.com) and [VS Code](https://code.visualstudio.com) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

2. **Open in Container**:
   - Clone the repo and open in VS Code
   - Press `F1` → **Dev Containers: Reopen in Container**
   - Wait for the container to build (first time takes ~5 minutes)

3. **Ready to go!** All dependencies are pre-installed including:
   - Python 3.12 with all packages (frozen versions)
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
python --version  # Python 3.10+ required
```

#### Step 2: Environment Setup

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies (versions are pinned for consistency)
pip install -r requirements.txt
```

#### Step 3: Configure Environment Variables

1. Copy `.env.example` to `.env`
2. Update with your Azure resources:

```env
# Required
AI_FOUNDRY_PROJECT_ENDPOINT=https://your-project.services.ai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o

# Optional (for specific notebooks)
BING_CONNECTION_ID=/subscriptions/.../connections/bing
AZURE_AI_SEARCH_ENDPOINT=https://your-search.search.windows.net
```

### Step 4: Microsoft Foundry Setup

1. **Create Microsoft Foundry Resource** — [Azure Portal](https://portal.azure.com/#create/Microsoft.CognitiveServicesAIFoundry)
2. **Deploy Models** — `gpt-4o`, `gpt-4o-mini`, `text-embedding-3-large`
3. **Connect Services** — Azure AI Search, Bing Search, Application Insights

For detailed setup instructions, see [Microsoft Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/).

### Step 5: Required Azure RBAC Roles

Assign the following roles based on the notebooks you plan to run. Each role specifies whether it should be assigned to **your user identity** or to the **Project Managed Identity**.

#### 🔑 Core Roles (Required for All Notebooks)

| Role | Assignee | Resource | Purpose |
|------|----------|----------|---------|
| **Azure AI Developer** | User | AI Foundry Project | Create and manage agents, threads, and runs |
| **Cognitive Services OpenAI User** | User | AI Foundry Project | Access OpenAI model deployments |

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

#### ️ Role Assignment Commands

```powershell
# Get your user principal ID
$USER_PRINCIPAL_ID = (az ad signed-in-user show --query id -o tsv)

# Get resource scopes (replace with your values)
$PROJECT_SCOPE = "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<project>"
$STORAGE_SCOPE = "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<storage>"
$SEARCH_SCOPE = "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.Search/searchServices/<search>"

# ═══════════════════════════════════════════════════════════════
# USER ROLES
# ═══════════════════════════════════════════════════════════════

# Core roles (required for all notebooks)
az role assignment create --role "Azure AI Developer" --assignee $USER_PRINCIPAL_ID --scope $PROJECT_SCOPE
az role assignment create --role "Cognitive Services OpenAI User" --assignee $USER_PRINCIPAL_ID --scope $PROJECT_SCOPE

# Storage roles (for file search notebooks)
az role assignment create --role "Storage Blob Data Contributor" --assignee $USER_PRINCIPAL_ID --scope $STORAGE_SCOPE

# Search roles (for AI Search notebooks)
az role assignment create --role "Search Index Data Contributor" --assignee $USER_PRINCIPAL_ID --scope $SEARCH_SCOPE
az role assignment create --role "Search Index Data Reader" --assignee $USER_PRINCIPAL_ID --scope $SEARCH_SCOPE
az role assignment create --role "Search Service Contributor" --assignee $USER_PRINCIPAL_ID --scope $SEARCH_SCOPE

# ═══════════════════════════════════════════════════════════════
# MANAGED IDENTITY ROLES (⚠️ CRITICAL for Foundry IQ Agents)
# ═══════════════════════════════════════════════════════════════

# Get Project Managed Identity from Azure Portal:
# AI Foundry Project → Settings → Identity → Object (principal) ID
$PROJECT_MI_ID = "<PROJECT_MANAGED_IDENTITY_PRINCIPAL_ID>"

az role assignment create --role "Search Index Data Reader" --assignee $PROJECT_MI_ID --scope $SEARCH_SCOPE
```

> **⚠️ Critical Notes:**
> - **Managed Identity Role**: The `Search Index Data Reader` on the Project Managed Identity is **required** for `8-foundry-IQ-agents.ipynb` - without it, the MCP tool cannot query the knowledge base at runtime.
> - **Role Propagation**: Role assignments can take **5-10 minutes** to propagate. If you encounter permission errors, wait and retry.
> - **Storage Networking**: If you encounter a `403 Forbidden` error with file search, configure the storage account networking to allow access.  

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
| 4 | [Bing Grounding](azure-ai-agents/4-bing-grounding.ipynb) | Web search integration |
| 5 | [Agents + AI Search](azure-ai-agents/5-agents-aisearch.ipynb) | Enterprise search integration |
| 6 | [Multi-Agent Workflows](azure-ai-agents/6-multi-agent-solution-with-workflows.ipynb) | Collaborative AI systems |
| 7 | [MCP Tools](azure-ai-agents/7-mcp-tools.ipynb) | Model Context Protocol integration |
| 8 | [🧠 Foundry IQ Agents](azure-ai-agents/8-foundry-IQ-agents.ipynb) | **Revolutionary agentic retrieval** - Knowledge-grounded agents |
| 9 | [Agent Memory Search](azure-ai-agents/9-agent-memory-search.ipynb) | Persistent memory patterns |

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
| 7 | [Bing Grounding](agent-framework/agents/azure-ai-agents/7-azure-ai-with-bing-grounding.ipynb) | Web search integration using Bing Grounding |
| 8 | [Hosted MCP](agent-framework/agents/azure-ai-agents/8-azure-ai-with-hosted-mcp.ipynb) | Model Context Protocol server integration |
| 9 | [Multi-turn Threads](agent-framework/agents/azure-ai-agents/9-azure-ai-with-existing-multi-turn-thread.ipynb) | Managing multi-turn conversation threads |

#### 🧠 Context Providers (`context-providers/`)

| # | Notebook | Use Case |
|---|----------|----------|
| 1 | [Simple Context Provider](agent-framework/context-providers/1-simple-context-provider.ipynb) | Customer Profile Collection |
| 2 | [Azure AI Search Context](agent-framework/context-providers/2-azure-ai-search-context-agentic.ipynb) | Document-Based Decisions with RAG |

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

---

### 💼 Industry Use Cases

For 49 real-world FSI use cases (banking, insurance, investment) mapped to each notebook, see [USE-CASES.md](USE-CASES.md).

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
