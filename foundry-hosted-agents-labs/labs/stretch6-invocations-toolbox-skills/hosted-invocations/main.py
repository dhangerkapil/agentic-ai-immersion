"""Stretch 6: benefits-claims-review-invocations. A Foundry Hosted Agent on the INVOCATIONS protocol.

Goal:    the second hosting protocol. Invocations is a single structured request -> structured response
         (no session, no streaming): the shape for batch jobs and API-to-API calls. This agent takes
         {"claim_ids": ["CLM-9003", ...]} and returns one review packet per claim: status, denial reason, the
         fix, the accepted proof-of-payment documents from KB-ACC-001, and a plain-language explanation the
         accounts team can paste into the denial follow-up. The facts come from claims_review.py (deterministic);
         the model adds the participant_explanation and nothing else.
Inputs:  env FOUNDRY_PROJECT_ENDPOINT (injected when hosted), AZURE_AI_MODEL_DEPLOYMENT_NAME (or FOUNDRY_MODEL),
         optional BENEFITS_HOSTED_PORT. common/ and data/ vendored by prepare.py.
Outputs: HTTP server speaking the Invocations protocol on port 8088.
Time:    10 min to read; the lab driver (../stretch6_invocations.py) starts and stops it for you.

Verified shape (base repo hosted-agents/benefits-review-invocations/main.py and hosted-agents/README.md):
    from agent_framework_foundry_hosting import InvocationsHostServer
    InvocationsHostServer(agent).run()
    request body is JSON: {"message": "..."}  (the server calls request.json(); a plain string gives HTTP 500)
Not verified (VERIFY tags below): the endpoint path, and the exact response envelope the server returns.

Run:     python prepare.py && python main.py          then  python test_local.py  in another terminal
Deploy:  python ../stretch6_invocations.py --deploy   (--protocol invocations)
"""
# %% Imports and path setup
from __future__ import annotations

import json
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

HERE = Path(__file__).resolve().parent
for folder in (HERE.parents[2] if len(HERE.parents) > 2 else HERE, HERE):     # repo root, then vendored copies
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

warnings.simplefilter("ignore")

from common import guardrails, benefits_data  # noqa: E402

from agent_framework import Agent, tool  # noqa: E402
from agent_framework.foundry import FoundryChatClient  # noqa: E402
from agent_framework_foundry_hosting import InvocationsHostServer  # noqa: E402
from azure.identity import DefaultAzureCredential  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from claims_review import KB_DOC_ID, hra_rules, review_claims  # noqa: E402,F401  (review_claims re-exported for tests)

AGENT_NAME = "benefits-claims-review-invocations"
DEFAULT_MODEL = "gpt-5.4-mini"
ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.environ.get("FOUNDRY_MODEL") or DEFAULT_MODEL


def log(message: str) -> None:
    print(f"[invocations] {message}", flush=True)


# %% Structured output: the batch the caller receives
class ClaimReview(BaseModel):
    claim_id: str
    participant_id: str = Field(description="Participant id, or empty when the claim was not found")
    status: str = Field(description="paid | pending | denied | not_found")
    review: str = Field(description="resubmit | no_fix | in_review | not_denied | not_found")
    denial_reason_code: str = Field(description="Reason code such as missing_proof_of_payment, or empty")
    fix_available: bool
    accepted_proof_of_payment: list[str] = Field(description="Copied verbatim from the review tool; empty unless the code is missing_proof_of_payment")
    resubmission_steps: list[str] = Field(description="Copied verbatim from the review tool")
    advisor_action_required: bool
    participant_explanation: str = Field(description="Two to four plain sentences for the participant, citing [KB-ACC-001]; no promise of payment; no account or card numbers")
    knowledge_ref: str


class ClaimReviewBatch(BaseModel):
    reviewed_at: str
    reviews: list[ClaimReview]


# %% The one tool: deterministic facts. The model must not invent any field it did not get from here.
@tool(approval_mode="never_require")
def review_denied_claims(claim_ids: Annotated[list[str], Field(description="Claim ids such as CLM-9003")]) -> list[dict]:
    """Return one review packet per claim from the systems of record and KB-ACC-001: status, denial reason and
    text, whether a fix exists, the accepted proof-of-payment documents, the resubmission steps."""
    return review_claims(claim_ids)


INSTRUCTIONS = f"""You are benefits-claims-review-invocations, a batch reviewer for the Benefits Marketplace accounts team.
The request is JSON with a claim_ids list. Call review_denied_claims exactly once with all of the ids, then return
a ClaimReviewBatch. Copy every factual field from the tool result unchanged (status, review, denial_reason_code,
fix_available, accepted_proof_of_payment, resubmission_steps, advisor_action_required, knowledge_ref). For a claim
the tool reports as an error, set status and review to not_found and explain that the id was not recognised.
Write participant_explanation yourself: two to four plain sentences, cite {KB_DOC_ID} in brackets, list the
accepted documents when the fix is a resubmission, never promise that a resubmission will be paid.

""" + guardrails.COMPLIANCE_INSTRUCTIONS
assert INSTRUCTIONS.endswith(guardrails.COMPLIANCE_INSTRUCTIONS), "every agent carries the compliance block"


# %% Request parsing helpers (also used by test_local.py to build the body)
def parse_request_text(text: str) -> list[str]:
    """Accept {"claim_ids": [...]}, a JSON list, or a comma separated string of ids."""
    raw = (text or "").strip()
    try:
        data = json.loads(raw)
    except ValueError:
        data = raw
    if isinstance(data, dict):
        data = data.get("claim_ids", [])
    if isinstance(data, str):
        data = [part for part in data.replace(";", ",").split(",")]
    return [str(item).strip().upper() for item in data if str(item).strip()]


def build_agent() -> Agent:
    if not ENDPOINT:
        sys.exit("[invocations] FOUNDRY_PROJECT_ENDPOINT is not set (locally: .env at the repo root; hosted: set by azd)")
    client = FoundryChatClient(project_endpoint=ENDPOINT, model=MODEL, credential=DefaultAzureCredential())
    agent = Agent(client=client, name=AGENT_NAME, instructions=INSTRUCTIONS, tools=[review_denied_claims],
                  default_options={"response_format": ClaimReviewBatch, "store": False})
    rules = hra_rules()
    log(f"agent {AGENT_NAME}: model={MODEL} protocol=invocations rules={rules['doc_id']} (reviewed {rules['last_reviewed']}) "
        f"started={datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return agent


# %% YOUR TURN (5 min): add a second review type. Give the tool an optional `include_pending: bool` parameter and,
# when true, add "expected_decision_by" (submitted + 5 business days) to pending claims. Batch jobs like this are
# where the Invocations protocol earns its place: no session, one request, one JSON answer.

if __name__ == "__main__":
    server = InvocationsHostServer(build_agent())
    port = int(os.environ.get("BENEFITS_HOSTED_PORT", "8088"))
    if port != 8088:
        # VERIFY against https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents before delivery: run(port=...)
        server.run(port=port)
    else:
        server.run()
