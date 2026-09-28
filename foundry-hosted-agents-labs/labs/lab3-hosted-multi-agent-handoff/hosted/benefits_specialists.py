"""Specialist agents for the Benefits Marketplace triage workflow (Lab 3, runs inside the hosted container).

  marketplace-guide    plan education and neutral comparison: search_plans, compare_plans, get_enrollment_window, search_knowledge
  accounts-assistant   HRA help: get_hra_account, get_claim_status, list_eligible_expenses, search_knowledge
  compliance-reviewer  reads a draft, returns a ReviewVerdict (structured output), no tools
  advisor-handoff      writes the HandoffPacket (structured output) for the licensed benefit advisor, no tools

Every instruction string ends with guardrails.COMPLIANCE_INSTRUCTIONS. Structured output uses the verified shape
    Agent(client=..., default_options={"response_format": PydanticModel})
Knowledge: by default a local search over data/knowledge (vendored into the container by prepare.py). When
BENEFITS_KB_MCP_URL is set (Lab 2's Foundry IQ knowledge base), the specialists get an MCPStreamableHTTPTool instead.

Adapted from the Option B lab3 benefits_specialists.py: the Lab 1 middleware package is gone, tools are wrapped with
@tool here, and search_knowledge is a plain function so the container has no dependency on an index.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
for folder in (HERE.parents[2] if len(HERE.parents) > 2 else HERE, HERE):     # repo root, then vendored copies
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
from common import guardrails, benefits_data  # noqa: E402

Lob = Literal["marketplace", "accounts", "both"]
KB_MCP_URL = os.environ.get("BENEFITS_KB_MCP_URL", "")


# ---------- structured outputs ----------
class ReviewVerdict(BaseModel):
    """What compliance-reviewer returns. All fields required so the JSON schema works in strict mode."""

    compliant: bool = Field(description="True when the draft follows every compliance rule")
    violations: list[str] = Field(description="One short line per rule broken, empty when compliant")
    offending_section: Literal["marketplace-guide", "accounts-assistant", "none"] = Field(
        description="Which specialist's section needs rewriting, or none")
    guidance: str = Field(description="Concrete rewrite guidance for the specialist, or 'none'")


class FactWithSource(BaseModel):
    fact: str = Field(description="One fact, plain language, no identifiers beyond participant_id")
    source: str = Field(description="Where it came from: a tool name such as get_hra_account or a doc id such as [KB-ACC-001]")


class HandoffPacket(BaseModel):
    """The case packet a licensed benefit advisor reads before calling the participant back."""

    case_id: str
    participant_id: str
    lob: Lob
    summary: str = Field(description="Two to four sentences: who, what they asked, what was explained")
    participant_goals: list[str]
    facts_gathered: list[FactWithSource]
    options_discussed: list[str] = Field(description="Neutral descriptions of options covered. Never a recommendation or ranking")
    open_questions: list[str]
    recommended_next_step_for_advisor: str = Field(description="What the advisor should do next, for example review two plans with the participant")
    compliance_flags: list[str] = Field(description="Flags raised by compliance-reviewer or the heuristic check; empty when clean")
    created_at: str = Field(description="ISO 8601 timestamp supplied in the prompt")


# ---------- tools (plain functions wrapped by as_tools) ----------
County = Annotated[str, Field(description="Utah county name such as Salt Lake, Utah, Davis or Weber")]
PID = Annotated[str, Field(description="Participant id such as P-1001")]


def search_plans(
    county: County,
    plan_type: Annotated[str | None, Field(description="Medicare Advantage HMO, Medicare Advantage PPO, Medigap Plan G, Medigap Plan N, Part D, ACA Bronze, ACA Silver, ACA Gold; omit for all")] = None,
    max_premium: Annotated[float | None, Field(description="Only plans at or below this monthly premium")] = None,
    needs_drug_coverage: Annotated[bool | None, Field(description="True to keep only plans with drug coverage")] = None,
    drug_name: Annotated[str | None, Field(description="Prescription name such as atorvastatin; returns the formulary tier when known")] = None,
) -> list[dict]:
    """Search 2027 plans offered in a Utah county. Returns up to 10 plans sorted by premium then star
    rating, with formulary tier examples. Educational comparison only."""
    return benefits_data.search_plans(county.strip().title(), "UT", plan_type, max_premium, needs_drug_coverage, drug_name)


def compare_plans(plan_ids: Annotated[list[str], Field(description="Two to four plan ids such as MA-CONTOSO-HMO-01")]) -> dict:
    """Side-by-side comparison of plans: premium, deductible, max out of pocket, star rating, network,
    drug coverage, service area. Present the fields neutrally."""
    return benefits_data.compare_plans([plan_id.strip().upper() for plan_id in plan_ids])


def get_enrollment_window(participant_id: PID) -> dict:
    """Which enrollment window applies to the participant today (AEP, IEP, OEP, SEP-possible, ACA open enrollment)."""
    return benefits_data.get_enrollment_window(participant_id.strip().upper())


def get_hra_account(participant_id: PID) -> dict:
    """HRA reimbursement account: balance, allocation, auto-reimbursement, debit card status, claims summary."""
    return benefits_data.get_hra_account(participant_id.strip().upper())


def get_claim_status(claim_id: Annotated[str, Field(description="Claim id such as CLM-9003")]) -> dict:
    """Return one HRA claim with status and, when denied, the human-readable denial reason."""
    return benefits_data.get_claim_status(claim_id.strip().upper())


def list_eligible_expenses(sponsor_id: Annotated[str, Field(description="Sponsor id such as SP-NORTHWIND")]) -> list[str]:
    """List the expense types a sponsor's HRA reimburses (premium, out_of_pocket, part_b_premium, ...)."""
    return benefits_data.list_eligible_expenses(sponsor_id.strip().upper())


