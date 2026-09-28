"""Lab 3: via-triage-hosted. A multi-agent workflow inside a Foundry Hosted Agent, with human approval across HTTP turns.

Goal:    one hosted agent (Responses protocol) that, on a participant turn, runs the Agent Framework workflow
         intake -> marketplace-guide + accounts-assistant (fan-out/fan-in) -> compliance-reviewer (revise once)
         -> advisor-handoff (Pydantic HandoffPacket), then PAUSES: the packet comes back to the caller with
         status pending_advisor_approval and is stored in common.session_store under the session id. The
         advisor's next turn ("approve", "revise: <text>", "decline: <reason>") resumes the paused workflow.
         This is how request_info-style human-in-the-loop works when the client is a web chat, not a terminal.
Inputs:  env FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME (or FOUNDRY_MODEL), optional VIA_REDIS_URL
         (session map shared across replicas), VIA_SESSION_DIR (file fallback), VIA_KB_MCP_URL (Lab 2 knowledge
         base; local search over data/knowledge otherwise), VIA_HOSTED_PORT. common/ and data/ vendored by prepare.py.
Outputs: HTTP server speaking the OpenAI Responses protocol (POST /responses) on port 8088.
Time:    15 min to read; the lab driver (../lab3_hosted_multi_agent.py) starts and stops it for you.

Turn protocol (the text of the Responses `input`):
    participant turn  {"session_id": "S1-...", "participant_id": "P-1001", "scenario": "S1", "message": "..."}
    advisor turn      {"session_id": "S1-...", "advisor": "approve"}      or plain text  approve | revise: ... | decline: ...
    reply             JSON: {"status": "pending_advisor_approval" | "approved" | "declined" | "no_pending_case" | "error", ...}
The session id inside the envelope is the same id the web chat uses for the Responses session, so the packet
can be found again by any replica.

Run:     python prepare.py && python main.py          then  python test_local.py  in another terminal
Deploy:  python ../lab3_hosted_multi_agent.py --deploy
"""
# %% Imports and path setup
from __future__ import annotations

import asyncio
import json
import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
for folder in (HERE.parents[2] if len(HERE.parents) > 2 else HERE, HERE):     # repo root, then vendored copies
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

warnings.simplefilter("ignore")

from common import guardrails, session_store  # noqa: E402

from agent_framework import Agent, AgentResponse, Message  # noqa: E402
from agent_framework.foundry import FoundryChatClient  # noqa: E402
from agent_framework_foundry_hosting import ResponsesHostServer  # noqa: E402
from azure.identity import DefaultAzureCredential  # noqa: E402

import via_specialists  # noqa: E402
from via_workflow import (  # noqa: E402
    TAG, AdvisorReviewRequest, CaseIntake, RunOutcome, build_workflow, finalize_packet, parse_decision,
    render_advisor_prompt, resume_case, start_case,
)

AGENT_NAME = "via-triage-hosted"
DEFAULT_MODEL = "gpt-5.4-mini"
ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.environ.get("FOUNDRY_MODEL") or DEFAULT_MODEL
SESSION_DIR = Path(os.environ.get("VIA_SESSION_DIR", str(HERE / "sessions")))
PENDING = "pending_advisor_approval"
NEXT_HINT = "Reply with approve | revise: <what to change> | decline: <reason>"


def log(message: str) -> None:
    print(f"{TAG} {message}", flush=True)


# %% Instructions for the outer agent (only used when a turn is not a case envelope or an advisor decision)
ROLE_INSTRUCTIONS = """You are via-triage-hosted, the Via Benefits triage service for licensed benefit advisors.
You do not answer participants directly. A case arrives as a JSON envelope with session_id, participant_id and
message; the workflow behind you runs the specialists, the compliance review and the handoff packet, and the
advisor approves, revises or declines it on the next turn. When someone sends you plain text that is not a
decision, explain the envelope format in three short lines and stop.

"""
INSTRUCTIONS = ROLE_INSTRUCTIONS + guardrails.COMPLIANCE_INSTRUCTIONS
assert INSTRUCTIONS.endswith(guardrails.COMPLIANCE_INSTRUCTIONS), "every agent carries the compliance block"


