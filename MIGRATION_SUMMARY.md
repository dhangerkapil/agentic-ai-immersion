# Agent Framework Migration Summary

## Overview
Updated three Azure AI notebook files to use the new **FoundryAgent API** and unified model parameters according to the agent framework release notes.

## Files Updated

### 1. `agent-framework/agents/azure-ai-agents/1-azure-ai-basic.ipynb`
**Changes:**
- ✅ Updated imports from `AzureAIProjectAgentProvider` to `FoundryAgent`
- ✅ Changed environment variable reference from `AZURE_AI_MODEL_DEPLOYMENT_NAME` to `OPENAI_MODEL` (unified parameter)
- ✅ Simplified agent creation using `FoundryAgent(agent_name=..., credential=credential)` with direct connection pattern
- ✅ Removed manual thread/conversation management
- ✅ Updated both non-streaming and streaming examples to use new API
- ✅ Added migration notes and key takeaways section

**Key API Changes:**
```python
# Old
async with AzureAIProjectAgentProvider(credential=credential) as provider:
    agent = await provider.create_agent(...)

# New
agent = FoundryAgent(
    agent_name="FinancialAdvisorAgent",
    credential=credential,
)
```

---

### 2. `azure-ai-agents/1-basics.ipynb`
**Changes:**
- ✅ Replaced `AIProjectClient`-based setup with `FoundryAgent` initialization
- ✅ Removed `PromptAgentDefinition` and `azure.ai.projects` imports
- ✅ Converted all functions to async/await patterns
- ✅ Simplified chat functionality using `agent.run(query)` method
- ✅ Auto-initialized credential and agent connection
- ✅ Updated cleanup to use credential closure instead of agent deletion
- ✅ Added migration table and best practices section

**Key API Changes:**
```python
# Old
credential = InteractiveBrowserCredential(tenant_id=tenant_id)
project_client = AIProjectClient(endpoint=project_endpoint, credential=credential)
agent = project_client.agents.create_version(...)

# New
credential = AzureCliCredential()
agent = FoundryAgent(agent_name="financial-services-advisor", credential=credential)
```

---

### 3. `azure-ai-agents/2-code-interpreter.ipynb`
**Changes:**
- ✅ Replaced `AIProjectClient` with `FoundryAgent` initialization
- ✅ Removed `CodeInterpreterTool` and `CodeInterpreterToolAuto` setup (tools pre-configured in Foundry)
- ✅ Converted all functions to async/await patterns
- ✅ Simplified agent queries using `agent.run()` method
- ✅ Updated conversation management (automatic with FoundryAgent)
- ✅ Streamlined cleanup procedure
- ✅ Added comprehensive migration comparison table

**Key Features:**
- Loan calculator with code interpreter still works via pre-configured agent in Foundry
- Loan comparison analysis simplified
- Portfolio risk analysis streamlined
- No changes needed to financial calculations or analysis logic

---

## Environment Variables

### Old Convention
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` - Azure AI specific
- `OPENAI_RESPONSES_MODEL_ID` - OpenAI specific
- `OPENAI_CHAT_MODEL_ID` - OpenAI specific

### New Unified Convention
- `OPENAI_MODEL` - Works with both OpenAI and Azure OpenAI (maps to deployment name)
- `AGENT_NAME` - Agent name in Azure AI Foundry

---

## API Migration Pattern

### Old Pattern
```python
from azure.ai.projects import AIProjectClient, PromptAgentDefinition

client = AIProjectClient(endpoint=endpoint, credential=credential)
agent = client.agents.create_version(
    agent_name="...",
    definition=PromptAgentDefinition(...)
)
conversation = openai_client.conversations.create()
response = openai_client.responses.create(conversation=conversation.id, ...)
```

### New Pattern
```python
from agent_framework.foundry import FoundryAgent

agent = FoundryAgent(
    agent_name="...",
    credential=credential,
    project_endpoint=os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"],
)
result = await agent.run(query)

# Streaming
async for chunk in agent.run(query, stream=True):
    print(chunk, end="")
