# Agent Framework Migration Guide — `1.0.0rc6`

Quick-reference for migrating from the beta API to `agent-framework-core 1.0.0rc6` / `agent-framework-foundry 1.0.0rc6`.
Based on [ADR 0021 — Provider-Leading Client Design](https://github.com/microsoft/agent-framework/blob/main/docs/decisions/0021-provider-leading-clients.md).

---

## Background: Provider-Leading Client Design & OpenAI Package Extraction

### Problem

The beta `agent-framework-core` bundled OpenAI and Azure OpenAI client implementations along with their dependencies (`openai`, `azure-identity`, `azure-ai-projects`, `packaging`). This made core heavier than necessary for users who don't use OpenAI and conflated core abstractions with a specific provider. Class naming (`OpenAIResponsesClient`, `OpenAIChatClient`) was based on the underlying OpenAI API rather than user intent, hurting discoverability.

### Decision Drivers

| Driver | Rationale |
|---|---|
| **Lightweight core** | Core contains only abstractions, middleware infrastructure, and telemetry — no provider-specific code or dependencies |
| **Discoverability-first** | `from agent_framework.openai import ...` surfaces OpenAI clients; `from agent_framework.azure import ...` surfaces Foundry/Azure classes |
| **Provider-leading naming** | Client names reflect the *provider*, not the underlying API. The Responses API default client is now `OpenAIChatClient` (not `OpenAIResponsesClient`) |
| **Clean separation** | Azure-specific deprecated wrappers belong in `agent-framework-foundry`, not the OpenAI package |

### Package Architecture (rc6)

```
agent-framework-core          # abstractions only (Agent, Message, Content, WorkflowBuilder, …)
    │
    ├── agent-framework-openai # OpenAI provider (openai + packaging deps only)
    │
    └── agent-framework-foundry # Azure AI Foundry provider (FoundryChatClient, FoundryAgent)
                                # also houses deprecated AzureOpenAI* wrappers for clean deletion
```

- `agent_framework.openai` and `agent_framework.azure` are **lazy-loading gateways** — backward-compatible import paths without hard dependencies.

### Key Decisions

1. **Class renames**: `OpenAIResponsesClient` → `OpenAIChatClient` (Responses API), `OpenAIChatClient` → `OpenAIChatCompletionClient` (Chat Completions API). Old names are deprecated aliases.
2. **Unified `model` parameter**: Replaces `model_id` (OpenAI), `deployment_name` (Azure OpenAI), and `model_deployment_name` (Azure AI) across all providers. Environment variables unified (e.g., `OPENAI_MODEL`).
3. **`FoundryChatClient`**: Replaces `AzureAIClient` for Azure AI Foundry Responses API access, built on `RawFoundryChatClient(RawOpenAIChatClient)`.
4. **Deprecated classes consolidated**: All `AzureOpenAI*` classes live in a single `_deprecated_azure_openai.py` in the foundry package for clean future deletion.

### Foundry Agent Design

The old `AzureAIClient` combined CRUD lifecycle management (creating/deleting agents) with runtime communication. The new design **removes CRUD entirely** — users connect to agents that already exist in Foundry.

**Chosen pattern** — `FoundryAgent` (Agent subclass):

```python
# Common case — single object, no boilerplate
from agent_framework.foundry import FoundryAgent

agent = FoundryAgent(
    agent_name="my-foundry-agent",
    credential=credential,
)
```

```python
# Advanced — custom client middleware via client_type
from agent_framework.foundry import FoundryAgent, RawFoundryAgentChatClient

agent = FoundryAgent(
    agent_name="my-agent",
    credential=credential,
    client_type=RawFoundryAgentChatClient,  # or a custom subclass
)
```

```python
# Composition pattern — still supported
from agent_framework import Agent
from agent_framework.foundry import RawFoundryAgentChatClient

agent = Agent(client=RawFoundryAgentChatClient(...))
```

#### Public Classes

| Class | Base | Purpose |
|---|---|---|
| `FoundryAgent` | `Agent` (with telemetry + middleware layers) | Recommended production agent for Foundry-hosted agents |
| `RawFoundryAgent` | `RawAgent` | Agent without middleware/telemetry |
| `RawFoundryAgentChatClient` | `RawOpenAIChatClient` | Responses API client with agent reference injection and tool validation. Extension point for custom client middleware |

#### Deprecations

| Deprecated | Replacement |
|---|---|
| `AzureAIClient` | `FoundryAgent` (uses `FoundryAgentClient` internally) |
| `AzureAIAgentClient` | No direct replacement (V1 Agents Service API) |
| `AzureAIProjectAgentProvider` | `FoundryAgent` |

> **Runtime validation**: Only `FunctionTool` is allowed — enforced in `RawFoundryAgentChatClient._prepare_options`, regardless of how the client is used.

---

## 1. Package & Import Changes

| Old Package / Import | New Package / Import |
|---|---|
| `agent-framework` (bundled OpenAI) | `agent-framework-core` (abstractions only) + `agent-framework-openai` (provider) |
| `agent-framework-azure-ai` | `agent-framework-foundry` |
| `from agent_framework import ChatAgent` | `from agent_framework import Agent` |
| `from agent_framework import ChatMessage` | `from agent_framework import Message` |
| `from agent_framework import Contents` | `from agent_framework import Content` |
| `from agent_framework import ChatClientProtocol` | `from agent_framework import SupportsChatGetResponse` |
| `from agent_framework import Role` (enum) | `Role` is now a `NewType(str)` — use `"user"`, `"assistant"`, `"system"`, `"tool"` string literals |
| `from agent_framework import ai_function` | `from agent_framework import tool` |
| `from agent_framework.azure import AzureAIClient` | `from agent_framework.foundry import FoundryChatClient` |

---

## 2. Agent Creation

```python
# OLD
from agent_framework import ChatAgent
agent = ChatAgent(
    name="MyAgent",
    chat_client=chat_client,
    instructions="...",
)

# NEW
from agent_framework import Agent
agent = Agent(
    client=chat_client,        # param renamed: chat_client → client
    name="MyAgent",
    instructions="...",
)
```

---

## 3. Role — Enum → String Literal

`Role` changed from an enum to a `NewType(str)`. `Role.SYSTEM`, `Role.USER`, `Role.ASSISTANT`, `Role.TOOL` no longer exist.

```python
# OLD
from agent_framework import Role
msg = Message(role=Role.SYSTEM, text="...")
msg = Message(role=Role.USER, text="...")
if msg.role == Role.ASSISTANT: ...

# NEW — use plain string literals, no import needed
msg = Message(role="system", text="...")
msg = Message(role="user", text="...")
if msg.role == "assistant": ...
```

| Old | New |
|---|---|
| `Role.SYSTEM` | `"system"` |
| `Role.USER` | `"user"` |
| `Role.ASSISTANT` | `"assistant"` |
| `Role.TOOL` | `"tool"` |

> Remove `Role` from imports — it's no longer useful as a standalone reference.

---

## 4. Chat Client Initialization

```python
# OLD
from agent_framework.azure import AzureAIClient
client = AzureAIClient(
    credential=credential,
    project_endpoint=endpoint,
    model_deployment_name=model,
)

# NEW — Foundry (Azure AI)
from agent_framework.foundry import FoundryChatClient
client = FoundryChatClient(
    credential=credential,
    project_endpoint=endpoint,
    model=model,                # unified 'model' param
)

# NEW — OpenAI Responses API (default, recommended)
from agent_framework.openai import OpenAIChatClient
client = OpenAIChatClient(model="gpt-4o")

# NEW — OpenAI Chat Completions API
from agent_framework.openai import OpenAIChatCompletionClient
client = OpenAIChatCompletionClient(model="gpt-4o")

# NEW — Azure OpenAI via AsyncAzureOpenAI
from openai import AsyncAzureOpenAI
from agent_framework.openai import OpenAIChatClient
azure_openai = AsyncAzureOpenAI(
    azure_endpoint="https://my-resource.openai.azure.com",
    api_version="2025-03-01-preview",
)
client = OpenAIChatClient(model="my-deployment", async_client=azure_openai)
```

### Client Class Renames

| Old Name | New Name | API |
|---|---|---|
| `OpenAIResponsesClient` | `OpenAIChatClient` | Responses API (default) |
| `OpenAIChatClient` | `OpenAIChatCompletionClient` | Chat Completions API |
| `AzureAIClient` | `FoundryChatClient` | Azure AI Foundry Responses API |

### Unified `model` Parameter

| Old Parameter | Provider | New Parameter |
|---|---|---|
| `model_id` | OpenAI | `model` |
| `deployment_name` | Azure OpenAI | `model` |
| `model_deployment_name` | Azure AI Foundry | `model` |

Environment variables are also unified: `OPENAI_MODEL` replaces `OPENAI_RESPONSES_MODEL_ID` / `OPENAI_CHAT_MODEL_ID`.

---

## 4. Foundry Agents (Pre-configured in Azure AI Foundry)

```python
# OLD
from agent_framework.azure import AzureAIProjectAgentProvider
async with AzureAIProjectAgentProvider(credential=cred) as provider:
    agent = await provider.create_agent(name="...", model=model)

# NEW
from agent_framework.foundry import FoundryAgent
agent = FoundryAgent(
    agent_name="my-foundry-agent",
    credential=credential,
    project_endpoint=os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"],
)
```

### FoundryAgent Key Parameters

| Parameter | Required | Description |
|---|---|---|
| `agent_name` | Yes | Name of the pre-configured agent in Azure AI Foundry |
| `credential` | Yes | Azure credential (e.g., `AzureCliCredential()`) |
| `project_endpoint` | No* | Foundry project endpoint. *Falls back to `AI_FOUNDRY_PROJECT_ENDPOINT` env var |
| `client_type` | No | Custom subclass of `RawFoundryAgentChatClient` for middleware/overrides |
| `instructions` | No | Override agent instructions at runtime |
| `tools` | No | Additional `FunctionTool` instances (only `FunctionTool` allowed) |

### Agent Streaming

```python
# Non-streaming
response = await agent.run("What is the current portfolio risk?")
print(response)

# Streaming — use stream=True (NOT run_stream)
async for chunk in agent.run("What is the current portfolio risk?", stream=True):
    print(chunk, end="")
```

> **⚠️ Note**: There is no `run_stream()` method. Use `agent.run(query, stream=True)`.

### FoundryAgentChatClient Workaround (rc6)

In `agent-framework-foundry 1.0.0rc6`, `RawFoundryAgentChatClient` may fail when tools have schemas that the Foundry agent service doesn't expect. Use a custom `client_type` to strip tool schemas:

```python
from agent_framework.foundry import FoundryAgent, RawFoundryAgentChatClient

class FoundryAgentChatClient(RawFoundryAgentChatClient):
    """Workaround for rc6: strips tool schemas before sending to Foundry."""

    def _prepare_options(self, options):
        options = super()._prepare_options(options)
        if hasattr(options, "tools") and options.tools:
            for t in options.tools:
                if hasattr(t, "function") and hasattr(t.function, "parameters"):
                    t.function.parameters = None
        return options

agent = FoundryAgent(
    agent_name="my-agent",
    credential=credential,
    project_endpoint=os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"],
    client_type=FoundryAgentChatClient,
)
```

> This workaround will likely be unnecessary in future releases.

---

## 5. Messages & Content

```python
# OLD
from agent_framework import ChatMessage, Contents
msg = ChatMessage(role=Role.USER, content="Hello")
items = msg.contents  # list[Contents]

# NEW
from agent_framework import Message, Content, Role
msg = Message(role=Role.USER, text="Hello")
# or with explicit content items:
msg = Message(role=Role.ASSISTANT, contents=[Content.from_text("Hello")])
```

### Content Factory Methods

```python
Content.from_text("...")
Content.from_function_call(call_id, name, arguments="{...}")
Content.from_function_result(call_id, result="...")
Content.from_function_approval_request(id, function_call)
content.to_function_approval_response(approved=True)
```

### Content Type Checks

```python
# OLD
from agent_framework import FunctionCallContent, FunctionResultContent
if isinstance(content, FunctionCallContent): ...

# NEW
if content.type == "function_call": ...
if content.type == "function_result": ...
if content.type == "function_approval_request": ...
```

---

## 6. Tool Decorator

```python
# OLD
from agent_framework import ai_function

@ai_function
def get_weather(city: str) -> str: ...

@ai_function(approval_mode="always")
def delete_record(id: str) -> str: ...

# NEW
from agent_framework import tool

@tool
def get_weather(city: str) -> str: ...

@tool(approval_mode="always")
def delete_record(id: str) -> str: ...
```

---

## 7. Workflow Builder

```python
# OLD
builder = WorkflowBuilder()
builder.register_agent(agent_a)
builder.register_agent(agent_b)
builder.register_executor(my_executor)
builder.set_start_executor(agent_a)
builder.add_edge(agent_a, agent_b)
workflow = builder.build()

# NEW
workflow = (
    WorkflowBuilder(start_executor=agent_a)   # start_executor is required
    .add_edge(agent_a, agent_b)
    .build()
)
```

### Sequential Chain (replaces `SequentialBuilder`)

```python
# OLD
from agent_framework import SequentialBuilder
workflow = SequentialBuilder().add_agents([a, b, c]).build()

# NEW
workflow = (
    WorkflowBuilder(start_executor=a)
    .add_chain([a, b, c])
    .build()
)
```

### Available Edge Methods

```python
builder.add_edge(source, target)
builder.add_chain([a, b, c])
builder.add_fan_out_edges(source, [t1, t2])
builder.add_fan_in_edges([s1, s2], target)
builder.add_multi_selection_edge_group(source, [t1, t2], selector_func)
builder.add_switch_case_edge_group(source, {key: target}, selector_func)
```

---

## 8. Running Workflows

```python
# OLD — streaming
async for event in workflow.run_stream("Hello"):
    ...

# NEW — streaming
async for event in workflow.run("Hello", stream=True):
    ...

# OLD — send responses (human-in-the-loop)
async for event in workflow.send_responses_streaming(responses):
    ...
# NEW
async for event in workflow.run(responses=responses, stream=True):
    ...

# OLD — non-streaming response send
result = await workflow.send_responses(responses)
# NEW
result = await workflow.run(responses=responses)
```

---

## 9. Workflow Events (Unified `WorkflowEvent`)

```python
# OLD — separate event classes
from agent_framework import (
    AgentRunUpdateEvent,
    WorkflowOutputEvent,
    WorkflowStatusEvent,
    RequestInfoEvent,
)
async for event in workflow.run_stream(msg):
    if isinstance(event, AgentRunUpdateEvent): ...
    if isinstance(event, WorkflowOutputEvent): ...
    if isinstance(event, WorkflowStatusEvent): ...
    if isinstance(event, RequestInfoEvent): ...

# NEW — single WorkflowEvent with .type discriminator
from agent_framework import WorkflowEvent, AgentResponseUpdate

async for event in workflow.run(msg, stream=True):
    if event.type == "data" and isinstance(event.data, AgentResponseUpdate):
        print(event.data, end="")           # streaming token
    elif event.type == "output":
        result = event.data                 # final output
    elif event.type == "status":
        print(event.data)                   # status update
    elif event.type == "request_info":
        # human-in-the-loop prompt
        ...
```

### Emitting Events (inside custom Executors)

```python
# OLD
await context.emit(AgentRunUpdateEvent(data=update))

# NEW
await context.emit(WorkflowEvent.data(update))
```

---

## 10. Custom Executors

```python
from agent_framework import Executor, WorkflowContext, Message, handler

class MyExecutor(Executor):
    def __init__(self):
        super().__init__(id="my-executor")

    @handler
    async def handle(self, message: str, context: WorkflowContext):
        # NOTE: message parameter comes FIRST, context SECOND
        # process message, call agents, emit events
        response = await self.some_agent.run(message)
        await context.emit(WorkflowEvent.data(
            AgentResponseUpdate(text=response.text)
        ))
        return response
```

---

## 11. Orchestration Builders — `agent_framework.orchestrations`

`HandoffBuilder` and `GroupChatBuilder` are **NOT removed** — they moved to `agent_framework.orchestrations`.

### `HandoffBuilder`

```python
from agent_framework.orchestrations import HandoffBuilder, HandoffAgentUserRequest

workflow = (
    HandoffBuilder()
    .with_start_agent(triage_agent)
    .add_handoff(triage_agent, [billing_agent, tech_agent])
    .add_handoff(billing_agent, [triage_agent])
    .add_handoff(tech_agent, [triage_agent])
    .with_autonomous_mode(
        agents=[billing_agent, tech_agent],
        prompts=["Handle the customer request autonomously."],
        turn_limits=[5],
    )
    .build()
)

# Streaming
async for event in workflow.run("I need help with my bill", stream=True):
    if event.type == "data" and isinstance(event.data, AgentResponseUpdate):
        print(event.data, end="")
    elif event.type == "request_info":
        # Human-in-the-loop: inspect event.data for function_approval_request
        response = HandoffAgentUserRequest.create_response("Approved")
        async for e in workflow.run(responses=[response], stream=True):
            ...
```

### `GroupChatBuilder`

```python
from agent_framework.orchestrations import GroupChatBuilder, GroupChatState

# Round-robin selection
def round_robin(state: GroupChatState) -> str:
    participants = state.participants
    idx = len(state.history) % len(participants)
    return participants[idx]

# Termination condition
def terminate_after_rounds(state: GroupChatState) -> bool:
    return len(state.history) >= 6  # 2 rounds × 3 agents

workflow = (
    GroupChatBuilder(
        participants=[analyst, researcher, writer],
        selection_func=round_robin,
        termination_condition=terminate_after_rounds,
    )
    .build()
)

# Streaming
async for event in workflow.run("Research topic", stream=True):
    if event.type == "data" and isinstance(event.data, AgentResponseUpdate):
        print(f"[{event.data.author_name}]: {event.data}", end="")
    elif event.type == "output" and isinstance(event.data, list):
        # Final conversation history
        for msg in event.data:
            print(f"{msg.author_name}: {msg.text}")
```

#### GroupChatBuilder with Orchestrator Agent

```python
# Use an LLM agent to select the next speaker
workflow = (
    GroupChatBuilder(
        participants=[analyst, researcher, writer],
        orchestrator_agent=moderator_agent,  # Agent decides next speaker
        termination_condition=terminate_condition,
    )
    .build()
)
```

### `MagenticBuilder` → Custom Orchestrator Executor

No direct replacement. Build a custom `Executor` that:
- Plans via an orchestrator agent
- Optionally emits `request_info` events for human approval
- Dispatches to sub-agents and aggregates results

---

## 12. Deprecated Classes (Still Available, Will Be Removed)

| Deprecated | Replacement | Notes |
|---|---|---|
| `OpenAIResponsesClient` | `OpenAIChatClient` | Renamed — Responses API is now the default |
| `OpenAIChatClient` *(old)* | `OpenAIChatCompletionClient` | Renamed — Chat Completions API |
| `OpenAIAssistantsClient` | *(none)* | Assistants API deprecated |
| `AzureOpenAI*Client` classes | `OpenAIChatClient` with `AsyncAzureOpenAI` | Consolidated in `_deprecated_azure_openai.py` |
| `AzureAIClient` | `FoundryChatClient` | Azure AI Foundry Responses API |
| `AzureAIAgentClient` | *(none)* | V1 Agents Service API — no replacement |
| `AzureAIProjectAgentProvider` | `FoundryAgent` | CRUD removed — connect to existing agents |

All deprecated `AzureOpenAI*` wrappers live in a single file in the `agent-framework-foundry` package for clean future deletion. Core's `agent_framework.openai` and `agent_framework.azure` namespaces remain as **lazy-loading gateways** preserving backward-compatible import paths.

---

## Quick Checklist

- [ ] Replace `ChatAgent` → `Agent`, `chat_client=` → `client=`
- [ ] Replace `ChatMessage` → `Message`, `Contents` → `Content`
- [ ] Replace `ChatClientProtocol` → `SupportsChatGetResponse`
- [ ] Replace `@ai_function` → `@tool`
- [ ] Replace `FunctionCallContent` / `FunctionResultContent` → `Content` type checks
- [ ] Update `WorkflowBuilder()` → `WorkflowBuilder(start_executor=...)`
- [ ] Remove `.register_agent()`, `.register_executor()`, `.set_start_executor()`
- [ ] Replace `run_stream(msg)` → `run(msg, stream=True)`
- [ ] Replace `send_responses_streaming(r)` → `run(responses=r, stream=True)`
- [ ] Replace individual event classes → `WorkflowEvent` with `.type` checks
- [ ] Use `GroupChatBuilder` / `HandoffBuilder` from `agent_framework.orchestrations`
- [ ] Handler signature: `(self, message: T, context: WorkflowContext)` — message FIRST
- [ ] `FoundryAgent` import from `agent_framework.foundry` (NOT `agent_framework.azure`)
- [ ] Include `project_endpoint` parameter for `FoundryAgent`
- [ ] Add `client_type=FoundryAgentChatClient` workaround for rc6 function tools
- [ ] Use `agent.run(query, stream=True)` (NOT `agent.run_stream()`)
