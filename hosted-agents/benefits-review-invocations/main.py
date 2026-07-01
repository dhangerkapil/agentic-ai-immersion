# Employee Benefits Review — Foundry Hosted Agent (INVOCATIONS protocol)
"""Foundry Hosted Agent — Employee Benefits Review using the INVOCATIONS protocol.

Contrasts with the Benefits Advisor agent (../benefits-advisor-responses), which uses
the Responses protocol. The Invocations protocol is a single structured request ->
structured response (fire-and-forget): ideal for batch processing, API-to-API
integration, and deterministic pipelines. No multi-turn conversation, no streaming,
no model-directed tool use.

Required environment variables:
    FOUNDRY_PROJECT_ENDPOINT        Foundry project endpoint (auto-injected when hosted)
    AZURE_AI_MODEL_DEPLOYMENT_NAME  Chat model deployment name

Learn more:
    Hosted agents: https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents
"""
from __future__ import annotations

import logging
import os
import warnings

# Silence the SDK ExperimentalWarning emitted at import time (preview features).
warnings.simplefilter("ignore")

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import InvocationsHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("benefits-review")

REVIEW_INSTRUCTIONS = """\
You are an Employee Benefits Review analyst. You receive a structured description of a
company's employee benefits program and return a concise, structured benefits review.

Produce a review with these sections:
1. **Summary** — one paragraph overall assessment.
2. **Strengths** — bullet list of what the program does well.
3. **Gaps** — bullet list of missing or below-market elements.
4. **Benchmark Positioning** — estimate the market position (P25 / P50 / P75) per category
   (healthcare, retirement, risk benefits, time off), stating assumptions.
5. **Recommendations** — prioritized, actionable improvements (quick win / medium / strategic).

Rules:
- Be decisive and concise. Do NOT ask clarifying questions — state assumptions instead.
- Use a generic currency unit (CU) unless a currency is specified.
- Return clean Markdown.
"""


def _project_endpoint() -> str:
    """Foundry project endpoint (injected when hosted; falls back to the workshop var locally)."""
    return os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"]


def main() -> None:
    """Build the review agent and start the Invocations host server (single request/response)."""
    model = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    client = FoundryChatClient(
        project_endpoint=_project_endpoint(),
        model=model,
        credential=DefaultAzureCredential(),
    )
    agent = Agent(client=client, instructions=REVIEW_INSTRUCTIONS)
    logger.info("Employee Benefits Review starting — Invocations protocol | model=%s", model)
    InvocationsHostServer(agent).run()


if __name__ == "__main__":
    main()
