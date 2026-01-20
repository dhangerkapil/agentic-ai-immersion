# Copyright (c) Microsoft. All rights reserved.
"""
Web Search Agent - A hosted agent that uses Bing Grounding for real-time web search.

This agent demonstrates the Agent Framework pattern for creating a hosted agent
that can search the web for current information using Bing Grounding.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from agent_framework import ChatAgent, HostedWebSearchTool
from agent_framework_azure_ai import AzureAIAgentClient
from azure.ai.agentserver.agentframework import from_agent_framework
from azure.identity.aio import DefaultAzureCredential

# Load environment variables from root .env file
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')


def get_agent() -> ChatAgent:
    """Create and return a ChatAgent with Bing Grounding search tool.
    
    This function creates a ChatAgent configured with:
    - Azure AI Agent Client for model access
    - Bing Grounding tool for real-time web search
    - Instructions for helpful, well-sourced responses
    
    Required Environment Variables (from root .env):
        AI_FOUNDRY_PROJECT_ENDPOINT: Your Microsoft Foundry project endpoint
        AZURE_AI_MODEL_DEPLOYMENT_NAME: The deployment name for your chat model
        BING_CONNECTION_ID: Connection ID for Bing Grounding in your project
    
    Returns:
        ChatAgent: A configured agent ready to handle web search queries
    """
    # Validate required environment variables
    assert "AI_FOUNDRY_PROJECT_ENDPOINT" in os.environ, (
        "AI_FOUNDRY_PROJECT_ENDPOINT environment variable must be set."
    )
    assert "AZURE_AI_MODEL_DEPLOYMENT_NAME" in os.environ, (
        "AZURE_AI_MODEL_DEPLOYMENT_NAME environment variable must be set."
    )
    assert "BING_CONNECTION_ID" in os.environ, (
        "BING_CONNECTION_ID environment variable must be set to use HostedWebSearchTool."
    )
    
    # Create Azure AI Agent Client with DefaultAzureCredential
    chat_client = AzureAIAgentClient(
        endpoint=os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"],
        async_credential=DefaultAzureCredential(),
    )

    # Create Bing Grounding search tool using HostedWebSearchTool
    # The connection_id enables web search capabilities through your AI Foundry project
    bing_search_tool = HostedWebSearchTool(
        name="Bing Grounding Search",
        description="Search the web for current information using Bing",
        connection_id=os.environ["BING_CONNECTION_ID"],
    )

    # Create ChatAgent with the Bing search tool
    agent = ChatAgent(
        chat_client=chat_client,
        name="WebSearchAgent",
        instructions=(
            "You are a helpful assistant that can search the web for current information. "
            "Use the Bing search tool to find up-to-date information and provide accurate, "
            "well-sourced answers. Always cite your sources when possible. "
            "For time-sensitive queries, include the date of the information when available."
        ),
        tools=bing_search_tool,
    )
    return agent


if __name__ == "__main__":
    # Run the agent as a hosted agent using the AgentServer adapter
    from_agent_framework(get_agent()).run()