# %% Shared state: one client, four specialists, the session map, and the paused workflows of this replica
class TriageService:
    """Runs cases and resumes them. Paused workflows live in memory (per replica); the packet lives in the
    session store (shared). If this replica restarts, approve/decline still finish from the stored packet and
    revise re-runs advisor-handoff alone, so no case is lost."""

    def __init__(self, client):
        self.client = client
        self.agents = via_specialists.build_all(client)
        self.sessions = session_store.get_session_store(SESSION_DIR)
        self.paused: dict[str, tuple[object, str]] = {}          # session_id -> (workflow, request_id)
        log(f"specialists={sorted(self.agents)} sessions={session_store.describe(self.sessions)}")

    # ----- session records -----
    def record(self, session_id: str, participant_id: str | None = None) -> session_store.SessionRecord:
        rec = self.sessions.get(session_id) or session_store.SessionRecord.new(session_id, agent_name=AGENT_NAME, participant_id=participant_id)
        if participant_id and not rec.participant_id:
            rec.participant_id = participant_id
        return rec

    def store_pending(self, rec: session_store.SessionRecord, pending: AdvisorReviewRequest, request_id: str | None, source: str) -> dict:
        rec.notes.update({"status": PENDING, "case_id": pending.case_id, "packet": pending.packet, "request_id": request_id,
                          "advisor_prompt": pending.prompt, "resume_path": source})
        rec.notes.setdefault("decisions", [])
        self.sessions.put(rec.touch())
        return {"status": PENDING, "session_id": rec.session_id, "case_id": pending.case_id,
                "participant_id": pending.packet.get("participant_id"), "lob": pending.packet.get("lob"),
                "packet_attempts": pending.packet.get("packet_attempts"), "packet": pending.packet,
                "advisor_prompt": pending.prompt, "next": NEXT_HINT, "resume_path": source}

    def store_final(self, rec: session_store.SessionRecord, final: dict, source: str) -> dict:
        rec.notes.update({"status": final["status"], "packet": final, "request_id": None, "resume_path": source})
        rec.notes.setdefault("decisions", []).append({"decision": final["advisor_decision"], "note": final.get("advisor_note", ""),
                                                      "at": final.get("decided_at")})
        self.sessions.put(rec.touch())
        self.paused.pop(rec.session_id, None)
        return {"status": final["status"], "session_id": rec.session_id, "case_id": final.get("case_id"), "packet": final, "resume_path": source}

    # ----- turns -----
    async def start(self, session_id: str, participant_id: str, message: str, scenario: str = "case") -> dict:
        rec = self.record(session_id, participant_id)
        case_id = f"CASE-{scenario}-{session_id}"[:64]
        workflow, _state = build_workflow(self.agents)
        log(f"session {session_id}: starting case {case_id} for {participant_id}")
        outcome: RunOutcome = await start_case(workflow, CaseIntake(case_id, participant_id, scenario, message))
        if outcome.output is not None:                       # cannot normally happen: the coordinator always asks
            return self.store_final(rec, outcome.output, "workflow")
        self.paused[session_id] = (workflow, outcome.pending_request_id)
        return self.store_pending(rec, outcome.pending, outcome.pending_request_id, "workflow")

    async def decide(self, session_id: str, feedback: str) -> dict:
        rec = self.sessions.get(session_id)
        if rec is None or rec.notes.get("status") != PENDING or not rec.notes.get("packet"):
            return {"status": "no_pending_case", "session_id": session_id,
                    "hint": "Send a case envelope first: {\"session_id\": ..., \"participant_id\": ..., \"message\": ...}"}
        decision, note = parse_decision(feedback)
        rec.notes.setdefault("decisions", []).append({"decision": decision, "note": note, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        paused = self.paused.get(session_id)
        if paused and paused[1]:
            workflow, request_id = paused
            outcome = await resume_case(workflow, request_id, feedback)
            if outcome.output is not None:
                return self.store_final(rec, outcome.output, "workflow")
            self.paused[session_id] = (workflow, outcome.pending_request_id)
            return self.store_pending(rec, outcome.pending, outcome.pending_request_id, "workflow")
        # This replica does not hold the paused workflow (restart, scale-out, version roll): finish from the store.
        log(f"session {session_id}: no paused workflow here, resuming from the session store ({decision})")
        packet = rec.notes["packet"]
        if decision in {"approve", "decline"}:
            return self.store_final(rec, finalize_packet(packet, decision, note, packet.get("packet_attempts")), "session_store")
        revised = await self.revise_packet(packet, note or feedback)
        pending = AdvisorReviewRequest(case_id=revised["case_id"], prompt=render_advisor_prompt(revised), packet=revised)
        return self.store_pending(rec, pending, None, "session_store")

    async def revise_packet(self, packet: dict, note: str) -> dict:
        """advisor-handoff alone, given the previous packet and the advisor's note (no specialists re-run)."""
        prompt = (f"Advisor feedback: {note}. Revise the packet below and return the full HandoffPacket again.\n\n"
                  f"PREVIOUS PACKET\n{json.dumps({k: v for k, v in packet.items() if k not in {'advisor_decision', 'advisor_note'}}, indent=2)}")
        response = await self.agents["advisor-handoff"].run(prompt)
        parsed = via_specialists.parse_structured(response.text, getattr(response, "value", None), via_specialists.HandoffPacket)
        revised = parsed.model_dump(mode="json") if parsed else dict(packet)
        revised["compliance_flags"] = sorted(set(revised.get("compliance_flags", [])) | set(packet.get("compliance_flags", [])))
        if parsed is None:
            revised["compliance_flags"].append("revision did not parse; previous packet kept")
        revised["packet_attempts"] = int(packet.get("packet_attempts") or 1) + 1
        return revised


SERVICE: TriageService | None = None


# %% Turn parsing: envelope JSON, advisor decision, or something else
def parse_turn(text: str, session_hint: str | None) -> tuple[str, dict]:
    """Returns (kind, fields) with kind in {"case", "decision", "other"}."""
    raw = (text or "").strip()
    fields: dict = {}
    if raw.startswith("{"):
        try:
            fields = json.loads(raw)
        except ValueError:
            fields = {}
    session_id = fields.get("session_id") or session_hint
    if fields.get("message") and fields.get("participant_id") and session_id:
        return "case", {"session_id": session_id, "participant_id": fields["participant_id"], "message": fields["message"],
                        "scenario": fields.get("scenario", "case")}
    decision_text = (fields.get("advisor") if fields else raw) or ""
    if session_id and is_decision(decision_text):
        return "decision", {"session_id": session_id, "feedback": decision_text}
    return "other", {"session_id": session_id}


def is_decision(text: str) -> bool:
    return text.split(":", 1)[0].strip().lower() in {"approve", "revise", "decline"}


async def handle_turn(text: str, session_hint: str | None) -> dict | None:
    kind, fields = parse_turn(text, session_hint)
    if kind == "other":
        return None
    try:
        if kind == "case":
            return await SERVICE.start(fields["session_id"], fields["participant_id"], fields["message"], fields["scenario"])
        return await SERVICE.decide(fields["session_id"], fields["feedback"])
    except Exception as exc:  # noqa: BLE001  (the caller gets a structured error, the log gets the type)
        log(f"turn failed: {type(exc).__name__}: {str(exc)[:300]}")
        return {"status": "error", "session_id": fields.get("session_id"), "error": f"{type(exc).__name__}: {str(exc)[:300]}"}


# %% Agent middleware: every Responses turn goes through here before the outer model is called
async def triage_router(context, call_next) -> None:
    """Short-circuit the run with the workflow result; fall through to the outer agent for anything else."""
    # VERIFY against https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/middleware before delivery:
    # agent middleware signature (context, call_next), context.messages (list of Message), how the session id is
    # exposed (context.session.session_id) and that setting context.result without awaiting call_next() returns
    # that AgentResponse to the caller.
    last = context.messages[-1] if getattr(context, "messages", None) else None
    text = getattr(last, "text", "") or ""
    session = getattr(context, "session", None)
    session_hint = getattr(session, "session_id", None) if session is not None else None
    result = await handle_turn(text, session_hint)
    if result is None:
        await call_next()
        return
    context.result = AgentResponse(messages=[Message("assistant", text=json.dumps(result, default=str))])


# %% Build the hosted agent
def build_agent() -> Agent:
    global SERVICE
    if not ENDPOINT:
        sys.exit(f"{TAG} FOUNDRY_PROJECT_ENDPOINT is not set (locally: .env at the repo root; hosted: set by azd)")
    client = FoundryChatClient(project_endpoint=ENDPOINT, model=MODEL, credential=DefaultAzureCredential())
    SERVICE = TriageService(client)
    agent = Agent(client=client, name=AGENT_NAME, instructions=INSTRUCTIONS, middleware=[triage_router], default_options={"store": False})
    log(f"agent {AGENT_NAME}: model={MODEL} kb={'mcp ' + via_specialists.KB_MCP_URL if via_specialists.KB_MCP_URL else 'local data/knowledge'} "
        f"started={datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return agent


# %% YOUR TURN (10 min): make the reviewer earn its keep.
# In via_specialists.MARKETPLACE_INSTRUCTIONS add the line "Finish with the single plan you would pick." Restart and
# run S1. In the server log you should see compliant=False, "sending marketplace-guide back for one revision", and
# a clean second pass. Put the line back. The once-only limit is what keeps a bad prompt from spinning forever.

# %% Local shortcut without the HTTP server (used by test_local.py --direct): run one case end to end
async def run_case_direct(session_id: str, participant_id: str, message: str, decisions: list[str]) -> dict:
    if SERVICE is None:
        build_agent()
    result = await SERVICE.start(session_id, participant_id, message, "direct")
    for decision in decisions:
        if result.get("status") != PENDING:
            break
        result = await SERVICE.decide(session_id, decision)
    return result


def run_case_direct_sync(session_id: str, participant_id: str, message: str, decisions: list[str]) -> dict:
    return asyncio.run(run_case_direct(session_id, participant_id, message, decisions))


if __name__ == "__main__":
    server = ResponsesHostServer(build_agent())
    port = int(os.environ.get("VIA_HOSTED_PORT", "8088"))
    if port != 8088:
        server.run(port=port)                    # VERIFY: run(port=...) (same note as Lab 1)
    else:
        server.run()
