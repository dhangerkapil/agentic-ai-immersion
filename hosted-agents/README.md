# 🚀 Hosted Agents - Web Search Agent Deployment

Deploy a **Web Search Agent** to Microsoft Foundry as a hosted agent. This agent uses Bing Grounding for real-time web search capabilities.

---

## 📋 Table of Contents

- [What are Hosted Agents?](#what-are-hosted-agents)
- [Prerequisites](#prerequisites)
- [Deployment Guide](#deployment-guide)
- [Testing Your Agent](#testing-your-agent)
- [Troubleshooting](#troubleshooting)
- [Resource Cleanup](#resource-cleanup)

---

## 🤖 What are Hosted Agents?

Hosted Agents are containerized AI agents that run as fully managed services in Microsoft Foundry. You provide the agent code and configuration, and Microsoft Foundry handles:

- Container building and registry management
- Deployment and scaling infrastructure
- Model integration and API endpoints
- Monitoring and logging

### Included Agent: Web Search Agent

| Agent | Description | Tools |
|-------|-------------|-------|
| **Web Search Agent** | Searches the web for real-time information | Bing Grounding |

---

## ✅ Prerequisites

### ⚠️ Region Availability

**Important:** Hosted Agents is a preview feature currently available in **North Central US only**.

If your AI Foundry project is in a different region, you'll get the error: `"Hosted Agents are not enabled in this region"`. In that case, you need to create a new project in **North Central US**.

Check the latest region support: [Hosted Agents Region Availability](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/hosted-agents?view=foundry&tabs=cli#region-availability)

### Install Azure Developer CLI (azd)

```powershell
# Windows
winget install microsoft.azd
```

```bash
# Linux
curl -fsSL https://aka.ms/install-azd.sh | bash

# MacOS
brew tap azure/azd && brew install azd
```

### Required Azure Resources

You need the following resources:
- Microsoft Foundry Project **(must be in North Central US region)**
- Bing Grounding Connection (configured in your project)
- Model Deployment (e.g., `gpt-4o`)

### Required Environment Variables

The agent requires these environment variables (set via `azd env set`):

| Variable | Description |
|----------|-------------|
| `AI_FOUNDRY_PROJECT_ENDPOINT` | Your Microsoft Foundry project endpoint |
| `AZURE_AI_PROJECT_ID` | Full resource ID of your project |
| `AZURE_SUBSCRIPTION_ID` | Your Azure subscription ID |
| `AZURE_RESOURCE_GROUP` | Your resource group name |
| `AZURE_AI_PROJECT_NAME` | Your AI Foundry project name |

---

## 📦 Deployment Guide

### Deploy with Existing Resources

Use this option since you already have a Microsoft Foundry project from the workshop.

#### Quick Command Reference

```powershell
cd hosted-agents
azd auth login
azd init
azd env set AZURE_SUBSCRIPTION_ID <your-subscription-id>
azd env set AZURE_RESOURCE_GROUP <your-resource-group>
azd env set AZURE_AI_PROJECT_NAME <your-project-name>
azd env set AZURE_AI_PROJECT_ID "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.CognitiveServices/accounts/<account-name>/projects/<project-name>"
azd env set AI_FOUNDRY_PROJECT_ENDPOINT "https://<account-name>.services.ai.azure.com/api/projects/<project-name>"
azd ai agent init
azd deploy
```

---

### Detailed Steps

#### Step 1: Navigate to Project Directory

```powershell
cd hosted-agents
```

Verify the structure:
```powershell
ls
# Should show: README.md, azure.yaml, src/
```

#### Step 2: Sign in to Azure

```powershell
azd auth login
```

Your browser will open for authentication. Sign in with your Azure account.

#### Step 3: Initialize azd Environment

```powershell
azd init
```

**When prompted:**
1. Select **"Scan current directory"** (it will detect the `azure.yaml` file)
2. Enter an environment name (e.g., `websearch-agent-dev`)

This creates a `.azure` folder to store your environment configuration.

#### Step 4: Connect to Your Existing Resources

Set environment variables to point to your Azure resources:

```powershell
# Basic resource info
azd env set AZURE_SUBSCRIPTION_ID <your-subscription-id>
azd env set AZURE_RESOURCE_GROUP <your-resource-group>
azd env set AZURE_AI_PROJECT_NAME <your-project-name>

# Required for hosted agent deployment
azd env set AZURE_AI_PROJECT_ID "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.CognitiveServices/accounts/<account-name>/projects/<project-name>"
azd env set AI_FOUNDRY_PROJECT_ENDPOINT "https://<account-name>.services.ai.azure.com/api/projects/<project-name>"
```

> 💡 **Tip:** Replace placeholders with your actual values.

#### Step 5: Initialize the Agent

```powershell
azd ai agent init
```

This command detects agents defined in `azure.yaml` and configures them.

**You'll be prompted to configure:**

| Setting | Recommended Value | Description |
|---------|-------------------|-------------|
| Model SKU | `GlobalStandard` | Deployment tier |
| Model deployment | `gpt-4o` | Your existing model |
| Container memory | `2Gi` | Memory allocation |
| Container CPU | `1` | CPU cores |
| Min replicas | `1` | Minimum instances |
| Max replicas | `3` | Maximum instances |

#### Step 6: Deploy the Agent

```powershell
azd deploy
```

**What happens:**
1. 📦 Builds the agent container image
2. 🏷️ Pushes to Azure Container Registry
3. 🚀 Deploys to Microsoft Foundry
4. ⚙️ Configures environment variables and model access

**Deployment typically takes 5-10 minutes.**

#### Step 7: Verify Deployment

After successful deployment, you'll see:

```
✅ Agent deployed successfully!

Agent playground URL: https://ai.azure.com/.../playground
Agent endpoint URL: https://<your-endpoint>/api/...
```

---

## 🧪 Testing Your Agent

### Option 1: Agent Playground (Recommended)

1. Copy the **Agent playground URL** from deployment output
2. Open in your browser
3. Start chatting with your agent

**Example queries:**
- "What are the latest AI news today?"
- "Search for recent Microsoft announcements"
- "What's happening in the tech industry this week?"

### Option 2: API Endpoint

```python
import requests

endpoint = "https://your-agent-endpoint-url"
headers = {
    "Content-Type": "application/json",
    "api-key": "your-api-key"
}

payload = {
    "messages": [
        {"role": "user", "content": "What are the latest AI trends?"}
    ]
}

response = requests.post(endpoint, json=payload, headers=headers)
print(response.json())
```

### Option 3: Using curl

```powershell
curl -X POST "https://your-agent-endpoint/responses" `
  -H "Content-Type: application/json" `
  -d '{"input": "What are the latest AI trends?", "stream": false}'
```

---

## 🔧 Troubleshooting

### Issue: "no project exists; run `azd init`"

**Cause:** You haven't initialized the azd project yet.

**Solution:**
```powershell
azd init
# Select "Scan current directory"
# Enter an environment name
```

### Issue: "infrastructure has not been provisioned"

**Cause:** When using existing resources, this error can sometimes appear.

**Solution:** The `azd ai agent init` command should handle this. If it persists, try:
```powershell
azd env set AZURE_RESOURCE_GROUP <your-resource-group>
azd ai agent init
azd deploy
```

### Issue: "Hosted Agents are not enabled in this region"

**Cause:** Your AI Foundry project is in a region that doesn't support hosted agents.

**Solution:** Currently, hosted agents are only available in **North Central US**. You need to:
1. Create a new AI Foundry project in North Central US
2. Update your environment variables to point to the new project

See: [Hosted Agents Region Availability](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/hosted-agents?view=foundry&tabs=cli#region-availability)

### Issue: "AI_FOUNDRY_PROJECT_ENDPOINT environment variable is required"

**Cause:** The project endpoint is not set.

**Solution:**
```powershell
azd env set AI_FOUNDRY_PROJECT_ENDPOINT "https://your-foundry.services.ai.azure.com/api/projects/your-project"
```

### Issue: "BING_CONNECTION_ID not set"

**Cause:** The agent can't find the Bing Grounding connection.

**Solution:** The `BING_CONNECTION_ID` environment variable must be set in the `agent.yaml` file. Verify your Bing Grounding connection exists in your AI Foundry project and the connection ID is correct.

### Issue: "Model not available in selected region"

**Solution:** Check [model region availability](https://learn.microsoft.com/azure/ai-foundry/agents/concepts/model-region-support).

### Issue: "Agent container failed to start"

**Solution:**
1. Check container logs in Azure Portal
2. Verify `requirements.txt` has all dependencies
3. Ensure sufficient memory/CPU allocated

### Verify Environment Variables

```powershell
azd env get-values
```

---

## 🗑️ Resource Cleanup

To avoid unnecessary charges:

```powershell
azd down
```

This removes deployed agent containers and associated resources.

> ⚠️ This does NOT delete your AI Foundry project or pre-existing resources.

---

## 📁 Folder Structure

```
hosted-agents/
├── .azure/             # azd environment config (created after azd init)
├── README.md           # This guide
├── azure.yaml          # azd project configuration
└── src/
    └── WebSearchAgent/
        ├── main.py           # Agent implementation
        ├── agent.yaml        # Agent configuration
        ├── Dockerfile        # Container definition
        └── requirements.txt  # Python dependencies
```

---

## 📚 Additional Resources

- [Azure Developer CLI Documentation](https://aka.ms/azd)
- [Hosted Agents Documentation](https://aka.ms/azdaiagent/docs)
- [Microsoft Foundry Documentation](https://learn.microsoft.com/azure/ai-foundry/)
- [Agent Framework GitHub](https://github.com/microsoft/agent-framework)

---

## ⚠️ Important Notice

This template is for **learning and development purposes**. For production:
- Implement additional security measures
- Follow [Microsoft Foundry security best practices](https://learn.microsoft.com/azure/ai-foundry/)
