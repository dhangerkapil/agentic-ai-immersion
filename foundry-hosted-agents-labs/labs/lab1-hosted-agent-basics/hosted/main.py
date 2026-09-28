"""Lab 1: the Benefits Marketplace concierge as a Microsoft Foundry Hosted Agent (Responses protocol).

Goal:    the smallest complete hosted agent: Agent Framework `Agent` + `FoundryChatClient` + three `@tool`
         functions over the systems of record (common.benefits_data) + the shared compliance block, served by
         `ResponsesHostServer`. Foundry builds a container from this folder, runs it, scales it and gives it
         an identity; locally the same file is a process on port 8088.
Inputs:  env FOUNDRY_PROJECT_ENDPOINT (injected when hosted; from .env locally), AZURE_AI_MODEL_DEPLOYMENT_NAME
         (or FOUNDRY_MODEL), optional BENEFITS_HOSTED_PORT. common/ and data/ are vendored here by prepare.py.
Outputs: HTTP server speaking the OpenAI Responses protocol (POST /responses) on port 8088.
Time:    10 min to read; the lab driver (../lab1_hosted_basics.py) starts and stops it for you.

Run:     python prepare.py && python main.py          (foreground; then python test_local.py in another terminal)
         python ../lab1_hosted_basics.py               (vendors, starts this server, runs S1 and S2, stops it)
Deploy:  python ../lab1_hosted_basics.py --deploy      (prints the azd commands; see ../README.md)

Verified shape (BRIEF-shared 5d, base repo hosted-agents/benefits-advisor-responses/main.py):
    client = FoundryChatClient(project_endpoint=ENDPOINT, model=MODEL, credential=DefaultAzureCredential())
    agent = Agent(client=client, instructions=INSTRUCTIONS, tools=tools, default_options={"store": False})
    ResponsesHostServer(agent).run()              # POST /responses, port 8088 locally

This file deliberately has no Redis history and no workflow tool. Lab 2 adds the knowledge base and the
message store; Lab 3 adds the multi-agent workflow; Stretch 5 adds delegation to a platform workflow agent.
"""
# %% Imports and path setup
from __future__ import annotations

import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

HERE = Path(__file__).resolve().parent
# Search order (last inserted wins): the repo root when run from the checkout, then hosted/ itself so the
# copies vendored by prepare.py (hosted/common, hosted/data) win inside the container.
for folder in (HERE.parents[2] if len(HERE.parents) > 2 else HERE, HERE):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

warnings.simplefilter("ignore")                  # preview-feature warnings from the SDKs at import time

from common import guardrails, benefits_data  # noqa: E402

from agent_framework import Agent, tool  # noqa: E402
from agent_framework.foundry import FoundryChatClient  # noqa: E402
from agent_framework_foundry_hosting import ResponsesHostServer  # noqa: E402
from azure.identity import DefaultAzureCredential  # noqa: E402
from pydantic import Field  # noqa: E402

AGENT_NAME = "benefits-concierge-hosted"
DEFAULT_MODEL = "gpt-5.4-mini"
ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.environ.get("FOUNDRY_MODEL") or DEFAULT_MODEL


def log(message: str) -> None:
    print(f"[hosted] {message}", flush=True)


# %% Instructions: the concierge role + the shared compliance block (verbatim, every agent)
ROLE_INSTRUCTIONS = """You are the Benefits Marketplace concierge, the front door of the Individual Marketplace, running as a hosted agent.
You serve participants of both lines of business: the Marketplace (plan education, comparisons, enrollment
windows) and Accounts (HRA balance, claims, debit cards, premium reimbursement).

How to work:
1. Confirm identity with participant_id and ZIP code only, then use the tools for every fact about the
   participant, the enrollment window or the reimbursement account. Never guess. If a tool returns an error
   object, explain it plainly.
2. In this version you have no plan search and no knowledge base. When a participant asks to compare plans
   or for a rule you cannot look up, say so and offer a licensed benefit advisor.
3. When a participant asks which plan to pick, asks to enroll, or describes a situation that needs judgment,
   offer a licensed benefit advisor and summarise the case in two sentences for the handoff.
4. Short paragraphs, plain language.

"""
INSTRUCTIONS = ROLE_INSTRUCTIONS + guardrails.COMPLIANCE_INSTRUCTIONS
assert INSTRUCTIONS.endswith(guardrails.COMPLIANCE_INSTRUCTIONS), "every agent carries the compliance block"


# %% Tools over the systems of record (pure functions from common.benefits_data, wrapped with @tool)
PID = Annotated[str, Field(description="Participant id such as P-1001")]


@tool(approval_mode="never_require")
def get_participant(participant_id: PID) -> dict:
    """Look up a Benefits Marketplace participant profile (age, county, Medicare status, current plan, preferences)."""
    return benefits_data.get_participant(participant_id)


@tool(approval_mode="never_require")
def get_enrollment_window(participant_id: PID) -> dict:
    """Which enrollment window applies to the participant today (AEP, IEP, OEP, SEP-possible, ACA open enrollment)."""
    return benefits_data.get_enrollment_window(participant_id)


@tool(approval_mode="never_require")
def get_hra_account(participant_id: PID) -> dict:
    """HRA reimbursement account: balance, allocation, auto-reimbursement, debit card status, claims summary."""
    return benefits_data.get_hra_account(participant_id)


TOOLS = [get_participant, get_enrollment_window, get_hra_account]


# %% YOUR TURN (5 min): add a get_sponsor tool. Wrap benefits_data.get_sponsor(sponsor_id) with @tool like the others,
# append it to TOOLS, restart, and ask "Who is my plan sponsor and how much is the HRA for the year?" as P-1001.
# Solution:
# @tool(approval_mode="never_require")
# def get_sponsor(sponsor_id: Annotated[str, Field(description="Sponsor id such as SP-NORTHWIND")]) -> dict:
#     """Plan sponsor programme: annual HRA amount, eligibility, eligible expense types, rollover notes."""
#     return benefits_data.get_sponsor(sponsor_id)
# TOOLS.append(get_sponsor)


# %% The agent
def tool_names() -> list[str]:
    return [getattr(t, "name", None) or getattr(t, "__name__", "?") for t in TOOLS]


def build_agent() -> Agent:
    if not ENDPOINT:
        sys.exit("[hosted] FOUNDRY_PROJECT_ENDPOINT is not set (locally: .env at the repo root; hosted: set by azd)")
    credential = DefaultAzureCredential()        # az login locally, the hosted agent's managed identity in Foundry
    client = FoundryChatClient(project_endpoint=ENDPOINT, model=MODEL, credential=credential)
    # store=False: the model service keeps no transcript of its own. Multi-turn state is the host server's
    # session handling (Lab 1) and, from Lab 2 on, our own message store.
    agent = Agent(client=client, name=AGENT_NAME, instructions=INSTRUCTIONS, tools=TOOLS, default_options={"store": False})
    log(f"agent {AGENT_NAME}: model={MODEL} tools={tool_names()} started={datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return agent


if __name__ == "__main__":
    server = ResponsesHostServer(build_agent())
    port = int(os.environ.get("BENEFITS_HOSTED_PORT", "8088"))
    if port != 8088:
        # VERIFY against https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents before delivery: run(port=...)
        server.run(port=port)
    else:
        server.run()                             # POST /responses on http://localhost:8088; Foundry sets the port when hosted