_WORD = re.compile(r"[a-z0-9]+")


def search_knowledge(
    query: Annotated[str, Field(description="What to look up, in plain words, for example 'accepted proof of payment'")],
    context: Annotated[Literal["marketplace", "accounts", "universal"], Field(description="Which knowledge context to search")] = "universal",
) -> dict:
    """Search the Benefits Marketplace knowledge base (Markdown docs) and return the best matching sections with their
    doc ids. Cite the doc id in brackets, for example [KB-ACC-001], after any statement taken from it."""
    terms = set(_WORD.findall(query.lower()))
    docs = benefits_data.list_knowledge_docs(context) + (benefits_data.list_knowledge_docs("universal") if context != "universal" else [])
    hits = []
    for doc in docs:
        text = benefits_data.read_knowledge_doc(doc["doc_id"])
        _, body = benefits_data.split_frontmatter(text)
        for section in re.split(r"\n(?=## )", body):
            words = set(_WORD.findall(section.lower()))
            score = len(terms & words)
            if score:
                hits.append({"doc_id": doc["doc_id"], "title": doc["title"], "score": score, "section": section.strip()[:1200]})
    hits.sort(key=lambda h: -h["score"])
    if not hits:
        return {"results": [], "note": "The knowledge base does not cover this question. Say so to the participant."}
    return {"results": hits[:3]}


def as_tools(functions: list) -> list:
    """Wrap plain functions with agent_framework.tool (import kept local so this module imports without it)."""
    from agent_framework import tool

    return [tool(approval_mode="never_require")(function) for function in functions]


def knowledge_tool():
    """Local search over data/knowledge by default; Lab 2's Foundry IQ MCP endpoint when BENEFITS_KB_MCP_URL is set."""
    if not KB_MCP_URL:
        return as_tools([search_knowledge])[0]
    import httpx
    from agent_framework import MCPStreamableHTTPTool
    from azure.identity import DefaultAzureCredential

    class EntraBearerAuth(httpx.Auth):
        """Fresh token per request for the knowledge base MCP endpoint (audience: Azure AI Search).
        In the container this is the hosted agent's managed identity: give it Search Index Data Reader."""

        def __init__(self):
            self.credential = DefaultAzureCredential()

        def auth_flow(self, request):
            token = self.credential.get_token("https://search.azure.com/.default").token
            request.headers["Authorization"] = f"Bearer {token}"
            yield request

    # VERIFY against https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/tools before delivery:
    # MCPStreamableHTTPTool(name=..., url=..., http_client=httpx.AsyncClient(auth=...)) (BRIEF-shared 5d shape).
    return MCPStreamableHTTPTool(name="benefits-kb", url=KB_MCP_URL, http_client=httpx.AsyncClient(auth=EntraBearerAuth(), timeout=60.0))


MARKETPLACE_TOOL_FUNCTIONS = [search_plans, compare_plans, get_enrollment_window]
ACCOUNTS_TOOL_FUNCTIONS = [get_hra_account, get_claim_status, list_eligible_expenses]


# ---------- instructions ----------
MARKETPLACE_INSTRUCTIONS = """
You are marketplace-guide, the plan education specialist of Benefits Marketplace, an individual health insurance marketplace.
- Start from the participant context in the case brief (county, Medicare status, current plan, priorities).
- Use search_plans with the participant's county and, when a prescription is named, drug_name, then
  compare_plans on the two to four most relevant plan ids. Present the comparison as a short table or list.
- Explain the enrollment window with get_enrollment_window and the plan types with search_knowledge.
- Frame everything against the participant's stated priorities, without steering. "Plan X lists atorvastatin
  on Tier 1" is fine. "Plan X is the better choice" is not.
- End with what a licensed benefit advisor can do next.
"""

ACCOUNTS_INSTRUCTIONS = """
You are accounts-assistant, the reimbursement account specialist of Benefits Marketplace.
- Use get_hra_account for balance, allocation, debit card status and the claim list; get_claim_status for one
  claim; list_eligible_expenses for what the sponsor reimburses; search_knowledge (context accounts) for the
  rules, the accepted proof-of-payment list and the denial reasons. Cite the doc id.
- When a claim is denied, state the reason in plain words, list what proof is accepted, and offer to flag the
  claim for resubmission. Never promise that a resubmission will be paid.
- Repeat only the data needed to answer. Never read back full account or card numbers.
"""

