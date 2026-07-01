// AgentOps — infrastructure for the Employee Benefits Concierge hosted agent.
// Deploys/ensures the chat model deployment used by the agent on an existing
// Microsoft Foundry (AI Services) account. Environment-specific values come from
// the parameter files under ./environments/.

@description('Name of the existing Microsoft Foundry (AI Services) account.')
param foundryAccountName string

@description('Azure region for resources.')
param location string = resourceGroup().location

@description('Chat model to deploy for the agent.')
param modelName string = 'gpt-5.4-mini'

@description('Model version.')
param modelVersion string = '2025-04-14'

@description('Provisioned capacity (thousands of tokens per minute).')
param capacity int = 20

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: foundryAccountName
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  parent: account
  name: modelName
  sku: {
    name: 'GlobalStandard'
    capacity: capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
  }
}

output modelDeploymentName string = modelDeployment.name
output location string = location
