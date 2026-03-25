# Azure Service Outline — Agentic AI Immersion Workshop

This document maps every Technology column entry from the 49 Industry Use Cases to the specific Azure service it represents. For each service, it describes what the service is, how mature it is, its core purpose, where to learn more, and exactly how the notebooks implement its features.

---

## Table of Contents

1. [Azure AI Foundry — AI Agents v2](#1-azure-ai-foundry--ai-agents-v2)
2. [Azure OpenAI Service — Code Interpreter](#2-azure-openai-service--code-interpreter)
3. [Azure AI Search](#3-azure-ai-search)
4. [Bing Search — Grounding with Bing Search](#4-bing-search--grounding-with-bing-search)
5. [Azure AI Foundry — File Search (Vector Stores + Blob Storage)](#5-azure-ai-foundry--file-search-vector-stores--blob-storage)
6. [Azure AI Foundry — Workflow Agents (Multi-Agent Workflows)](#6-azure-ai-foundry--workflow-agents-multi-agent-workflows)
7. [Azure AI Foundry — MCP Server (Foundry MCP)](#7-azure-ai-foundry--mcp-server-foundry-mcp)
8. [Azure AI Foundry IQ — Knowledge Bases (Agentic Retrieval)](#8-azure-ai-foundry-iq--knowledge-bases-agentic-retrieval)
9. [Azure AI Foundry — Memory Store (Agent Memory Search)](#9-azure-ai-foundry--memory-store-agent-memory-search)
10. [Microsoft Agent Framework](#10-microsoft-agent-framework)
11. [Azure Cache for Redis — Distributed Thread Storage](#11-azure-cache-for-redis--distributed-thread-storage)
12. [Magentic One — Multi-Agent Orchestration](#12-magentic-one--multi-agent-orchestration)
13. [Azure Monitor + Application Insights + OpenTelemetry](#13-azure-monitor--application-insights--opentelemetry)
14. [Azure AI Evaluation Service — Built-in Evaluators](#14-azure-ai-evaluation-service--built-in-evaluators)
15. [Azure AI Red Teaming Service](#15-azure-ai-red-teaming-service)

---

## 1. Azure AI Foundry — AI Agents v2

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Financial Services Advisor | `azure-ai-agents/1-basics.ipynb` |
| Financial Advisor Basics | `agent-framework/agents/azure-ai-agents/1-azure-ai-basic.ipynb` |
| Investment Portfolio Management | `agent-framework/agents/azure-ai-agents/2-azure-ai-with-explicit-settings.ipynb` |
| Persistent Financial Advisor | `agent-framework/agents/azure-ai-agents/3-azure-ai-with-existing-ai-agent.ipynb` |
| Banking Operations Center | `agent-framework/agents/azure-ai-agents/4-azure-ai-with-function-tools.ipynb` |
| Loan Application Discussion | `agent-framework/agents/azure-ai-agents/9-azure-ai-with-existing-multi-turn-thread.ipynb` |

### Service Description

Azure AI Foundry is Microsoft's unified platform for building, deploying, and managing AI applications and agents at enterprise scale. The **AI Agents v2** service within Foundry provides a managed runtime for conversational agents that can call tools, maintain conversation history, and leverage connected Azure services — without requiring developers to manage infrastructure.

Agents are defined declaratively using `PromptAgentDefinition`, versioned in a project registry, and invoked through an OpenAI-compatible Responses/Conversations API. The platform handles token context management, tool dispatch, and retry logic automatically.

### Maturity

**Generally Available (GA)** — Azure AI Foundry (formerly Azure Machine Learning Studio + Azure OpenAI Studio) reached GA status. The AI Agents v2 SDK (`azure-ai-projects`) is in active development with rapid iteration; preview features are clearly labeled in the portal.

### Core Use Case

Managed hosting and lifecycle management of AI agents — from creation and versioning through multi-turn conversation execution and tool invocation — within a governed enterprise project environment.

### Microsoft Learn Reference

[Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)
[Azure AI Agents Overview](https://learn.microsoft.com/en-us/azure/ai-services/agents/overview)

### How the Notebooks Implement This Service

**`1-basics.ipynb`** establishes the canonical pattern for all other notebooks:
- Authenticates via `InteractiveBrowserCredential` or `AzureCliCredential`
- Initializes `AIProjectClient(endpoint=AI_FOUNDRY_PROJECT_ENDPOINT, credential=...)`
- Defines agent behavior declaratively: `PromptAgentDefinition(model=deployment_name, instructions=system_prompt)`
- Registers a versioned agent: `project_client.agents.create_version(agent_name=..., definition=...)`
- Acquires a conversation-aware OpenAI client: `project_client.get_openai_client()`
- Conducts multi-turn dialogue: `openai_client.conversations.create()` + `openai_client.responses.create()`

**Agent Framework notebooks** extend this by wrapping `AIProjectClient` in `AzureAIAgentClient`, which adds the Agent Framework's middleware, thread management, and observability layers while still delegating execution to the same Foundry Agents v2 runtime.

---

## 2. Azure OpenAI Service — Code Interpreter

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Loan & Portfolio Calculator | `azure-ai-agents/2-code-interpreter.ipynb` |
| Financial Analytics Dashboard | `agent-framework/agents/azure-ai-agents/5-azure-ai-with-code-interpreter.ipynb` |

### Service Description

Code Interpreter is a sandboxed Python execution environment provided as a built-in tool within the Azure AI Agents runtime. When an agent is equipped with Code Interpreter, the model can autonomously write and execute Python code, process uploaded files, perform multi-step computations, and generate charts — all within an isolated compute environment managed by Azure. Results are streamed back to the agent as structured output.

### Maturity

**Generally Available (GA)** — Code Interpreter has been available in Azure OpenAI Assistants and Agents APIs since their public release.

### Core Use Case

On-demand code execution for numerical computation, data analysis, file processing, and visualization — enabling agents to move beyond language generation into grounded, verifiable calculation.

### Microsoft Learn Reference

[Code Interpreter Tool in Azure AI Agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/code-interpreter)

### How the Notebooks Implement This Service

**`2-code-interpreter.ipynb`** attaches the tool during agent creation:
```python
from azure.ai.projects.models import CodeInterpreterTool, CodeInterpreterToolAuto

tool = CodeInterpreterTool(container=CodeInterpreterToolAuto())
project_client.agents.create_version(
    agent_name="loan-calculator",
    definition=PromptAgentDefinition(model=..., instructions=..., tools=[tool])
)
```
The agent then receives natural-language requests ("calculate a 30-year mortgage amortization schedule for $450,000 at 6.5%") and autonomously generates Python code, executes it in the sandbox, and returns results. The notebooks exercise: loan payment formulas, compound interest calculations, portfolio allocation analysis, and amortization table generation.

**`5-azure-ai-with-code-interpreter.ipynb`** follows the identical pattern through the Agent Framework wrapper, exercising the same sandboxed execution but within a middleware-enabled pipeline that adds audit logging around each code execution event.

---

## 3. Azure AI Search

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Banking Products Catalog | `azure-ai-agents/5-agents-aisearch.ipynb` |
| Loan Underwriting & Risk Assessment | `agent-framework/context-providers/2-azure-ai-search-context-agentic.ipynb` |

### Service Description

Azure AI Search (formerly Azure Cognitive Search) is a cloud-native search service that combines full-text search, vector search, and semantic ranking into a single index. In agentic AI workflows it serves as the knowledge backbone: documents are ingested with vector embeddings, indexed with configurable HNSW (Hierarchical Navigable Small World) graphs, and queried at runtime by agents using hybrid or semantic retrieval modes. The service integrates natively with Azure OpenAI for integrated vectorization — meaning embeddings can be generated at query time without client-side vector computation.

### Maturity

**Generally Available (GA)** — Vector search and semantic ranker are GA. The agentic "knowledge base" wrapping used in context providers is in active preview.

### Core Use Case

Enterprise knowledge retrieval — enabling agents to search, filter, and rank large document corpora using natural language queries with semantic understanding and vector similarity.

### Microsoft Learn Reference

[Azure AI Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
[Vector Search in Azure AI Search](https://learn.microsoft.com/en-us/azure/search/vector-search-overview)
[Semantic Ranking](https://learn.microsoft.com/en-us/azure/search/semantic-search-overview)

### How the Notebooks Implement This Service

**`5-agents-aisearch.ipynb`** builds a full vector search pipeline from scratch:
```python
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile, AzureOpenAIVectorizer,
    SemanticConfiguration, SemanticSearch
)
from azure.ai.projects.models import AzureAISearchAgentTool, AzureAISearchQueryType
```
Steps: (1) creates a search index with HNSW vector profile and integrated Azure OpenAI vectorizer, (2) generates embeddings for banking product descriptions using `openai_client.embeddings.create()`, (3) uploads documents with pre-computed vectors via `search_client.upload_documents()`, (4) attaches the index to the agent as `AzureAISearchAgentTool` with `query_type=AzureAISearchQueryType.SEMANTIC`, enabling semantic re-ranking of vector results.

**`2-azure-ai-search-context-agentic.ipynb`** uses the Agent Framework's `AzureAISearchContextProvider` with "agentic mode" — the search provider autonomously plans sub-queries for complex multi-hop questions (e.g., "is this applicant eligible based on income thresholds AND credit history?"), executes multiple searches, and synthesizes a single grounded context object for the agent. Index fields use 3072-dimension vectors from `text-embedding-3-large`.

---

## 4. Bing Search — Grounding with Bing Search

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Financial Market Research | `azure-ai-agents/4-bing-grounding.ipynb` |
| Financial Market Research Portal | `agent-framework/agents/azure-ai-agents/7-azure-ai-with-bing-grounding.ipynb` |

### Service Description

Grounding with Bing Search is a managed Azure connection that lets AI Agents query the live Bing web index in real time. Unlike static document retrieval, Bing grounding brings current information — today's market prices, breaking regulatory news, real-time interest rates — into agent responses. The connection is configured in the Azure AI Foundry portal and referenced at runtime via a named connection ID, keeping API keys out of application code.

### Maturity

**Generally Available (GA)** — Bing grounding shipped as a first-class tool in the Azure AI Agents SDK. The underlying Bing Search API is a mature, long-standing Azure service.

### Core Use Case

Real-time web-grounded responses for agents that must answer questions about current events, live market data, or any information that changes faster than a static knowledge base can be refreshed.

### Microsoft Learn Reference

[Grounding with Bing Search — Azure AI Agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/bing-grounding)

### How the Notebooks Implement This Service

**`4-bing-grounding.ipynb`** configures the connection at runtime:
```python
from azure.ai.projects.models import (
    BingGroundingAgentTool,
    BingGroundingSearchToolParameters,
    BingGroundingSearchConfiguration
)

conn = project_client.connections.get(name=bing_conn_name)
tool = BingGroundingAgentTool(
    bing_grounding=BingGroundingSearchToolParameters(
        search_configurations=[BingGroundingSearchConfiguration(connection_id=conn.id)]
    )
)
```
The agent is then asked questions like "What are current 10-year Treasury yields?" and "Summarize today's top financial market news." Bing search results are grounded into the response, with source attribution surfaced in the output. The notebook also exercises freshness-sensitive queries where a static RAG approach would produce stale answers.

**`7-azure-ai-with-bing-grounding.ipynb`** wraps the same Bing tool within the Agent Framework, adding middleware that intercepts each response to append regulatory disclaimers ("Market data is for informational purposes only…") — demonstrating how Bing's live data capability is governed by enterprise compliance layers.

---

## 5. Azure AI Foundry — File Search (Vector Stores + Blob Storage)

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Banking Document Search | `azure-ai-agents/3-file-search.ipynb` |
| Loan Policy Document Search | `agent-framework/agents/azure-ai-agents/6-azure-ai-with-file-search.ipynb` |

### Service Description

File Search is a managed document retrieval tool within Azure AI Agents that handles the entire RAG pipeline automatically: upload files → chunk → embed → store in a managed vector store → query at agent runtime. Backed by Azure Blob Storage for file persistence and an internal vector store for semantic retrieval, it removes the need to manually configure Azure AI Search for document Q&A scenarios. It is optimized for scenarios where documents are uploaded directly (PDFs, Word files, policy documents) rather than crawled from an existing corpus.

### Maturity

**Generally Available (GA)** — File Search shipped with the Azure AI Agents GA release. The underlying vector store infrastructure is managed by the Foundry service.

### Core Use Case

Rapid document Q&A — upload compliance documents, loan policies, or regulatory guides and immediately query them through an agent with semantic search, without configuring a separate search service.

### Microsoft Learn Reference

[File Search Tool — Azure AI Agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/file-search)

### How the Notebooks Implement This Service

**`3-file-search.ipynb`** demonstrates the complete upload-to-query flow:
```python
from azure.ai.projects.models import FileSearchTool

# Create a managed vector store
store = openai_client.vector_stores.create(name="loan-policy-store")

# Upload files with automatic chunking, embedding, and indexing
openai_client.vector_stores.files.upload_and_poll(
    vector_store_id=store.id, file=open("loan_policy.pdf", "rb")
)

# Attach to agent
tool = FileSearchTool(vector_store_ids=[store.id])
```
The notebook uploads FSI-relevant documents (loan policies, banking regulations, compliance guides) and queries them with domain questions like "What are the income verification requirements for a jumbo loan?" The `upload_and_poll()` call blocks until indexing completes, ensuring the agent can query immediately after upload. Files are stored in Azure Blob Storage under the Foundry project's managed storage account — this is why the `Storage Blob Data Contributor` RBAC role is required.

---

## 6. Azure AI Foundry — Workflow Agents (Multi-Agent Workflows)

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Insurance Claims Processing | `azure-ai-agents/6-multi-agent-solution-with-workflows.ipynb` |

### Service Description

Workflow Agents is a declarative multi-agent orchestration capability within Azure AI Foundry. Developers define an agent workflow as a YAML document that specifies a sequence of steps — invoking specialist agents, setting variables, branching on conditions, and ending the conversation — and the Foundry runtime executes these steps server-side, managing inter-agent communication and shared context automatically. This eliminates the need for client-side orchestration code and enables durable, resumable multi-agent pipelines.

### Maturity

**Public Preview** — Workflow Agents is a newer addition to Azure AI Foundry. The declarative YAML schema and `WorkflowAgentDefinition` API are actively evolving.

### Core Use Case

Server-side orchestration of multi-agent pipelines where each agent is a specialist (e.g., intake, validation, underwriting, approval) and the workflow runtime manages handoffs, shared state, and sequencing.

### Microsoft Learn Reference

[Workflow Agents — Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/multi-agent)

### How the Notebooks Implement This Service

**`6-multi-agent-solution-with-workflows.ipynb`** builds a three-agent insurance claims pipeline:
```python
from azure.ai.projects.models import WorkflowAgentDefinition

workflow_yaml = """
actions:
  - type: SetVariable
    name: claim_id
    value: "{{ inputs.claim_id }}"
  - type: InvokeAzureAgent
    agent_name: claims-intake-agent
    ...
  - type: InvokeAzureAgent
    agent_name: claims-validation-agent
    ...
  - type: InvokeAzureAgent
    agent_name: payout-decision-agent
    ...
  - type: EndConversation
"""
workflow_agent = project_client.agents.create_version(
    agent_name="claims-workflow",
    definition=WorkflowAgentDefinition(workflow=workflow_yaml)
)
```
The notebook streams workflow execution events using `openai_client.responses.create(stream=True)`, consuming `WORKFLOW_ACTION` events (each step's status) and `MESSAGE` items (agent outputs). The three specialist agents — intake, validation, payout — each have their own instructions and tools, and the YAML workflow controls the sequencing, passing claim data between them via shared conversation context.

---

## 7. Azure AI Foundry — MCP Server (Foundry MCP)

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Platform Operations Assistant | `azure-ai-agents/7-mcp-tools.ipynb` |
| Documentation Research Assistant | `agent-framework/agents/azure-ai-agents/8-azure-ai-with-hosted-mcp.ipynb` |

### Service Description

The Azure AI Foundry MCP Server exposes Foundry's own management APIs as Model Context Protocol (MCP) tools. MCP is an open protocol that standardizes how AI models discover and call external tools. The Foundry MCP Server (`https://mcp.ai.azure.com/sse`) provides tools for: browsing the Azure AI model catalog, managing model deployments, creating evaluations, listing knowledge bases, and managing agent registries — all accessible to an agent at runtime over a Server-Sent Events (SSE) transport. "Hosted MCP" extends this concept to externally hosted tool servers accessible via URL.

### Maturity

**Public Preview** — MCP tooling in Azure AI Agents is in active preview. The MCP protocol itself is an emerging open standard gaining rapid industry adoption.

### Core Use Case

Enabling agents to introspect and manage the AI platform itself — model catalog browsing, deployment orchestration, evaluation pipeline management — through a standardized, discoverable tool protocol.

### Microsoft Learn Reference

[MCP Tools — Azure AI Agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/model-context-protocol)
[Azure AI Foundry MCP Server](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/model-context-protocol)

### How the Notebooks Implement This Service

**`7-mcp-tools.ipynb`** configures the MCP connection and handles the approval flow:
```python
from azure.ai.projects.models import MCPTool
from openai.types.responses.response_input_param import McpApprovalResponse

tool = MCPTool(
    server_label="foundry-mcp",
    server_url="https://mcp.ai.azure.com/sse",
    project_connection_id=project_client.connection_id
)
```
When the agent calls an MCP tool, the response stream includes an approval request that the application must explicitly confirm before execution proceeds — the notebook implements a `McpApprovalResponse` handler for this. The agent is used for operations like "list available GPT-4o deployments," "create an evaluation for this agent," and "what models are available in the East US region?" — all resolved via Foundry MCP tool calls.

**`8-azure-ai-with-hosted-mcp.ipynb`** uses the same `MCPTool` pattern but points to an externally hosted documentation server, enabling the agent to query cloud-hosted technical documentation at runtime.

---

## 8. Azure AI Foundry IQ — Knowledge Bases (Agentic Retrieval)

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Multi-Source Fraud Investigation | `azure-ai-agents/8-foundry-IQ-agents.ipynb` |
| Loan Underwriting & Risk Assessment | `agent-framework/context-providers/2-azure-ai-search-context-agentic.ipynb` |

### Service Description

Foundry IQ is Azure AI Foundry's agentic knowledge retrieval layer. It wraps Azure AI Search indexes in a higher-order "Knowledge Base" abstraction that supports multi-index retrieval, autonomous query planning, and cross-source reasoning. Rather than executing a single search per question, an IQ-enabled agent decomposes complex queries into sub-queries across multiple knowledge sources, synthesizes the results, and constructs grounded answers. This makes it suitable for regulatory compliance checks that require correlating multiple policy documents, or fraud investigations that must cross-reference transaction patterns, regulations, and procedural guidelines simultaneously.

### Maturity

**Public Preview** — Foundry IQ and the Knowledge Bases API are in active preview. The underlying Azure AI Search service is GA; the IQ orchestration layer is newer.

### Core Use Case

Multi-source agentic retrieval for complex enterprise queries — where the answer requires synthesizing information from several distinct document collections or knowledge domains simultaneously.

### Microsoft Learn Reference

[Foundry IQ Knowledge Bases](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/knowledge-bases)
[Agentic Retrieval with Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-agentic-retrieval-concept)

### How the Notebooks Implement This Service

**`8-foundry-IQ-agents.ipynb`** builds fraud investigation knowledge sources backed by Azure AI Search:
- Creates multiple search indexes with 3072-dimension vectors from `text-embedding-3-large`
- Processes documents in batches: `openai_client.embeddings.create(input=batch, model=embedding_deployment)`
- Registers indexes as Knowledge Sources in the Foundry IQ service
- Creates three specialist agents — policy analysis, risk assessment, claims processing — each connected to their respective knowledge bases
- At query time, agents autonomously decompose fraud investigation questions into targeted sub-queries across each knowledge base, returning a synthesized, grounded answer

**`2-azure-ai-search-context-agentic.ipynb`** exercises the same capability through the Agent Framework's `AzureAISearchContextProvider` in agentic mode. The context provider is configured with `mode="agentic"`, enabling it to plan multi-step retrieval for underwriting eligibility questions that require correlating income criteria, credit score thresholds, and property appraisal guidelines from separate index partitions.

---

## 9. Azure AI Foundry — Memory Store (Agent Memory Search)

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Personalized Banking Assistant | `azure-ai-agents/9-agent-memory-search.ipynb` |

### Service Description

The Azure AI Foundry Memory Store is a managed service that gives agents persistent, semantic memory across conversation sessions. It extracts and stores user profile facts and chat summaries automatically after conversations, then recalls relevant memories at the start of new sessions via semantic similarity search. Memory stores are backed by Azure OpenAI embeddings for similarity retrieval and Azure OpenAI chat models for summary generation — both managed by the Foundry service with no external infrastructure required.

### Maturity

**Public Preview** — The Memory Store API (`azure.ai.projects.models.MemoryStoreDefaultDefinition`, `MemorySearchTool`) is a recently introduced preview capability in Azure AI Agents v2.

### Core Use Case

Cross-session personalization for AI agents — remembering customer preferences, past interactions, and profile facts so agents can provide continuity-aware responses without requiring explicit context re-injection at each session start.

### Microsoft Learn Reference

[Agent Memory — Azure AI Agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/tools/agent-memory)

### How the Notebooks Implement This Service

**`9-agent-memory-search.ipynb`** creates a full memory lifecycle:
```python
from azure.ai.projects.models import (
    MemoryStoreDefaultDefinition, MemorySearchTool, MemoryStoreDefaultOptions
)

# Create memory store backed by OpenAI models
memory_store = project_client.memory_stores.create(
    MemoryStoreDefaultDefinition(
        chat_model=chat_deployment,
        embedding_model=embedding_deployment,
        options=MemoryStoreDefaultOptions(
            user_profile_enabled=True,
            chat_summary_enabled=True
        )
    )
)

# Attach memory retrieval to agent
tool = MemorySearchTool(
    memory_store_name=memory_store.name,
    scope="user",
    update_delay=30  # seconds of inactivity before memory extraction
)
```
The notebook simulates a banking customer across two sessions: Session 1 establishes preferences ("I prefer conservative investments," "I have two children," "I'm planning for retirement in 10 years"). After an idle period, the memory store automatically extracts a user profile and chat summary. Session 2 opens a fresh conversation — the agent immediately recalls the customer's conservative risk preference and retirement timeline without the user re-stating them, demonstrating continuity-aware personalization.

---

## 10. Microsoft Agent Framework

### Use Cases Covered

All 35 use cases in the `agent-framework/` directory, including all middleware, thread management, observability, streaming/sequential/human-in-the-loop workflow notebooks.

| Technology Tag | Notebooks |
|---------------|-----------|
| Agent Framework (core) | `agents/azure-ai-agents/1-9` |
| Agent Framework, Context Providers | `context-providers/1-2` |
| Agent Framework, Agent/Function/Class/Decorator/Chat Middleware | `middleware/1-9` |
| Agent Framework, Foundry Tracing / Azure Monitor / Workflow Observability | `observability/1-3` |
| Agent Framework, Custom/Redis Message Store, Thread Suspend/Resume | `threads/1-3` |
| Agent Framework, Streaming/Sequential/Custom Executors/Human-in-the-Loop/Human Escalation/Reflection | `workflows/1-9` |

### Service Description

The Microsoft Agent Framework (distributed as the `microsoft-agents-*` Python packages, built on Semantic Kernel) is an open-source application-layer orchestration framework for building enterprise AI agents. It sits above the Azure AI Agents runtime and provides: a middleware pipeline (analogous to ASP.NET middleware), pluggable thread/message storage, observable workflow execution, streaming support, human-in-the-loop approval gates, and multi-agent workflow patterns (sequential, branching, reflection). It is not a separate Azure service with its own resource type — it is a client-side framework that calls Azure AI Agents v2 and Azure OpenAI APIs.

### Maturity

**Public Preview / Rapid Development** — The Microsoft Agent Framework is under active development alongside Azure AI Foundry. APIs are subject to change across minor releases.

### Core Use Case

Enterprise-grade agent application development — providing the cross-cutting concerns (compliance middleware, audit logging, PII redaction, human approval gates, distributed session storage) that production FSI and other regulated industry deployments require on top of the raw Agents API.

### Microsoft Learn Reference

[Microsoft Agent Framework Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/agent-framework)
[Semantic Kernel Agents](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/)

### How the Notebooks Implement This Service

**Middleware notebooks (`middleware/1-9`)** demonstrate how the framework's pipeline intercepts every agent request and response:
- `1-agent-and-run-level-middleware.ipynb`: registers middleware at agent-level and run-level to emit compliance audit records for every transaction
- `5-chat-middleware.ipynb`: implements PII redaction (strips account numbers from outbound messages) and sensitive-query blocking
- `7-middleware-termination.ipynb`: terminates pipeline execution early when prohibited transaction patterns are detected
- `8-override-result-with-middleware.ipynb`: post-processes agent responses to append mandatory regulatory disclaimers

**Thread notebooks (`threads/1-3`)** show pluggable message storage:
- `1-custom-chat-message-store-thread.ipynb`: implements a custom `IChatMessageStore` backed by a compliance-approved database
- `3-suspend-resume-thread.ipynb`: serializes thread state, suspends it (simulating a multi-day claims process), and resumes from the persisted checkpoint

**Workflow notebooks (`workflows/1-9`)** cover orchestration patterns:
- Streaming workflows: real-time token streaming to front-end via `run_stream()`
- Sequential workflows: linear agent chains where output N feeds input N+1
- Human-in-the-loop: `5-credit-limit-with-human-input.ipynb` and `6-workflow-as-agent-human-in-the-loop-transaction-review.ipynb` pause execution, surface a decision to a human approver, then resume
- Reflection pattern: `9-workflow-as-agent-reflection-pattern.ipynb` uses a critic agent to iteratively improve communication quality

---

## 11. Azure Cache for Redis — Distributed Thread Storage

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Distributed Customer Session Management | `agent-framework/threads/2-redis-chat-message-store-thread.ipynb` |

### Service Description

Azure Cache for Redis is a fully managed, in-memory data store based on the open-source Redis software. In the context of AI agents, it serves as a distributed message/thread store — persisting conversation history across multiple application instances, enabling horizontal scaling of stateful agent deployments. The Agent Framework integrates with Redis through `RedisChatMessageStore`, which maps each conversation thread to a Redis key with configurable message-count limits and TTL-based expiry.

### Maturity

**Generally Available (GA)** — Azure Cache for Redis is a mature, production-grade service. The Agent Framework's `RedisChatMessageStore` integration is in preview alongside the broader framework.

### Core Use Case

Horizontal scaling of stateful agent conversations — multiple application instances share a Redis-backed message store so any instance can continue any customer's conversation, with automatic session persistence surviving pod restarts or deployment rollouts.

### Microsoft Learn Reference

[Azure Cache for Redis Documentation](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/)

### How the Notebooks Implement This Service

**`2-redis-chat-message-store-thread.ipynb`** demonstrates per-thread Redis storage with the Agent Framework:
```python
from microsoft_agents.threads import RedisChatMessageStore, AgentThread

store = RedisChatMessageStore(
    redis_url="redis://localhost:6379",
    thread_id=customer_session_id,
    max_messages=50  # sliding window — older messages are trimmed
)
thread = AgentThread(message_store=store)
response = await agent_client.run(query, thread=thread)
```
The notebook simulates a banking customer service scenario where three separate agent instances handle messages in the same conversation. Each instance reads from and writes to the shared Redis store, demonstrating that conversation continuity is preserved across instance boundaries. The `max_messages` sliding window prevents unbounded memory growth in long customer sessions. After the session, `store.clear()` removes the Redis key, satisfying data retention compliance requirements.

---

## 12. Magentic One — Multi-Agent Orchestration

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Investment Research with Compliance | `agent-framework/workflows/7-magentic-compliance-review-with-human-input.ipynb` |
| Investment Research Report Generation | `agent-framework/workflows/8-magentic-investment-research.ipynb` |

### Service Description

Magentic One is Microsoft Research's multi-agent orchestration framework, integrated into the Microsoft Agent Framework as `MagenticBuilder`. It implements an "orchestrator + specialist agents" pattern where a central orchestrator agent dynamically assigns tasks to specialist agents, tracks progress, and synthesizes a final result. Unlike static sequential workflows, Magentic orchestration is adaptive — the orchestrator replans if agents stall, hit errors, or produce incomplete outputs. The framework supports human review gates via `.with_plan_review()` that pause execution for compliance inspection before the plan runs.

### Maturity

**Public Preview** — Magentic One was published by Microsoft Research and is being productized within the Agent Framework. The API surface (particularly `MagenticBuilder`, `MagenticPlanReviewRequest`) is actively evolving.

### Core Use Case

Dynamic multi-agent research and analysis pipelines — where multiple specialist agents (market researcher, quantitative analyst, compliance reviewer) must collaborate on open-ended tasks that cannot be fully pre-planned as a static workflow.

### Microsoft Learn Reference

[Magentic One Overview](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/magentic-one)
[Magentic One Research Paper](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/)

### How the Notebooks Implement This Service

**`7-magentic-compliance-review-with-human-input.ipynb`** adds a human compliance gate:
```python
from microsoft_agents.workflows.magentic import MagenticBuilder

workflow = (
    MagenticBuilder()
    .participants([market_researcher_agent, quant_analyst_agent])
    .with_standard_manager(
        agent=orchestrator_agent,
        max_round_count=10,
        max_stall_count=3,
        max_reset_count=2
    )
    .with_plan_review()   # pauses before execution for human approval
    .build()
)
```
When the orchestrator proposes a research plan, a `MagenticPlanReviewRequest` event fires. The notebook handles this interactively — the compliance officer can `event_data.approve()` to proceed or `event_data.revise(feedback="Exclude derivatives analysis from scope")` to send the plan back for revision.

**`8-magentic-investment-research.ipynb`** runs the full research pipeline without the human gate, letting the orchestrator autonomously coordinate the market researcher (news and trend analysis) and quant analyst (quantitative metrics and risk ratios) to produce a consolidated investment research report.

---

## 13. Azure Monitor + Application Insights + OpenTelemetry

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Wealth Management Advisory Monitoring | `observability-and-evaluations/1-telemetry.ipynb` |
| Trade Execution Monitoring | `agent-framework/observability/1-agent-with-foundry-tracing.ipynb` |
| Customer Service Monitoring | `agent-framework/observability/2-azure-ai-agent-observability.ipynb` |
| Loan Processing Pipeline Monitoring | `agent-framework/observability/3-workflow-observability.ipynb` |

### Service Description

**Azure Monitor** is the unified observability platform for Azure, providing metrics, logs, and traces for all Azure resources. **Application Insights** is Azure Monitor's application performance management (APM) layer, providing distributed tracing, live metrics, and query tools (Kusto-based Log Analytics). **OpenTelemetry** is the CNCF open standard for instrumentation — Azure's `azure-monitor-opentelemetry` package implements OpenTelemetry's SDK and exports traces/metrics to Application Insights automatically.

For AI agents, this stack captures: token usage, request latency, tool invocation counts, error rates, custom business attributes (client ID, query category, compliance flags), and full prompt/response content for audit trails.

### Maturity

**Generally Available (GA)** — Azure Monitor and Application Insights are mature, production-grade services. The `azure-monitor-opentelemetry` Python package is GA. AI-specific telemetry attributes (token counts, model names) are being standardized by the OpenTelemetry GenAI working group.

### Core Use Case

End-to-end observability for AI agent systems — capturing latency, cost (via token tracking), quality signals, compliance audit trails, and real-time error alerting across agent workflows.

### Microsoft Learn Reference

[Azure Monitor Overview](https://learn.microsoft.com/en-us/azure/azure-monitor/overview)
[Application Insights for Python](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opencensus-python)
[OpenTelemetry for Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable)
[Tracing in Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/trace-agents)

### How the Notebooks Implement This Service

All observability notebooks share a setup pattern:
```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

conn_str = await project_client.telemetry.get_application_insights_connection_string()
configure_azure_monitor(connection_string=conn_str)
tracer = trace.get_tracer(__name__)
```

**`1-telemetry.ipynb`** adds rich business context to spans:
```python
with tracer.start_as_current_span("wealth-advisory-query", kind=SpanKind.CLIENT) as span:
    span.set_attribute("client.id", client_id)
    span.set_attribute("query.category", "portfolio_rebalancing")
    span.set_attribute("response.latency_ms", elapsed)
    span.set_attribute("compliance.disclaimer_included", True)
```
The full prompt and response text are captured as span attributes, creating an immutable audit trail viewable in Application Insights Transaction Search and the Azure AI Foundry tracing portal.

**`1-agent-with-foundry-tracing.ipynb`** (Agent Framework) instruments trade execution workflows, correlating custom spans with the Agent Framework's automatic instrumentation to produce end-to-end traces that include both framework-level events (middleware execution, thread persistence) and business-level context (trade ID, amount, approval status).

---

## 14. Azure AI Evaluation Service — Built-in Evaluators

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Loan Advisory Quality Testing | `observability-and-evaluations/2-agent-evaluation.ipynb` |
| Banking Assistant Evaluation | `observability-and-evaluations/3-agent-evaluation-with-function-tools.ipynb` |
| Banking Operations Tool Validation | `observability-and-evaluations/4-tool-call-accuracy-evaluation.ipynb` |

### Service Description

The Azure AI Evaluation Service provides managed evaluation runs for AI agents and models, accessible through the OpenAI Evals API exposed by Azure AI Foundry. Developers define test datasets and evaluation criteria using a library of built-in evaluators — covering safety (`builtin.violence`, `builtin.hate_unfairness`), quality (`builtin.fluency`, `builtin.groundedness`, `builtin.relevance`), and task adherence (`builtin.task_adherence`, `builtin.tool_call_accuracy`). Evaluation runs are asynchronous, polled for completion, and produce item-level scores with a summary report accessible from the AI Foundry portal.

### Maturity

**Generally Available (GA)** — The Azure AI Evaluation SDK (`azure-ai-evaluation`) and the evals API through AI Foundry are generally available for safety and quality evaluators. Tool call accuracy evaluators are in active preview.

### Core Use Case

Systematic, automated quality assurance for AI agents — measuring safety, factual groundedness, response quality, and correct tool selection across a test dataset, enabling regression testing of agent behavior across model updates and prompt changes.

### Microsoft Learn Reference

[Evaluate Azure AI Agents](https://learn.microsoft.com/en-us/azure/ai-services/agents/how-to/evaluate-agents)
[Azure AI Evaluation SDK](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/evaluate-generative-ai-app)

### How the Notebooks Implement This Service

**`2-agent-evaluation.ipynb`** runs built-in safety and quality evaluators:
```python
eval_obj = openai_client.evals.create(
    name="loan-advisor-eval",
    data_source_config=DataSourceConfigCustom(
        item_schema={"type": "object", "properties": {"query": {"type": "string"}}}
    ),
    testing_criteria=[
        {"type": "builtin.violence"},
        {"type": "builtin.fluency"},
        {"type": "builtin.task_adherence"}
    ]
)
run = openai_client.evals.runs.create(eval_id=eval_obj.id, data_source=test_dataset)

# Poll for completion (5-second intervals)
while run.status not in ["completed", "failed"]:
    time.sleep(5)
    run = openai_client.evals.runs.retrieve(eval_id=eval_obj.id, run_id=run.id)

items = openai_client.evals.runs.output_items.list(eval_id=eval_obj.id, run_id=run.id)
```
Test queries cover FSI scenarios: mortgage guidance, APR explanations, credit requirements. Each response is scored independently, with aggregate pass/fail rates and a portal report URL for drill-down analysis.

**`4-tool-call-accuracy-evaluation.ipynb`** uses `builtin.tool_call_accuracy` to verify that the banking agent selects the correct tool (balance inquiry vs. transaction history vs. loan calculator) for each query type — critical for validating that tool routing logic is correct before production deployment.

---

## 15. Azure AI Red Teaming Service

### Use Cases Covered

| Use Case | Notebook |
|----------|----------|
| Banking AI Security Assessment | `observability-and-evaluations/5-red-team-security-testing.ipynb` |

### Service Description

The Azure AI Red Teaming Service is a managed adversarial testing service that systematically probes AI models and agents for safety and security vulnerabilities using automated attack strategies. It applies encoding-based obfuscation (Base64, Morse code, Caesar cipher, Unicode confusables), multi-turn manipulation (crescendo escalation, jailbreak chaining), and direct adversarial prompts across configurable risk categories. Results include per-category vulnerability scores, severity classifications, and a comprehensive findings report — all managed server-side without requiring a local attack framework.

### Maturity

**Public Preview** — Azure AI Red Teaming (`azure.ai.projects.models.RedTeam`) is a newer service within Azure AI Foundry, released as part of Responsible AI tooling. The attack strategy library and scoring models are actively expanding.

### Core Use Case

Automated pre-production security assessment of AI agents — identifying prompt injection vulnerabilities, jailbreak susceptibility, harmful content generation risks, and data leakage vectors before deploying agents to customers.

### Microsoft Learn Reference

[Azure AI Red Teaming](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/red-teaming)
[Responsible AI with Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/responsible-ai/overview)

### How the Notebooks Implement This Service

**`5-red-team-security-testing.ipynb`** launches a targeted security scan of the banking AI deployment:
```python
from azure.ai.projects.models import (
    RedTeam, AttackStrategy, RiskCategory, AzureOpenAIModelConfiguration
)

red_team_config = RedTeam(
    display_name="banking-ai-security-scan",
    target=AzureOpenAIModelConfiguration(
        deployment_name=AZURE_AI_MODEL_DEPLOYMENT_NAME
    ),
    attack_strategies=[
        AttackStrategy.BASE64,
        AttackStrategy.FLIP,
        AttackStrategy.MORSE_CODE,
        AttackStrategy.CAESAR_CIPHER,
        AttackStrategy.UNICODE_CONFUSABLE,
        AttackStrategy.CRESCENDO,
        AttackStrategy.MULTI_TURN
    ],
    risk_categories=[
        RiskCategory.VIOLENCE,
        RiskCategory.HATE_UNFAIRNESS,
        RiskCategory.SEXUAL,
        RiskCategory.SELF_HARM
    ]
)

scan = project_client.red_teams.create(red_team=red_team_config)
```
The notebook polls for completion at 30-second intervals (10-minute timeout) and retrieves comprehensive findings with severity scores. For each attack strategy, the service generates adversarial prompts disguised using the specified encoding (e.g., a violent request encoded in Base64), submits them to the target model, and evaluates whether harmful content was generated. Results surface which encoding/risk combinations produced the highest vulnerability scores, guiding remediation priorities for the banking AI deployment's content safety configuration.

---

## Service Maturity Summary

| Azure Service | Maturity | Primary SDK Package |
|--------------|----------|-------------------|
| Azure AI Foundry — AI Agents v2 | GA | `azure-ai-projects` |
| Azure OpenAI — Code Interpreter | GA | `azure-ai-projects` |
| Azure AI Search | GA (vector/semantic GA; agentic preview) | `azure-search-documents` |
| Bing Search — Grounding | GA | `azure-ai-projects` |
| AI Foundry — File Search | GA | `azure-ai-projects` |
| AI Foundry — Workflow Agents | Public Preview | `azure-ai-projects` |
| AI Foundry — MCP Server | Public Preview | `azure-ai-projects` |
| AI Foundry IQ — Knowledge Bases | Public Preview | `azure-ai-projects` |
| AI Foundry — Memory Store | Public Preview | `azure-ai-projects` |
| Microsoft Agent Framework | Public Preview | `microsoft-agents-*` |
| Azure Cache for Redis | GA (Redis integration preview) | `redis` + agent framework |
| Magentic One | Public Preview | `microsoft-agents-workflows` |
| Azure Monitor + App Insights + OTel | GA | `azure-monitor-opentelemetry` |
| Azure AI Evaluation Service | GA (tool accuracy preview) | `azure-ai-evaluation` |
| Azure AI Red Teaming | Public Preview | `azure-ai-projects` |
