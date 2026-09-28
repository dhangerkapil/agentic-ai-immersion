"""Lab 2 hosted agent: benefits-concierge-hosted v2, knowledge over MCP plus external session state.

Runs on:  Microsoft Foundry as a container (azd builds it from this folder) and, for testing, as a local
          process on port 8088. Same file both places. This is the product; the notebook is the cockpit.
Goal:     Agent Framework `Agent` + `FoundryChatClient` behind `ResponsesHostServer`, with
            * five tools over the systems of record (get_participant, get_enrollment_window, get_hra_account,
              search_plans, compare_plans) wrapped with @tool,
            * the Foundry IQ knowledge base as an `MCPStreamableHTTPTool` (endpoint from BENEFITS_KB_MCP_URL, Entra
              bearer token injected by an httpx auth class, audience https://search.azure.com/.default),
            * conversation history OUTSIDE the container: common.message_store (Redis when BENEFITS_REDIS_URL is set,
              file store otherwise) and the common.session_store map. Kill the process, start it again, the
              participant continues where they were.
Inputs:   env FOUNDRY_PROJECT_ENDPOINT (injected when hosted), AZURE_AI_MODEL_DEPLOYMENT_NAME, BENEFITS_KB_MCP_URL,
          optional BENEFITS_REDIS_URL, BENEFITS_MESSAGE_STORE_DIR, BENEFITS_SESSION_DIR, BENEFITS_HOSTED_PORT,
          APPLICATIONINSIGHTS_CONNECTION_STRING (Lab 4 turns tracing on with it).
Outputs:  HTTP server speaking the OpenAI Responses protocol (POST /responses) on port 8088.
Time:     10 min to read; ../lab2_hosted_knowledge.py starts and stops it for you.

Run:      python prepare.py && python main.py          (then python test_local.py in another terminal)
Deploy:   python ../lab2_hosted_knowledge.py --deploy   (prints the azd commands; see README)

Verified shapes (BRIEF-shared 5d, base repo hosted-agents/benefits-advisor-responses/main.py):
    client = FoundryChatClient(project_endpoint=ENDPOINT, model=MODEL, credential=DefaultAzureCredential())
    agent = Agent(client=client, instructions=INSTRUCTIONS, tools=tools, default_options={"store": False})
    ResponsesHostServer(agent).run()
    MCPStreamableHTTPTool(name="benefits-kb", url=MCP_URL, http_client=httpx.AsyncClient(auth=..., headers=...))
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

from common import guardrails, session_store, benefits_data  # noqa: E402

import httpx  # noqa: E402
from agent_framework import Agent, MCPStreamableHTTPTool, tool  # noqa: E402
from agent_framework.foundry import FoundryChatClient  # noqa: E402
from agent_framework_foundry_hosting import ResponsesHostServer  # noqa: E402
from azure.identity import DefaultAzureCredential  # noqa: E402
from pydantic import Field  # noqa: E402

LAB = "lab2"
AGENT_NAME = "benefits-concierge-hosted"
DEFAULT_MODEL = "gpt-5.4-mini"
ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.environ.get("FOUNDRY_MODEL") or DEFAULT_MODEL
KB_MCP_URL = os.environ.get("BENEFITS_KB_MCP_URL", "")
KB_SCOPE = "https://search.azure.com/.default"
REDIS_URL = os.environ.get("BENEFITS_REDIS_URL", "")
MESSAGE_STORE_DIR = Path(os.environ.get("BENEFITS_MESSAGE_STORE_DIR", str(HERE / "message_store")))
SESSION_DIR = Path(os.environ.get("BENEFITS_SESSION_DIR", str(HERE / "sessions")))


def log(message: str) -> None:
    print(f"[hosted] {message}", flush=True)


# %% Instructions: the concierge role + knowledge rules + the shared compliance block (verbatim, every agent)
ROLE_INSTRUCTIONS = """You are the Benefits Marketplace concierge, the front door of the Individual Marketplace, running as a hosted agent.
You serve participants of both lines of business: the Marketplace (plan education, comparisons, enrollment
windows) and Accounts (HRA balance, claims, debit cards, premium reimbursement).

How to work:
1. Confirm identity with participant_id and ZIP code only, then use the tools for every fact about the
   participant, plans or accounts. Never guess. If a tool returns an error object, explain it plainly.
2. Knowledge: call knowledge_base_retrieve FIRST for any question about rules, enrollment periods, plan types,
   proof of payment, debit cards or reimbursement. Cite the doc id in square brackets, for example [KB-ACC-001],
   after each statement that comes from it. If the knowledge tool is unavailable, say the rule text is not at hand.
