# 🤖 Agents

This folder contains examples demonstrating how to create and use agents with Azure AI using the Microsoft Agent Framework.

## 🧠 What is the Agent Framework?

The **Microsoft Agent Framework** is an open-source SDK for building AI agents and multi-agent workflows. It combines ideas from Semantic Kernel and AutoGen into a unified foundation.

## 📓 Available Notebooks

All notebooks are in the `azure-ai-agents/` folder:

| # | Notebook | Description |
|---|----------|-------------|
| 1 | [`1-azure-ai-basic.ipynb`](azure-ai-agents/1-azure-ai-basic.ipynb) | Basic agent usage with automatic lifecycle management |
| 2 | [`2-azure-ai-with-explicit-settings.ipynb`](azure-ai-agents/2-azure-ai-with-explicit-settings.ipynb) | Creating agents with explicit configuration |
| 3 | [`3-azure-ai-with-existing-ai-agent.ipynb`](azure-ai-agents/3-azure-ai-with-existing-ai-agent.ipynb) | Working with pre-existing agents using agent IDs |
| 4 | [`4-azure-ai-with-function-tools.ipynb`](azure-ai-agents/4-azure-ai-with-function-tools.ipynb) | Function tool integration patterns |
| 5 | [`5-azure-ai-with-code-interpreter.ipynb`](azure-ai-agents/5-azure-ai-with-code-interpreter.ipynb) | Python code execution capabilities |
| 6 | [`6-azure-ai-with-file-search.ipynb`](azure-ai-agents/6-azure-ai-with-file-search.ipynb) | Document-based question answering |
| 7 | [`7-azure-ai-with-bing-grounding.ipynb`](azure-ai-agents/7-azure-ai-with-bing-grounding.ipynb) | Web search integration using Bing |
| 8 | [`8-azure-ai-with-hosted-mcp.ipynb`](azure-ai-agents/8-azure-ai-with-hosted-mcp.ipynb) | Model Context Protocol (MCP) server integration |
| 9 | [`9-azure-ai-with-existing-multi-turn-thread.ipynb`](azure-ai-agents/9-azure-ai-with-existing-multi-turn-thread.ipynb) | Managing multi-turn conversation threads |

## 🚀 Prerequisites

1. **Azure CLI Authentication**:
   ```bash
   az login
   ```

2. **Environment Variables** (in root `.env` file):
   ```
   AI_FOUNDRY_PROJECT_ENDPOINT=your-project-endpoint
   AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o
   ```

3. **For Bing Grounding** (optional):
   ```
   BING_CONNECTION_ID=/subscriptions/.../connections/bing-connection
   ```

## 🎓 Learning Path

| Level | Notebooks |
|-------|-----------|
| **Beginner** | 1 (Basic) → 2 (Explicit Settings) |
| **Intermediate** | 3 (Existing Agent) → 4 (Function Tools) |
| **Advanced** | 5 (Code Interpreter) → 6 (File Search) → 7 (Bing Grounding) → 8 (MCP) → 9 (Multi-turn) |

## 📚 Related Resources

- [Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)

