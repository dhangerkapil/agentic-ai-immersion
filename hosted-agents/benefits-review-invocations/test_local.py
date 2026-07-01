# Local smoke test for the Employee Benefits Review (Invocations agent).
"""Builds the agent against your Foundry project and runs one structured review.

Prereqs: `az login`, plus FOUNDRY_PROJECT_ENDPOINT (or the workshop's
AI_FOUNDRY_PROJECT_ENDPOINT) and AZURE_AI_MODEL_DEPLOYMENT_NAME in the environment
or a .env file.

Run:  python test_local.py
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

from main import REVIEW_INSTRUCTIONS, _project_endpoint

SAMPLE_PAYLOAD = (
    "Company: 200-employee fintech.\n"
    "Benefits: basic health insurance (employee only), 5% retirement match, "
    "12 days annual leave, no life insurance, no dental, no parental leave top-up."
)


async def main() -> None:
    model = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    client = FoundryChatClient(
        project_endpoint=_project_endpoint(),
        model=model,
        credential=DefaultAzureCredential(),
    )
    agent = Agent(client=client, instructions=REVIEW_INSTRUCTIONS)

    result = await agent.run(f"Review this employee benefits program:\n{SAMPLE_PAYLOAD}")
    text = getattr(result, "text", None) or str(result)
    print("REVIEW:\n", text[:1400])


if __name__ == "__main__":
    asyncio.run(main())