3. Plan comparisons: search_plans, then compare_plans for 2 to 4 plan ids. Show a compact table (plan, carrier,
   type, premium, deductible, max out of pocket, stars, network, drug coverage, formulary tier for any drug the
   participant named). Neutral trade-offs only, never a ranking. Doctor networks are not in the data: say the
   participant must confirm a doctor with the carrier or an advisor.
4. When a participant asks which plan to pick, asks to enroll, or describes a situation that needs judgment,
   say a licensed benefit advisor will help and offer the handoff.
5. This conversation may continue after a restart. Earlier turns are provided to you; refer back to them
   (participant id, drugs and plans already discussed, balances already quoted) instead of asking again.
6. Short paragraphs, plain language.

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
    return benefits_data.get_enrollment_window(participant_id, today=os.environ.get("BENEFITS_TODAY"))


@tool(approval_mode="never_require")
def get_hra_account(participant_id: PID) -> dict:
    """HRA reimbursement account: balance, allocation, auto-reimbursement, debit card status, claims summary."""
    return benefits_data.get_hra_account(participant_id)


@tool(approval_mode="never_require")
def search_plans(county: Annotated[str, Field(description="Utah county name such as Salt Lake")],
                 plan_type: Annotated[str | None, Field(description="Medicare Advantage HMO, Medicare Advantage PPO, "
                                                                    "Medigap Plan G, Medigap Plan N, Part D, ACA Bronze, "
                                                                    "ACA Silver, ACA Gold")] = None,
                 max_premium: Annotated[float | None, Field(description="Maximum monthly premium")] = None,
                 drug_name: Annotated[str | None, Field(description="Drug to check the formulary tier for, "
                                                                    "for example atorvastatin")] = None) -> list[dict]:
    """Plans available in a county for plan year 2027, sorted by premium then star rating (max 10). Educational only."""
    return benefits_data.search_plans(county=county, state="UT", plan_type=plan_type, max_premium=max_premium,
                                 needs_drug_coverage=True if drug_name else None, drug_name=drug_name)


@tool(approval_mode="never_require")
def compare_plans(plan_ids: Annotated[list[str], Field(description="Two to four plan ids such as MA-CONTOSO-HMO-01")]) -> dict:
    """Side by side comparison fields for the given plans. Neutral facts; the agent must not rank them."""
    return benefits_data.compare_plans(plan_ids)


FUNCTION_TOOLS = [get_participant, get_enrollment_window, get_hra_account, search_plans, compare_plans]


# %% Knowledge: the Foundry IQ knowledge base over MCP, called with the container's own identity
class EntraBearerAuth(httpx.Auth):
    """Fresh Entra token per request for the knowledge base MCP endpoint (audience: Azure AI Search).

    Locally the token comes from az login; in the container from the hosted agent's managed identity, which
    needs Search Index Data Reader on the search service. No keys anywhere.
    """

    def __init__(self, credential, scope: str = KB_SCOPE):
        self.credential = credential
        self.scope = scope

    def auth_flow(self, request):
        # VERIFY against https://learn.microsoft.com/agent-framework/ (MCP tools) before delivery: httpx runs this
        # sync generator for AsyncClient requests too; credential.get_token caches until near expiry.
        token = self.credential.get_token(self.scope).token
        request.headers["Authorization"] = f"Bearer {token}"
        yield request


def knowledge_tool(credential) -> MCPStreamableHTTPTool | None:
    """The knowledge base as an in-process MCP tool. Returns None when BENEFITS_KB_MCP_URL is not set."""
    if not KB_MCP_URL:
        log("knowledge: BENEFITS_KB_MCP_URL not set, the agent runs without the knowledge base")
        return None
    # VERIFY against https://learn.microsoft.com/agent-framework/ before delivery: MCPStreamableHTTPTool keyword
    # names (name, url, http_client) and that the tool list exposes knowledge_base_retrieve to the model.
    http_client = httpx.AsyncClient(auth=EntraBearerAuth(credential), timeout=60)
    log(f"knowledge: MCP {KB_MCP_URL.split('?')[0]}")
    return MCPStreamableHTTPTool(name="benefits-kb", url=KB_MCP_URL, http_client=http_client)


# %% Message store: history outside the container (Agent 2 owns common/message_store.py; Lab 2 imports it)
try:
    from common import message_store as _message_store  # noqa: E402
except ImportError:                              # module not written yet, or not vendored: in-memory only
    _message_store = None


