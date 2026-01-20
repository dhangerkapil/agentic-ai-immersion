# 🔄 Workflows

This folder contains examples demonstrating workflow orchestration patterns with Azure AI agents using the Microsoft Agent Framework.

## 🧠 What are Workflows?

**Workflows** enable you to orchestrate multiple agents, executors, and human-in-the-loop interactions in complex business processes. They provide graph-based execution, streaming responses, and support for patterns like sequential processing, reflection, and multi-agent coordination.

## 📓 Available Notebooks

| # | Notebook | Industry Use Case | Key Concepts |
|---|----------|--------------|--------------|
| 1 | [`1-azure-ai-agents-streaming.ipynb`](1-azure-ai-agents-streaming.ipynb) | Real-time Trading Updates | Streaming with AzureAIAgentClient |
| 2 | [`2-azure-chat-agents-streaming.ipynb`](2-azure-chat-agents-streaming.ipynb) | Customer Support Chat | Streaming with AzureOpenAIChatClient |
| 3 | [`3-sequential-agents-loan-application.ipynb`](3-sequential-agents-loan-application.ipynb) | Loan Application Processing | Sequential agent pipeline |
| 4 | [`4-sequential-custom-executors-compliance.ipynb`](4-sequential-custom-executors-compliance.ipynb) | Loan Advisory with Compliance | Custom executors after agents |
| 5 | [`5-credit-limit-with-human-input.ipynb`](5-credit-limit-with-human-input.ipynb) | Credit Limit Approval | Human-in-the-loop decisions |
| 6 | [`6-workflow-as-agent-human-in-the-loop-transaction-review.ipynb`](6-workflow-as-agent-human-in-the-loop-transaction-review.ipynb) | Wire Transfer Authorization | Workflow-as-agent with escalation |
| 7 | [`7-magentic-compliance-review-with-human-input.ipynb`](7-magentic-compliance-review-with-human-input.ipynb) | Investment Plan Compliance Review | Magentic multi-agent with human approval |
| 8 | [`8-magentic-investment-research.ipynb`](8-magentic-investment-research.ipynb) | Investment Research Analysis | Magentic multi-agent orchestration |
| 9 | [`9-workflow-as-agent-reflection-pattern.ipynb`](9-workflow-as-agent-reflection-pattern.ipynb) | Customer Communication Quality | Reflection pattern with review loop |

## 🚀 Prerequisites

1. **Azure CLI Authentication**:
   ```bash
   az login
   ```

2. **Environment Variables** (in root `.env` file):
   ```
   AZURE_OPENAI_ENDPOINT=your-openai-endpoint
   AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=gpt-4o
   AI_FOUNDRY_PROJECT_ENDPOINT=your-project-endpoint
   ```

## 🎓 Learning Path

| Level | Notebooks | Focus |
|-------|-----------|-------|
| **Beginner** | 1 (Streaming) → 2 (Chat Streaming) | Basic workflow and streaming patterns |
| **Intermediate** | 3 (Sequential) → 4 (Custom Executors) | Agent pipelines and custom processing |
| **Advanced** | 5, 6 (Human-in-the-loop) → 7, 8 (Magentic) → 9 (Reflection) | Complex orchestration patterns |

## 🔧 Workflow Patterns

| Pattern | Description | Example Notebook |
|---------|-------------|------------------|
| **Streaming** | Real-time token streaming responses | 1, 2 |
| **Sequential** | Linear agent-to-agent handoff | 3, 4 |
| **Human-in-the-loop** | Pause for human approval/input | 5, 6, 7 |
| **Magentic** | Multi-agent collaboration with manager | 7, 8 |
| **Reflection** | Self-review and improvement loop | 9 |
| **Workflow-as-Agent** | Embed workflow within agent interface | 6, 9 |

## 🔍 Key APIs Used

| API | Purpose | Notebook |
|-----|---------|----------|
| `WorkflowBuilder` | Define workflow graph | All |
| `register_executor()` | Add executors to workflow | 3, 4, 6, 9 |
| `with_edge()` | Define execution flow | All |
| `ctx.request_info()` | Request human input | 5, 6, 7 |
| `@response_handler` | Handle human responses | 5, 6, 7 |
| `MagenticBuilder` | Build multi-agent workflows | 7, 8 |
| `AgentResponseUpdate` | Emit streaming responses | 6, 9 |
| `AgentRunUpdateEvent` | Add events to context | 6, 9 |

## 💼 Business Use Cases

| Use Case | Business Value | Notebook |
|----------|----------------|----------|
| **Real-time Data Updates** | Stream live data and analysis | 1 |
| **Customer Support Chat** | Interactive customer support | 2 |
| **Application Processing** | End-to-end application workflow | 3 |
| **Advisory with Compliance** | Custom compliance checks post-analysis | 4 |
| **Approval Workflow** | Risk-based approval with human review | 5 |
| **High-Value Authorization** | High-value transaction escalation | 6 |
| **Plan Compliance Review** | Ensure compliance before execution | 7 |
| **Multi-Agent Research** | Multi-analyst collaboration for research | 8 |
| **Communication Quality** | Review and improve communications | 9 |

## 📚 Related Resources

- [Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Workflow Orchestration Guide](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/workflow-orchestration)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
