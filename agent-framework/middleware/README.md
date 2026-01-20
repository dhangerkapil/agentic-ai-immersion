# 🔧 Middleware

This folder contains examples demonstrating middleware patterns with Azure AI agents using the Microsoft Agent Framework.

## 🧠 What is Middleware?

**Middleware** allows you to intercept and modify behavior at different execution stages—agent runs, function calls, and chat interactions. It's essential for building robust AI applications with logging, security, error handling, and compliance.

## 📓 Available Notebooks

| # | Notebook | Industry Use Case |
|---|----------|--------------|
| 1 | [`1-agent-and-run-level-middleware.ipynb`](1-agent-and-run-level-middleware.ipynb) | Agent-level vs run-level middleware |
| 2 | [`2-function-based-middleware.ipynb`](2-function-based-middleware.ipynb) | Function-based patterns |
| 3 | [`3-class-based-middleware.ipynb`](3-class-based-middleware.ipynb) | Class-based inheritance |
| 4 | [`4-decorator-middleware.ipynb`](4-decorator-middleware.ipynb) | Portfolio Rebalancing |
| 5 | [`5-chat-middleware.ipynb`](5-chat-middleware.ipynb) | Customer Service Filtering |
| 6 | [`6-exception-handling-with-middleware.ipynb`](6-exception-handling-with-middleware.ipynb) | Market Data Recovery |
| 7 | [`7-middleware-termination.ipynb`](7-middleware-termination.ipynb) | Transaction Compliance Screening |
| 8 | [`8-override-result-with-middleware.ipynb`](8-override-result-with-middleware.ipynb) | Market Data Enrichment |
| 9 | [`9-shared-state-middleware.ipynb`](9-shared-state-middleware.ipynb) | Transaction Audit Trail |

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

## 🎓 Learning Path

| Level | Notebooks |
|-------|-----------|
| **Beginner** | 1 (Agent/Run Level) → 2 (Function-based) → 3 (Class-based) |
| **Intermediate** | 4 (Decorators) → 5 (Chat) → 6 (Exception Handling) |
| **Advanced** | 7 (Termination) → 8 (Result Override) → 9 (Shared State) |

## 🔧 Middleware Types

| Type | Purpose | Example |
|------|---------|---------|
| **Agent Middleware** | Intercept agent runs | Logging, security |
| **Function Middleware** | Intercept function calls | Validation, retry |
| **Chat Middleware** | Intercept chat requests | PII filtering, audit |

## 📚 Related Resources

- [Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)