def build_message_store():
    """History provider from common.message_store: Redis when BENEFITS_REDIS_URL is set, file store otherwise.

    get_message_store(default_dir) picks the backend (RedisMessageStore / FileMessageStore); as_history_provider
    wraps it in the async history-provider surface the Agent reads before and writes after every run. With
    Redis, build_history_provider hands back the framework's own RedisHistoryProvider instead (base repo
    threads/2 pattern). Returns None when the module is missing: history then stays in process memory, which
    is exactly the failure the kill-and-restart demo exposes.
    """
    if _message_store is None:
        log("WARNING common.message_store not found: history stays in memory and dies with the process")
        return None
    # VERIFY against https://learn.microsoft.com/agent-framework/user-guide/agents/conversation-storage before
    # delivery: the provider returned here is usable as the agent's chat message store (context_providers).
    if REDIS_URL:
        provider = _message_store.build_history_provider(MESSAGE_STORE_DIR)
        log(f"history: redis ({REDIS_URL.split('@')[-1]}) via {type(provider).__name__}")
        return provider
    store = _message_store.get_message_store(MESSAGE_STORE_DIR)
    log(f"history: {_message_store.describe(store)}")
    return _message_store.as_history_provider(store)


def agent_kwargs_for_store(provider) -> dict:
    """Wire the history provider into the Agent; nothing when we fell back to in-memory."""
    if provider is None:
        return {}
    return {"context_providers": [provider]}


SESSIONS = session_store.get_session_store(SESSION_DIR)


def record_session(session_id: str, participant_id: str | None = None) -> None:
    """Keep the session map in step with the message store (turn count, last seen)."""
    rec = SESSIONS.get(session_id) or session_store.SessionRecord.new(
        session_id, agent_name=AGENT_NAME, participant_id=participant_id, history=("redis" if REDIS_URL else "file"))
    rec.conversation_id = rec.conversation_id or session_id
    if participant_id and not rec.participant_id:
        rec.participant_id = participant_id
    SESSIONS.put(rec.touch())


# %% Tracing (optional, Lab 4): the container gets APPLICATIONINSIGHTS_CONNECTION_STRING from its environment
def configure_tracing() -> bool:
    connection = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection:
        return False
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(connection_string=connection)
        # VERIFY against https://learn.microsoft.com/agent-framework/user-guide/observability before delivery.
        from agent_framework.observability import configure_otel_providers

        configure_otel_providers()
        return True
    except Exception as exc:                     # noqa: BLE001
        log(f"tracing setup failed ({type(exc).__name__}); running without traces")
        return False


# %% The agent
def build_agent() -> Agent:
    if not ENDPOINT:
        sys.exit("[hosted] FOUNDRY_PROJECT_ENDPOINT is not set (locally: .env at the repo root; hosted: set by azd)")
    credential = DefaultAzureCredential()        # az login locally, the hosted agent's managed identity in Foundry
    client = FoundryChatClient(project_endpoint=ENDPOINT, model=MODEL, credential=credential)
    tools = list(FUNCTION_TOOLS)
    kb = knowledge_tool(credential)
    if kb is not None:
        tools.append(kb)
    store = build_message_store()
    # store=False: the model service keeps no transcript; history is ours (Redis or files) and travels with the
    # session id, so any replica or a restarted container can continue the conversation.
    agent = Agent(client=client, name=AGENT_NAME, instructions=INSTRUCTIONS, tools=tools,
                  default_options={"store": False}, **agent_kwargs_for_store(store))
    log(f"agent {AGENT_NAME} v2: model={MODEL} tools={len(tools)} knowledge={'on' if kb else 'off'} "
        f"sessions={session_store.describe(SESSIONS)} started={datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return agent


# %% YOUR TURN (5 min): add get_claim_status so S2 (denied claim CLM-9003) can be answered end to end.
# Wrap benefits_data.get_claim_status(claim_id) with @tool like the others, append it to FUNCTION_TOOLS, restart,
# and ask "Why was my claim CLM-9003 denied and what proof do you accept?" as P-1003. The denial reason comes
# from the tool, the accepted proof list from the knowledge base with a [KB-ACC-001] citation.
# Solution:
# @tool(approval_mode="never_require")
# def get_claim_status(claim_id: Annotated[str, Field(description="Claim id such as CLM-9003")]) -> dict:
#     """Status of one HRA claim, with the human readable denial reason when denied."""
#     return benefits_data.get_claim_status(claim_id)
# FUNCTION_TOOLS.append(get_claim_status)

if __name__ == "__main__":
    log(f"tracing: {'on' if configure_tracing() else 'off (no APPLICATIONINSIGHTS_CONNECTION_STRING)'}")
    server = ResponsesHostServer(build_agent())
    port = int(os.environ.get("BENEFITS_HOSTED_PORT", "8088"))
    if port != 8088:
        # VERIFY against https://learn.microsoft.com/azure/foundry/agents/how-to/hosted-agents before delivery: run(port=...)
        server.run(port=port)
    else:
        server.run()                             # POST /responses on http://localhost:8088; Foundry sets the port when hosted
