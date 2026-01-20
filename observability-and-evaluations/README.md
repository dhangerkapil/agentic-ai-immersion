# 📊 Observability and Evaluations with Microsoft Foundry

Practical notebooks for implementing **telemetry**, **tracing**, and **AI agent evaluations** using Microsoft Foundry — all with **real-world business** use cases.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Repository Guide](#repository-guide)
5. [Suggested Learning Path](#suggested-learning-path)
6. [Key Evaluators Reference](#key-evaluators-reference)
7. [Troubleshooting](#troubleshooting)
8. [Additional Resources](#additional-resources)

## Overview

This directory demonstrates how to build **robust AI agents** with proper observability and evaluation capabilities. For enterprise applications, this is critical for:

- **Compliance & Governance** — Full audit trails of AI interactions
- **Quality Assurance** — Safety and quality evaluation of agent responses
- **Operational Excellence** — Performance monitoring and debugging
- **Continuous Improvement** — Data-driven agent optimization

All notebooks feature **business use cases** including advisory services, approval workflows, operations, and compliance monitoring.

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.10 or later |
| **Azure Subscription** | Access to Microsoft Foundry |
| **Azure CLI** | 2.60+ with active `az login` session |
| **Azure OpenAI** | Deployed model (gpt-4o recommended) |
| **Optional** | Application Insights for telemetry |

## Environment Setup

1. **Create `.env` file** in the parent directory with:

   ```bash
   # Microsoft Foundry Project
   AI_FOUNDRY_PROJECT_ENDPOINT=https://<account>.services.ai.azure.com/api/projects/<project>
   TENANT_ID=your-tenant-id
   AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o

   # Azure OpenAI (for local evaluations)
   AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_DEPLOYMENT=your_deployment_name
   ```

2. **Install packages**:

   ```bash
   pip install azure-ai-projects azure-ai-evaluation azure-identity python-dotenv opentelemetry-sdk azure-monitor-opentelemetry
   ```

3. **Authenticate**:

   ```bash
   az login --use-device-code
   ```

---

## Repository Guide

### 📊 Notebook Overview

| Notebook | Use Case | Key Concept |
|----------|----------|-------------|
| [1-telemetry.ipynb](#1-telemetryipynb) | Advisory Agent | Azure Monitor tracing, custom spans |
| [2-agent-evaluation.ipynb](#2-agent-evaluationipynb) | Advisory Agent Evaluation | Built-in evaluators, safety checks |
| [3-agent-evaluation-with-function-tools.ipynb](#3-agent-evaluation-with-function-toolsipynb) | Business Assistant | Tool-enabled agent evaluation |
| [4-tool-call-accuracy-evaluation.ipynb](#4-tool-call-accuracy-evaluationipynb) | Operations Tooling | Tool selection accuracy |
| [5-red-team-security-testing.ipynb](#5-red-team-security-testingipynb) | AI Security | Red team adversarial testing |

---

### 1-telemetry.ipynb

Learn how to implement **telemetry and tracing** for AI agents.

| Feature | Description |
|---------|-------------|
| **Use Case** | Advisory Agent with Monitoring |
| **Azure Monitor Setup** | Configure OpenTelemetry with Application Insights |
| **Content Recording** | Capture prompts and responses for compliance |
| **Custom Trace Spans** | Add business context (client ID, query category) |
| **Compliance Tracking** | Full audit trail of agent interactions |

**Key APIs:**

```python
configure_azure_monitor(connection_string=...)
tracer = trace.get_tracer("agent-name")
with tracer.start_as_current_span("operation") as span:
    span.set_attribute("client_id", "C-12345")
```

**Why it matters:** Compliance requirements often mandate full traceability of AI-assisted interactions.

---

### 2-agent-evaluation.ipynb

Learn how to **evaluate AI agents** using Microsoft Foundry's built-in evaluators.

| Feature | Description |
|---------|-------------|
| **Use Case** | Advisory Agent Evaluation |
| **Built-in Evaluators** | Violence detection, fluency, task adherence |
| **Test Queries** | Business-relevant advisory questions |
| **Results Analysis** | Detailed metrics and report URLs |
| **Compliance Focus** | Safety and regulatory compliance checks |

**Key APIs:**

```python
eval_object = openai_client.evals.create(
    name="Advisory Agent Evaluation",
    data_source_config=data_source_config,
    testing_criteria=testing_criteria,
)
eval_run = openai_client.evals.runs.create(eval_id=eval_object.id, ...)
```

**Why it matters:** Ensures agents don't provide harmful, inappropriate, or non-compliant advice.

---

### 3-agent-evaluation-with-function-tools.ipynb

Learn how to **evaluate AI agents with function tools** for complex business operations.

| Feature | Description |
|---------|-------------|
| **Use Case** | Business Assistant with Operations Tools |
| **Function Tools** | Data lookup, record retrieval |
| **Tool Processing** | Handle function calls and return results |
| **Response Evaluation** | Evaluate tool-augmented responses |
| **Data Source Type** | `azure_ai_responses` for specific response evaluation |

**Key APIs:**

```python
get_data_tool = FunctionTool(
    name="get_record_data",
    parameters={...},
    strict=True,
)
# Process function calls
input_list.append(FunctionCallOutput(
    type="function_call_output",
    call_id=item.call_id,
    output=json.dumps(result),
))
```

**Why it matters:** Validates that agents correctly use business APIs and present accurate information.

---

### 4-tool-call-accuracy-evaluation.ipynb

Learn how to evaluate **tool call accuracy** — whether agents select the correct tools.

| Feature | Description |
|---------|-------------|
| **Use Case** | Operations Tool Selection |
| **Evaluator** | `builtin.tool_call_accuracy` |
| **Test Scenarios** | Data inquiry, process initiation, report generation, request submission |
| **Multi-tool** | Tests scenarios requiring multiple tool calls |
| **Inline Data** | Uses JSONL data source with inline test content |

**Key APIs:**

```python
testing_criteria = [{
    "type": "azure_ai_evaluator",
    "evaluator_name": "builtin.tool_call_accuracy",
    "data_mapping": {
        "query": "{{item.query}}",
        "tool_definitions": "{{item.tool_definitions}}",
        "tool_calls": "{{item.tool_calls}}",
    },
}]
```

**Why it matters:** Prevents agents from accidentally initiating wrong operations.

---

### 5-red-team-security-testing.ipynb

Learn how to perform **Red Team security scans** to identify AI vulnerabilities.

| Feature | Description |
|---------|-------------|
| **Use Case** | AI Security Assessment |
| **Attack Strategies** | BASE64, FLIP, CRESCENDO, MULTI_TURN encoding attacks |
| **Risk Categories** | Violence, hate/unfairness, sexual, self-harm detection |
| **Scan Management** | Create, monitor, and list security scans |
| **Compliance** | Security testing requirements |

**Key APIs:**

```python
from azure.ai.projects.models import RedTeam, AttackStrategy, RiskCategory

red_team = RedTeam(
    attack_strategies=[AttackStrategy.BASE64],
    risk_categories=[RiskCategory.VIOLENCE],
    target=AzureOpenAIModelConfiguration(model_deployment_name="gpt-4o"),
)
red_team_response = project_client.red_teams.create(red_team=red_team, headers={...})
```

**Why it matters:** Proactively identifies security vulnerabilities before deployment, preventing data breaches and compliance violations.

---

## Suggested Learning Path

| Step | Focus | Notebook | Time |
|------|-------|----------|------|
| 1 | **Telemetry Setup** | `1-telemetry.ipynb` | 20 min |
| 2 | **Basic Evaluation** | `2-agent-evaluation.ipynb` | 25 min |
| 3 | **Tool-Enabled Agents** | `3-agent-evaluation-with-function-tools.ipynb` | 30 min |
| 4 | **Tool Accuracy** | `4-tool-call-accuracy-evaluation.ipynb` | 25 min |
| 5 | **Security Testing** | `5-red-team-security-testing.ipynb` | 30 min |

**Progression:**
```
Telemetry → Basic Evaluation → Tool Evaluation → Tool Accuracy → Red Team
    ↓              ↓                  ↓                ↓              ↓
 Monitoring    Safety checks     Function tools    Selection    Security
```

---

## Key Evaluators Reference

### Built-in Evaluators

| Evaluator | Purpose | Business Application |
|-----------|---------|----------------------|
| `builtin.violence` | Detect violent content | Ensure safe customer interactions |
| `builtin.fluency` | Measure response quality | Professional communication |
| `builtin.task_adherence` | Check if task was completed | Accurate advisory guidance |
| `builtin.tool_call_accuracy` | Validate correct tool usage | Proper operation selection |

### Data Source Types

| Type | Use Case |
|------|----------|
| `azure_ai_target_completions` | Evaluate agent with test queries |
| `azure_ai_responses` | Evaluate specific response by ID |
| `jsonl` (inline) | Provide test data directly in code |

### Evaluation Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Create Eval    │────▶│   Run Eval       │────▶│  Analyze        │
│  (criteria)     │     │   (test data)    │     │  Results        │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                       │
        ▼                        ▼                       ▼
   Define what           Execute against          View metrics,
   to measure            agent/data               report URLs
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Authentication failures** | Re-run `az login --use-device-code` |
| **Trace IDs showing as zeros** | Use `telemetry.get_application_insights_connection_string()` |
| **Missing environment variables** | Verify `.env` file in parent directory |
| **Evaluation stuck in "queued"** | Check model deployment quota and availability |
| **Package import errors** | Run `pip install azure-ai-projects>=2.0.0b1` |
| **Tool call accuracy errors** | With `strict=True`, ALL properties must be in `required` array |

---

## Additional Resources

### Documentation

- [Microsoft Foundry Evaluation](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/evaluation)
- [Azure AI Evaluation SDK](https://learn.microsoft.com/python/api/azure-ai-evaluation/)
- [OpenTelemetry with Azure Monitor](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-overview)
- [Function Calling Best Practices](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/function-calling)
- [Azure AI Red Teaming](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/red-teaming)

### GitHub Samples

- [Agent Evaluation Samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/evaluations)
- [Telemetry Samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/telemetry)
- [Agentic Evaluators](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/evaluations/agentic_evaluators)
- [Red Team Samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/red_team)

---

> **Note:** Microsoft Foundry evaluation capabilities are in preview. APIs may evolve — refer to official documentation for the latest updates.