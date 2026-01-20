# 🧵 Threads

This folder contains examples demonstrating thread management patterns with Azure AI agents using the Microsoft Agent Framework.

## 🧠 What are Threads?

**Threads** enable multi-turn conversations with AI agents by persisting conversation history across interactions. They support session persistence, serialization, and various storage backends for robust applications.

## 📓 Available Notebooks

| # | Notebook | Industry Use Case |
|---|----------|--------------|
| 1 | [`1-custom-chat-message-store-thread.ipynb`](1-custom-chat-message-store-thread.ipynb) | Compliance Audit Trail |
| 2 | [`2-redis-chat-message-store-thread.ipynb`](2-redis-chat-message-store-thread.ipynb) | Distributed Customer Sessions |
| 3 | [`3-suspend-resume-thread.ipynb`](3-suspend-resume-thread.ipynb) | Insurance Claim Processing |

## 🚀 Prerequisites

1. **Azure CLI Authentication**:
   ```bash
   az login
   ```

2. **Environment Variables** (in root `.env` file):
   ```
   AI_FOUNDRY_PROJECT_ENDPOINT=your-project-endpoint
   AZURE_OPENAI_ENDPOINT=your-openai-endpoint
   AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o
   ```

3. **For Redis notebook (2)**: Redis server running on localhost:6379
   ```bash
   docker run -d -p 6379:6379 redis:latest
   ```

## 🎓 Learning Path

| Level | Notebooks |
|-------|-----------|
| **Beginner** | 1 (Custom Store) - Custom `ChatMessageStoreProtocol` |
| **Intermediate** | 3 (Suspend/Resume) - Service-managed vs in-memory |
| **Advanced** | 2 (Redis Store) - Distributed sessions, persistence |

## 🔧 Thread Types

| Type | Client | Storage | Use Case |
|------|--------|---------|----------|
| **Service-Managed** | `AzureAIAgentClient` | Azure cloud | Enterprise apps |
| **In-Memory** | `AzureOpenAIChatClient` | Local memory | Custom backends |
| **Redis-Backed** | `AzureOpenAIChatClient` | Redis | Distributed apps |
| **Custom Store** | `AzureOpenAIChatClient` | Your database | Compliance |

## 🔍 Key APIs Used

| API | Purpose |
|-----|---------|
| `AzureAIAgentClient.as_agent()` | Service-managed threads (Azure stores messages) |
| `AzureOpenAIChatClient.as_agent()` | In-memory threads (supports custom stores) |
| `thread.serialize()` | Save thread state |
| `agent.deserialize_thread()` | Restore thread state |
| `ChatMessageStoreProtocol` | Interface for custom storage |
| `RedisChatMessageStore` | Built-in Redis storage |
| `chat_message_store_factory` | Factory pattern for stores |

## 💼 Industry Use Cases

| Use Case | Business Value | Notebook |
|----------|----------------|----------|
| **Compliance Audit Trail** | Full message history for regulatory audits | 1 |
| **Distributed Sessions** | Scale support across app instances | 2 |
| **Claim Processing** | Continue conversations across devices | 3 |

## 📚 Related Resources

- [Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Multi-Turn Conversations](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/multi-turn-conversation?pivots=programming-language-python)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
