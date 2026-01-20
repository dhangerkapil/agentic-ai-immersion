# 📝 Context Providers

This folder demonstrates how to use **Context Providers** in the Microsoft Agent Framework to give agents memory and dynamic context capabilities.

## 🧠 What are Context Providers?

Context providers observe the agent lifecycle and allow you to:

- **Inject Context** (`invoking()`) - Add instructions/context before each agent call
- **Extract Information** (`invoked()`) - Capture data from conversations after each call
- **Persist State** (`serialize()`) - Save context data for thread continuation

## 📓 Available Notebooks

| # | Notebook | Description | Use Case |
|---|----------|-------------|----------|
| 1 | `1-simple-context-provider.ipynb` | Custom context provider with structured data extraction | **KYC Profile Collection** - Collects customer information progressively |
| 2 | `2-azure-ai-search-context-agentic.ipynb` | Azure AI Search with agentic mode for RAG | **Loan Underwriting** - Multi-hop reasoning over policy documents |

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

3. **For Notebook 2 (Azure AI Search)**:
   ```
   AZURE_AI_SEARCH_ENDPOINT=your-search-endpoint
   ```

## 📋 Notebook Details

### 1. Simple Context Provider (KYC Use Case)

Learn how to create a custom `ContextProvider` that:
- Extracts customer information using Pydantic models
- Provides dynamic instructions based on collected data
- Tracks profile completion status across conversation turns

**Key Concepts**: `invoking()`, `invoked()`, structured output extraction

### 2. Azure AI Search Context Provider (Underwriting Use Case)

Learn how to use the built-in `AzureAISearchContextProvider` with:
- Vector search using HNSW algorithm
- Azure OpenAI embeddings
- Agentic mode for multi-hop reasoning

**Key Concepts**: RAG, vector search, semantic configuration

## 🎓 Learning Path

1. **Start with Notebook 1** - Understand the context provider pattern
2. **Move to Notebook 2** - See how to integrate with Azure AI Search for RAG

## 📚 Related Resources

- [Agent Memory Documentation](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-memory?pivots=programming-language-python)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