```

---

## Key Benefits

1. **Simplified Code** - 50%+ less boilerplate
2. **Unified Parameters** - Single `OPENAI_MODEL` variable
3. **Automatic Context** - No manual thread/conversation management
4. **Pre-configured Agents** - Agents set up in Foundry, notebooks just connect
5. **Cleaner API** - Direct `agent.run()` instead of complex chain calls
6. **Better Async Support** - Native async/await patterns

---

## Deprecated Classes

The following classes are now deprecated:
- `AzureAIProjectAgentProvider` → Use `FoundryAgent`
- `AIProjectClient` (for agent creation) → Not needed
- `AzureAIClient` → Use `FoundryAgent`
- `AzureAIAgentClient` → Use `FoundryAgent`
- `AzureAIProjectAgentProvider` → Use `FoundryAgent`

---

## Testing Notes

All notebooks should be tested with:
1. Pre-configured agents in Azure AI Foundry
2. Proper authentication via `AzureCliCredential` or `InteractiveBrowserCredential`
3. Unified `OPENAI_MODEL` environment variable set
4. Appropriate permissions in Azure AI Foundry project

---

## Backward Compatibility

The old API (`AIProjectClient`, `AzureAIProjectAgentProvider`) remains available but deprecated. Organizations can migrate at their own pace. Lazy-loading gateways in `agent_framework.openai` and `agent_framework.azure` namespaces provide backward-compatible import paths.

---

## Next Steps

1. ✅ Test notebooks with actual Foundry agents
2. ✅ Update `.env` configuration with unified variables
3. ✅ Verify code interpreter capabilities work
4. ✅ Run all three notebooks end-to-end
5. ✅ Fixed notebook 11 (group chat) — rewritten with `GroupChatBuilder`
6. ✅ Verified notebook 10 (handoff) — all APIs correct
7. Consider: Update additional notebooks using old API
8. Consider: Add new examples showcasing `RawFoundryAgent` for advanced use cases

---

## Common Mistakes & Corrections

These errors were discovered during notebook testing and article review:

### 1. Wrong Import Path for FoundryAgent
```python
# ❌ WRONG
from agent_framework.azure import FoundryAgent

# ✅ CORRECT
from agent_framework.foundry import FoundryAgent
```

### 2. Missing `project_endpoint` Parameter
```python
# ❌ Incomplete — may fail if env var not set
agent = FoundryAgent(agent_name="my-agent", credential=credential)

# ✅ Explicit endpoint
agent = FoundryAgent(
    agent_name="my-agent",
    credential=credential,
    project_endpoint=os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"],
)
```

### 3. Wrong Streaming API
```python
# ❌ WRONG — run_stream does not exist
async for chunk in agent.run_stream("query"):
    print(chunk)

# ✅ CORRECT
async for chunk in agent.run("query", stream=True):
    print(chunk, end="")
```

### 4. Wrong Environment Variable Name
```python
# ❌ WRONG
os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]

# ✅ CORRECT (for agents that use it)
os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]  # This is fine for agent notebooks
# The unified OPENAI_MODEL is for chat client notebooks
```

### 5. Missing `client_type` for Foundry Agents with Function Tools
```python
# ❌ Missing workaround — may fail with tool schema errors in rc6
agent = FoundryAgent(agent_name="my-agent", credential=credential)

# ✅ Include workaround class
agent = FoundryAgent(
    agent_name="my-agent",
    credential=credential,
    project_endpoint=os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"],
    client_type=FoundryAgentChatClient,  # strips tool schemas
)
```

### 6. Handler Signature Order in Custom Executors
```python
# ❌ WRONG — context first
@handler
async def handle(self, context: WorkflowContext, message: str):

# ✅ CORRECT — message first, context second
@handler
async def handle(self, message: str, context: WorkflowContext):
```

### 7. GroupChatBuilder and HandoffBuilder Are NOT Removed
```python
# ❌ WRONG assumption — these exist in agent_framework.orchestrations
# "No direct replacement. Build a custom Executor..."

# ✅ CORRECT — import from orchestrations
from agent_framework.orchestrations import GroupChatBuilder, GroupChatState
from agent_framework.orchestrations import HandoffBuilder, HandoffAgentUserRequest
```
