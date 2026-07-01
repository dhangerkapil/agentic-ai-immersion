# Local smoke test for the Employee Benefits Cost Advisor (Responses agent).
"""Builds the agent against your Foundry project and runs one non-streaming turn.

Prereqs: `az login`, plus FOUNDRY_PROJECT_ENDPOINT (or the workshop's
AI_FOUNDRY_PROJECT_ENDPOINT) and AZURE_AI_MODEL_DEPLOYMENT_NAME in the environment
or a .env file.

Run:  python test_local.py
"""
import asyncio
import os

from dotenv import load_dotenv

# Load the agent-local .env if present, then the workshop root .env as a fallback.
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

from main import (
    BUNDLED_SKILLS_DIR,
    SYSTEM_INSTRUCTIONS,
    _load_skill_content,
    _project_endpoint,
)


async def main() -> None:
    model = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    names = [n.strip() for n in os.environ.get("SKILL_NAMES", "").split(",") if n.strip()]
    instructions = SYSTEM_INSTRUCTIONS + _load_skill_content(names, BUNDLED_SKILLS_DIR)

    client = FoundryChatClient(
        project_endpoint=_project_endpoint(),
        model=model,
        credential=DefaultAzureCredential(),
    )
    agent = Agent(client=client, instructions=instructions, default_options={"store": False})

    result = await agent.run("In two sentences, explain what a P50 benefits cost benchmark means.")
    text = getattr(result, "text", None) or str(result)
    print("RESPONSE:\n", text)


if __name__ == "__main__":
    asyncio.run(main())
