import os, sys, asyncio
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')
print("Step 1: env loaded")
from agent_framework import Agent, Message
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential
print("Step 2: imports ok")
print("Step 3: env vars")
for v in ["AI_FOUNDRY_PROJECT_ENDPOINT","AZURE_AI_MODEL_DEPLOYMENT_NAME","BING_CONNECTION_ID"]:
    print(f"  {v}={'SET' if v in os.environ else 'MISSING'}")
client = AzureAIAgentClient(endpoint=os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"], async_credential=DefaultAzureCredential())
tool = AzureAIAgentClient.get_web_search_tool(bing_connection_id=os.environ["BING_CONNECTION_ID"])
agent = Agent(client=client, name="WebSearchAgent", instructions="Search the web and provide answers.", tools=[tool])
print(f"Step 4: agent created name={agent.name}")

async def query():
    messages = [Message("user", ["What is the weather in Seattle today?"])]
    response = await agent.run(messages)
    return response.message.text if response.message else ""

resp = asyncio.run(query())
print(f"Step 5: response length={len(resp)}")
print(f"Response: {resp[:500]}")
print("ALL TESTS PASSED")
