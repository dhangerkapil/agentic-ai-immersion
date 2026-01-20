# 🤖 Microsoft Agent Framework Samples

Practical notebooks and reference material for building Microsoft Agent Framework solutions across agents, workflows, memory, middleware, and observability scenarios — all with **real-world business** use cases.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Running the Notebooks](#running-the-notebooks)
5. [Repository Guide](#repository-guide)
6. [Suggested Learning Path](#suggested-learning-path)
7. [Troubleshooting](#troubleshooting)
8. [Additional Resources](#additional-resources)

## Overview

The Microsoft Agent Framework is the next generation of tooling from the Semantic Kernel and AutoGen teams. It provides a unified programming model for building intelligent agents, multi-agent workflows, and connected tools in both Python and .NET. These samples showcase core scenarios ranging from single-agent chat to advanced orchestration with state management, custom memory, and telemetry.

All notebooks feature **business use cases** including application processing, compliance review, execution monitoring, customer service, and research workflows.

> The framework is currently in public preview. Expect APIs and package names to evolve.

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.10 or later |
| **Azure Subscription** | Access to Microsoft Foundry |
| **Azure CLI** | 2.60+ with active `az login` session |
| **Optional** | Redis (distributed threads), Application Insights (telemetry) |

## Environment Setup

1. **Install packages** — Install the preview roll-up package or specific integrations as needed.

2. **Configure environment variables** — Copy `.env.example` to `.env` and update with your Azure resources:
   - `AI_FOUNDRY_PROJECT_ENDPOINT` — Your Microsoft Foundry project endpoint
   - `AZURE_OPENAI_ENDPOINT` — Your Azure OpenAI endpoint
   - `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` — Model deployment name (e.g., gpt-4o)
   - Additional variables as needed: `BING_CONNECTION_ID`, `AZURE_AI_SEARCH_ENDPOINT`, Redis connection strings

3. **Verify authentication** — Run `az account show` to confirm the CLI is signed in and targeting the correct subscription.

## Running the Notebooks

1. Activate your Python virtual environment.
2. Open the notebook you want to explore and execute the cells in order.
3. Most notebooks include setup cells that validate credentials before the scenarios run.

---

## Repository Guide

### 📁 `agents/`

Single-agent patterns for Azure AI. See [agents/README.md](agents/README.md) for details.

| # | Notebook | Description |
|---|----------|-------------|
| 1 | `1-azure-ai-basic.ipynb` | Basic agent usage with automatic lifecycle management |
| 2 | `2-azure-ai-with-explicit-settings.ipynb` | Creating agents with explicit configuration |
| 3 | `3-azure-ai-with-existing-ai-agent.ipynb` | Working with pre-existing agents using agent IDs |
| 4 | `4-azure-ai-with-function-tools.ipynb` | Function tool integration patterns |
| 5 | `5-azure-ai-with-code-interpreter.ipynb` | Python code execution capabilities |
| 6 | `6-azure-ai-with-file-search.ipynb` | Document-based question answering |
| 7 | `7-azure-ai-with-bing-grounding.ipynb` | Web search integration using Bing |
| 8 | `8-azure-ai-with-hosted-mcp.ipynb` | Model Context Protocol (MCP) server integration |
| 9 | `9-azure-ai-with-existing-multi-turn-thread.ipynb` | Managing multi-turn conversation threads |

**Learning Path**: 1 (Basic) → 2 (Explicit Settings) → 4 (Function Tools) → 5 (Code Interpreter) → 7 (Bing Grounding) → 8 (MCP)

---

### 📁 `context-providers/`

Memory and context management with business use cases. See [context-providers/README.md](context-providers/README.md) for details.

| Notebook | Use Case | Key Concepts |
|----------|----------|--------------|
| `1-simple-context-provider.ipynb` | **Customer Profile Collection** | Custom context provider, structured data extraction |
| `2-azure-ai-search-context-agentic.ipynb` | **Application Review** | Azure AI Search, RAG, multi-hop reasoning |

**Learning Path**: Simple Context Provider → Azure AI Search RAG

---

### 📁 `threads/`

Conversation threading and persistence with business use cases. See [threads/README.md](threads/README.md) for details.

| Notebook | Use Case | Key Concepts |
|----------|----------|--------------|
| `1-custom-chat-message-store-thread.ipynb` | **Compliance Audit Trail** | Custom ChatMessageStoreProtocol |
| `2-redis-chat-message-store-thread.ipynb` | **Distributed Customer Sessions** | Redis persistence, scalable sessions |
| `3-suspend-resume-thread.ipynb` | **Request Processing** | Thread serialization, cross-session resume |

**Learning Path**: Custom Store → Suspend/Resume → Redis Store

---

### 📁 `middleware/`

Interception patterns for agents and workflows with business use cases. See [middleware/README.md](middleware/README.md) for details.

| Notebook | Use Case |
|----------|----------|
| `1-agent-and-run-level-middleware.ipynb` | Agent-level vs run-level middleware |
| `2-function-based-middleware.ipynb` | Function-based patterns |
| `3-class-based-middleware.ipynb` | Class-based inheritance |
| `4-decorator-middleware.ipynb` | **Resource Rebalancing** |
| `5-chat-middleware.ipynb` | **Customer Service Filtering** |
| `6-exception-handling-with-middleware.ipynb` | **Data Recovery** |
| `7-middleware-termination.ipynb` | **Compliance Screening** |
| `8-override-result-with-middleware.ipynb` | **Data Enrichment** |
| `9-shared-state-middleware.ipynb` | **Audit Trail** |

**Learning Path**: Agent/Run Level → Function-based → Class-based → Decorators → Chat → Exception Handling → Termination → Result Override → Shared State

---

### 📁 `observability/`

Operational telemetry with business use cases. See [observability/README.md](observability/README.md) for details.

| Notebook | Use Case | Key Concepts |
|----------|----------|--------------|
| `1-agent-with-foundry-tracing.ipynb` | **Execution Monitoring** | Manual Azure Monitor setup, custom spans |
| `2-azure-ai-agent-observability.ipynb` | **Customer Service Monitoring** | AzureAIAgentClient with auto-telemetry |
| `3-workflow-observability.ipynb` | **Processing Pipeline** | Multi-stage workflow tracing |

**Learning Path**: Foundry Tracing → Agent Observability → Workflow Observability

---

### 📁 `workflows/`

Graph-based orchestration with business use cases. See [workflows/README.md](workflows/README.md) for details.

| # | Notebook | Use Case | Pattern |
|---|----------|----------|---------|
| 1 | `1-azure-ai-agents-streaming.ipynb` | **Real-time Data Updates** | Streaming |
| 2 | `2-azure-chat-agents-streaming.ipynb` | **Customer Support Chat** | Streaming |
| 3 | `3-sequential-agents-loan-application.ipynb` | **Application Processing** | Sequential pipeline |
| 4 | `4-sequential-custom-executors-compliance.ipynb` | **Advisory with Compliance** | Custom executors |
| 5 | `5-credit-limit-with-human-input.ipynb` | **Approval Workflow** | Human-in-the-loop |
| 6 | `6-workflow-as-agent-human-in-the-loop-transaction-review.ipynb` | **High-Value Authorization** | Workflow-as-agent + escalation |
| 7 | `7-magentic-compliance-review-with-human-input.ipynb` | **Plan Compliance Review** | Magentic + Human approval |
| 8 | `8-magentic-investment-research.ipynb` | **Multi-Agent Research** | Magentic multi-agent |
| 9 | `9-workflow-as-agent-reflection-pattern.ipynb` | **Communication Quality** | Reflection pattern |

**Learning Path**: Streaming → Sequential → Human-in-the-loop → Magentic → Reflection

---

## Suggested Learning Path

| Step | Focus | Notebooks |
|------|-------|-----------|
| 1 | **Foundations** | `agents/azure-ai-agents/1-azure-ai-basic.ipynb` → `2-azure-ai-with-explicit-settings.ipynb` |
| 2 | **Persistence** | `threads/` notebooks — message storage and resume patterns |
| 3 | **Memory** | `context-providers/` — profile collection and RAG with Azure AI Search |
| 4 | **Tooling** | `agents/azure-ai-agents/4-azure-ai-with-function-tools.ipynb` → 8 (MCP integration) |
| 5 | **Workflows** | `workflows/` — 1-2 (streaming) → 3-4 (sequential) → 5-7 (human-in-the-loop) → 8 (Magentic) → 9 (Reflection) |
| 6 | **Observability** | `observability/` — tracing with Azure Monitor and Application Insights |
| 7 | **Middleware** | `middleware/` — interception patterns for enterprise applications |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Authentication failures** | Re-run `az login` and confirm Azure AI permissions |
| **Missing environment variables** | Verify `.env` mirrors the keys called out in notebook setup cells |
| **Package import errors** | Ensure `agent-framework` packages installed in the same interpreter as Jupyter |
| **Redis connectivity** | Update connection string and confirm service is reachable |
| **Application Insights delay** | Telemetry can take a few minutes; use Live Metrics Stream for real-time debugging |

## Additional Resources

- [Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
- [Azure AI Services](https://learn.microsoft.com/azure/ai-services/)
- [Azure Monitor OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-overview)

> Keep an eye on release notes in the official documentation for API or package updates while the framework remains in preview.
