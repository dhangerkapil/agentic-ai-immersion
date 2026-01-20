# 🔍 Observability

This folder contains examples demonstrating observability and tracing patterns with Azure AI agents using the Microsoft Agent Framework.

## 🧠 What is Observability?

**Observability** enables you to monitor, trace, and debug AI agent applications using OpenTelemetry and Azure Application Insights. It's essential for building robust AI systems with compliance, auditing, and performance monitoring requirements.

## 📓 Available Notebooks

| # | Notebook | Industry Use Case | Key Concepts |
|---|----------|--------------|--------------|
| 1 | [`1-agent-with-foundry-tracing.ipynb`](1-agent-with-foundry-tracing.ipynb) | Trade Execution Monitoring | Manual Azure Monitor setup, custom spans |
| 2 | [`2-azure-ai-agent-observability.ipynb`](2-azure-ai-agent-observability.ipynb) | Customer Service Monitoring | AzureAIAgentClient with auto-telemetry |
| 3 | [`3-workflow-observability.ipynb`](3-workflow-observability.ipynb) | Loan Processing Pipeline | Multi-stage workflow tracing |

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

3. **Application Insights** (optional but recommended):
   - Configure Application Insights in your Microsoft Foundry project
   - Traces will be visible in Azure Portal > Application Insights > Transaction Search

## 🎓 Learning Path

| Level | Notebooks | Focus |
|-------|-----------|-------|
| **Beginner** | 1 (Foundry Tracing) | Manual `configure_azure_monitor()` setup, trace IDs |
| **Intermediate** | 2 (Agent Observability) | `AzureAIAgentClient` with integrated telemetry |
| **Advanced** | 3 (Workflow Observability) | Multi-executor pipeline with OTEL providers |

## 🔧 Observability Patterns

| Pattern | Description | Example Notebook |
|---------|-------------|------------------|
| **Manual Setup** | Configure Azure Monitor explicitly | 1 - Trade Execution |
| **Integrated Telemetry** | Agent client handles observability | 2 - Customer Service |
| **Workflow Tracing** | Track multi-stage pipelines | 3 - Loan Processing |
| **Custom Spans** | Add business-specific trace context | All notebooks |

## 🔍 Key APIs Used

| API | Purpose | Notebook |
|-----|---------|----------|
| `configure_azure_monitor()` | Set up Azure Monitor exporter | 1, 2 |
| `get_tracer().start_as_current_span()` | Create custom trace spans | 1, 2, 3 |
| `format_trace_id()` | Get readable trace ID for debugging | 1, 2, 3 |
| `configure_otel_providers()` | Set up OTEL for workflows | 3 |
| `WorkflowBuilder` | Create observable workflow pipelines | 3 |

## 📊 Telemetry Data Collected

| Component | Spans | Events |
|-----------|-------|--------|
| **Agent** | `agent.run`, `agent.run_stream` | Tool calls, responses |
| **Workflow** | `workflow.build`, `workflow.run` | Executor invocations |
| **Executor** | `executor.process` | Message send/receive |

## 💼 Industry Use Cases

| Use Case | Business Value | Notebook |
|----------|----------------|----------|
| **Trade Execution Monitoring** | Audit trail for trades, compliance | 1 |
| **Customer Service Monitoring** | Track support interactions, SLA metrics | 2 |
| **Loan Processing Pipeline** | End-to-end visibility, bottleneck detection | 3 |

## 📚 Related Resources

- [Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview)
- [Azure Monitor OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-overview)
- [Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)