REVIEWER_INSTRUCTIONS = """
You are compliance-reviewer for Benefits Marketplace. You read a draft written by other agents for a participant and
check it against the compliance rules below. You do not answer the participant.
Return a ReviewVerdict. Mark compliant=false when the draft: recommends or ranks plans, tells the participant
which plan to choose or enroll in, gives medical advice, guarantees coverage or cost, asks for or repeats a
full SSN, Medicare number or card number, or states knowledge-base facts without a [KB-...] citation.
Name the offending section (marketplace-guide or accounts-assistant) and give one paragraph of rewrite guidance.
"""

HANDOFF_INSTRUCTIONS = """
You are advisor-handoff for Benefits Marketplace. You write the case packet a licensed benefit advisor reads before
calling the participant back. You do not talk to the participant.
Build a HandoffPacket from the case brief, the specialist sections and the compliance flags you are given.
- facts_gathered: one entry per fact, each with its source (tool name or [KB-...] doc id).
- options_discussed: neutral descriptions only. If the drafts contain a recommendation, do not carry it over;
  add a compliance flag instead.
- open_questions: what the advisor still needs to ask, including any request for a recommendation the
  participant made (only the advisor may answer it).
- Use the created_at timestamp given in the prompt verbatim.
- When you receive advisor feedback on a previous packet, apply it and return the full HandoffPacket again.
"""


def with_compliance(role_text: str) -> str:
    """Role text plus the shared compliance block. Every agent in every lab appends this block."""
    return role_text.strip() + "\n\n" + guardrails.COMPLIANCE_INSTRUCTIONS


# ---------- builders ----------
def build_marketplace_guide(client, kb_tool=None, *, name: str = "marketplace-guide"):
    from agent_framework import Agent

    tools = as_tools(MARKETPLACE_TOOL_FUNCTIONS) + [kb_tool or knowledge_tool()]
    return Agent(client=client, name=name, instructions=with_compliance(MARKETPLACE_INSTRUCTIONS), tools=tools,
                 default_options={"store": False})


def build_accounts_assistant(client, kb_tool=None, *, name: str = "accounts-assistant"):
    from agent_framework import Agent

    tools = as_tools(ACCOUNTS_TOOL_FUNCTIONS) + [kb_tool or knowledge_tool()]
    return Agent(client=client, name=name, instructions=with_compliance(ACCOUNTS_INSTRUCTIONS), tools=tools,
                 default_options={"store": False})


def build_compliance_reviewer(client, *, name: str = "compliance-reviewer"):
    from agent_framework import Agent

    return Agent(client=client, name=name, instructions=with_compliance(REVIEWER_INSTRUCTIONS),
                 default_options={"response_format": ReviewVerdict, "store": False})


def build_advisor_handoff(client, *, name: str = "advisor-handoff"):
    from agent_framework import Agent

    return Agent(client=client, name=name, instructions=with_compliance(HANDOFF_INSTRUCTIONS),
                 default_options={"response_format": HandoffPacket, "store": False})


def build_all(client) -> dict:
    kb = knowledge_tool()
    return {"marketplace-guide": build_marketplace_guide(client, kb), "accounts-assistant": build_accounts_assistant(client, kb),
            "compliance-reviewer": build_compliance_reviewer(client), "advisor-handoff": build_advisor_handoff(client)}


def parse_structured(response_text: str, text_value, model_cls):
    """Structured output arrives as parsed .value on the response when the client supports it, otherwise as
    JSON text. Returns a model instance or None when neither parses."""
    if isinstance(text_value, model_cls):
        return text_value
    if isinstance(text_value, dict):
        try:
            return model_cls.model_validate(text_value)
        except Exception:  # noqa: BLE001  (fall through to the text)
            pass
    text = (response_text or "").strip()
    for candidate in (text, text[text.find("{"): text.rfind("}") + 1]):
        if candidate.startswith("{"):
            try:
                return model_cls.model_validate_json(candidate)
            except Exception:  # noqa: BLE001
                continue
    return None


if __name__ == "__main__":
    # No-model smoke test of the pure parts: knowledge search and the tool functions.
    hit = search_knowledge("accepted proof of payment denied claim", "accounts")
    print(f"[benefits-specialists] search_knowledge -> {[r['doc_id'] for r in hit['results']]}")
    assert hit["results"] and hit["results"][0]["doc_id"] == "KB-ACC-001", hit
    print(f"[benefits-specialists] get_claim_status(CLM-9003) -> {get_claim_status('CLM-9003')['status']}")
    print(f"[benefits-specialists] search_plans(Salt Lake, atorvastatin) -> {len(search_plans('Salt Lake', drug_name='atorvastatin'))} plans")
    print("[benefits-specialists] PASS")
