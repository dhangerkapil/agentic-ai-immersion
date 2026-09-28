"""The Benefits Marketplace triage workflow graph (Lab 3, runs inside the hosted container).

  IntakeExecutor        classifies the case (marketplace | accounts | both) and fans out to the specialists
  marketplace-guide     AgentExecutor over the specialist agent
  accounts-assistant    AgentExecutor over the specialist agent
  SpecialistMerge       fan-in: waits until every expected specialist answered, sends the draft to review
  compliance-reviewer   AgentExecutor, structured ReviewVerdict
  ComplianceGate        reflection: if the reviewer or guardrails.contains_recommendation flags the draft,
                        sends it back to the offending specialist once; then forwards the draft
  AdvisorCoordinator    asks advisor-handoff for the HandoffPacket, then ctx.request_info for the human
                        decision: approve | revise: <note> | decline: <note>
  advisor-handoff       AgentExecutor, structured HandoffPacket

Verified shapes (BRIEF-shared 5d and the base repo notebooks workflows/5 and workflows/6):
    class X(Executor):  @handler async def h(self, msg: T, ctx: WorkflowContext[Out]) -> None
    await ctx.send_message(msg[, target_id="executor-id"]);  await ctx.yield_output(value)
    await ctx.request_info(request_data=Req(...), response_type=str)
    @response_handler async def r(self, original_request: Req, feedback: str, ctx: WorkflowContext[Out, YieldT])
    WorkflowBuilder(start_executor=e).add_edge(a, b).build()
    events = [e async for e in workflow.run(intake, stream=True)]; request_info events carry request_id + data;
    resume with workflow.run(responses={request_id: answer}, stream=True); an output event carries the packet.
Fan-out and fan-in are explicit add_edge calls plus a counting merge executor, so no builder beyond
WorkflowBuilder is used.

What changed from the terminal version (Option B lab3): the human decision no longer comes from input().
`start_case` runs until the workflow pauses at request_info and returns the pending packet; `resume_case`
feeds the advisor's next HTTP turn back in. main.py keeps the paused workflow per session and stores the packet
in common.session_store so a restarted container can still finish the case.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_framework import (
    AgentExecutor,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Executor,
    Message,
    WorkflowBuilder,
    WorkflowContext,
    handler,
    response_handler,
)

HERE = Path(__file__).resolve().parent
for folder in (HERE.parents[2] if len(HERE.parents) > 2 else HERE, HERE):     # repo root, then vendored copies
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
from common import guardrails, benefits_data  # noqa: E402
from benefits_specialists import HandoffPacket, ReviewVerdict, parse_structured  # noqa: E402

TAG = "[benefits-triage]"
MARKETPLACE = "marketplace-guide"
ACCOUNTS = "accounts-assistant"
REVIEWER = "compliance-reviewer"
HANDOFF = "advisor-handoff"
COORDINATOR = "advisor-coordinator"
SPECIALISTS_FOR_LOB = {"marketplace": [MARKETPLACE], "accounts": [ACCOUNTS], "both": [MARKETPLACE, ACCOUNTS]}
PROFILE_FIELDS = ("participant_id", "first_name", "age", "county", "state", "sponsor_id", "medicare_eligible",
                  "medicare_parts", "current_plan_id", "language", "contact_preference")

MARKETPLACE_TERMS = re.compile(
    r"\b(plans?|premiums?|drugs?|formulary|doctors?|cardiologist|network|medicare advantage|medigap|part d|aca|"
    r"compare|switch|enroll(ment)?|coverage|prescriptions?|turn(ing)? 65)\b", re.I)
ACCOUNTS_TERMS = re.compile(
    r"\b(hra|claims?|denied|reimburs\w*|balance|debit card|my card|card (is|was|got)|proof of payment|receipts?|subsidy)\b", re.I)


# ---------- messages that travel on the edges ----------
@dataclass
class CaseIntake:
    case_id: str
    participant_id: str
    scenario: str
    message: str


@dataclass
class ApprovedDraft:
    case_id: str
    lob: str
    text: str
    compliance_flags: list[str]
    revision: int


@dataclass
class AdvisorReviewRequest:
    case_id: str
    prompt: str
    packet: dict


@dataclass
class CaseState:
    """Per-run state shared by the custom executors (one workflow instance handles one case).
    Production note: keep this in ctx.set_shared_state so checkpoints capture it (see README)."""

    intake: CaseIntake | None = None
    lob: str = "both"
    participant: dict = field(default_factory=dict)
    expected: set[str] = field(default_factory=set)
    sections: dict[str, str] = field(default_factory=dict)
    revision: int = 0
    compliance_flags: list[str] = field(default_factory=list)
    packet_attempts: int = 0

    def reset(self, intake: CaseIntake, lob: str, participant: dict) -> None:
        self.intake, self.lob, self.participant = intake, lob, participant
        self.expected, self.sections, self.revision = set(SPECIALISTS_FOR_LOB[lob]), {}, 0
        self.compliance_flags, self.packet_attempts = [], 0


# ---------- pure helpers (unit-testable, no model) ----------
def minimized_profile(participant: dict) -> dict:
    """Only what the agents need. No date of birth, no ZIP, no account ids in the prompt (data minimization)."""
    profile = {key: participant.get(key) for key in PROFILE_FIELDS if key in participant}
    preferences = participant.get("preferences") or {}
    profile["stated_preferences"] = {key: preferences.get(key, []) for key in ("doctors", "prescriptions", "priorities")}
    return profile


def classify_lob(message: str, participant: dict | None = None) -> str:
    """Keyword classifier (word boundaries, so "my cardiologist" is not "my card"). YOUR TURN in
    lab3_hosted_multi_agent.py swaps it for a model-based one."""
    marketplace = MARKETPLACE_TERMS.search(message) is not None
    accounts = ACCOUNTS_TERMS.search(message) is not None
    if marketplace and accounts:
        return "both"
    if marketplace:
        return "marketplace"
    if accounts:
        return "accounts"
    fallback = (participant or {}).get("lob_relationship", "both")
    return fallback if fallback in SPECIALISTS_FOR_LOB else "both"


def render_case_brief(state: CaseState) -> str:
    intake = state.intake
    profile = state.participant if "error" in state.participant else minimized_profile(state.participant)
    lines = [f"CASE {intake.case_id} ({intake.scenario}), line of business: {state.lob}",
             "PARTICIPANT CONTEXT (from the profile; do not ask for these again)"]
    lines += [f"- {key}: {value}" for key, value in profile.items() if key != "stated_preferences"]
    for key, values in (profile.get("stated_preferences") or {}).items():
        if values:
            lines.append(f"- {key}: {', '.join(values)}")
    lines += ["", "PARTICIPANT SAID", intake.message, "",
              "Write your section of the reply. Only cover your line of business. Cite [KB-...] ids."]
    return "\n".join(lines)


def render_draft(state: CaseState) -> str:
    return "\n\n".join(f"### {name}\n{text.strip()}" for name, text in state.sections.items())


def render_review_prompt(draft: str) -> str:
    return "Review this draft reply to a participant and return your verdict.\n\nDRAFT\n" + draft


def render_revision_prompt(verdict: ReviewVerdict, draft: str) -> str:
    return ("compliance-reviewer flagged your section. Rewrite it so it follows every compliance rule.\n"
            f"Violations: {'; '.join(verdict.violations) or 'recommendation language detected'}\n"
            f"Guidance: {verdict.guidance}\n\nYOUR PREVIOUS SECTION\n{draft}")


def render_packet_prompt(state: CaseState, draft: ApprovedDraft, created_at: str) -> str:
    return (f"Write the HandoffPacket for case {draft.case_id}, participant {state.intake.participant_id}, lob {draft.lob}.\n"
            f"created_at: {created_at}\ncompliance_flags to carry over: {draft.compliance_flags or []}\n\n"
            f"CASE BRIEF\n{render_case_brief(state)}\n\nSPECIALIST SECTIONS (revision {draft.revision})\n{draft.text}")


def render_advisor_prompt(packet: dict) -> str:
    lines = [f"Handoff packet for case {packet.get('case_id')} ({packet.get('participant_id')}, lob {packet.get('lob')})",
             f"Summary: {packet.get('summary')}", "Options discussed:"]
    lines += [f"  - {item}" for item in packet.get("options_discussed", [])]
    lines += ["Open questions:"] + [f"  - {item}" for item in packet.get("open_questions", [])]
    lines += [f"Next step for you: {packet.get('recommended_next_step_for_advisor')}",
              f"Compliance flags: {packet.get('compliance_flags') or 'none'}",
              "Reply: approve | revise: <what to change> | decline: <reason>"]
    return "\n".join(lines)


def parse_decision(feedback: str) -> tuple[str, str]:
    decision, _, note = (feedback or "").strip().partition(":")
    decision = decision.strip().lower()
    if decision not in {"approve", "revise", "decline"}:
        decision = "revise"
        note = feedback
    return decision, note.strip()


def finalize_packet(packet: dict, decision: str, note: str, attempts: int | None = None) -> dict:
    """The final packet shape, shared by the workflow path and the restart fallback in main.py."""
    final = dict(packet)
    final["advisor_decision"] = decision
    final["advisor_note"] = note
    if attempts is not None:
        final["packet_attempts"] = attempts
    final["status"] = "approved" if decision == "approve" else "declined"
    final["decided_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return final


# ---------- executors ----------
class IntakeExecutor(Executor):
    def __init__(self, state: CaseState, id: str = "intake"):
        super().__init__(id=id)
        self.state = state

    @handler
    async def start(self, intake: CaseIntake, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        participant = benefits_data.get_participant(intake.participant_id)
        lob = classify_lob(intake.message, participant)
        self.state.reset(intake, lob, participant)
        brief = render_case_brief(self.state)
        print(f"{TAG} intake {intake.case_id}: lob={lob}, specialists={sorted(self.state.expected)}", flush=True)
        for target in SPECIALISTS_FOR_LOB[lob]:  # explicit fan-out: one request per in-scope specialist
            await ctx.send_message(AgentExecutorRequest(messages=[Message("user", text=brief)], should_respond=True), target_id=target)


class SpecialistMerge(Executor):
    def __init__(self, state: CaseState, id: str = "merge"):
        super().__init__(id=id)
        self.state = state

    @handler
    async def collect(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        # VERIFY against https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.agentexecutorresponse
        # that executor_id names the AgentExecutor that produced the response.
        who = getattr(response, "executor_id", None) or next(iter(self.state.expected))
        self.state.sections[who] = response.agent_response.text or ""
        waiting = self.state.expected - set(self.state.sections)
        print(f"{TAG} merge: got {who}" + (f", waiting for {sorted(waiting)}" if waiting else ", draft complete"), flush=True)
        if waiting:
            return
        await ctx.send_message(AgentExecutorRequest(messages=[Message("user", text=render_review_prompt(render_draft(self.state)))], should_respond=True))


class ComplianceGate(Executor):
    def __init__(self, state: CaseState, id: str = "compliance-gate"):
        super().__init__(id=id)
        self.state = state

    @handler
    async def decide(self, response: AgentExecutorResponse, ctx: WorkflowContext[AgentExecutorRequest | ApprovedDraft]) -> None:
        verdict = parse_structured(response.agent_response.text, getattr(response.agent_response, "value", None), ReviewVerdict)
        if verdict is None:
            verdict = ReviewVerdict(compliant=False, violations=["reviewer output could not be parsed"], offending_section="none", guidance="none")
        draft = render_draft(self.state)
        heuristic = guardrails.contains_recommendation(draft)
        flags = list(verdict.violations) + (["heuristic: contains_recommendation matched"] if heuristic else [])
        print(f"{TAG} compliance: compliant={verdict.compliant} heuristic_hit={heuristic} revision={self.state.revision}", flush=True)
        target = verdict.offending_section if verdict.offending_section in self.state.sections else next(iter(self.state.sections), None)
        if flags and self.state.revision == 0 and target:  # reflection: revise once
            self.state.revision += 1
            self.state.expected = {target}
            previous = self.state.sections.pop(target)
            print(f"{TAG} compliance: sending {target} back for one revision", flush=True)
            await ctx.send_message(AgentExecutorRequest(messages=[Message("user", text=render_revision_prompt(verdict, previous))], should_respond=True), target_id=target)
            return
        if flags:
            flags.append("unresolved after one revision: advisor must fix before any use")
        self.state.compliance_flags = flags
        await ctx.send_message(ApprovedDraft(self.state.intake.case_id, self.state.lob, draft, flags, self.state.revision), target_id=COORDINATOR)


class AdvisorCoordinator(Executor):
    def __init__(self, state: CaseState, id: str = COORDINATOR):
        super().__init__(id=id)
        self.state = state
        self.last_packet: dict | None = None

    @handler
    async def on_draft(self, draft: ApprovedDraft, ctx: WorkflowContext[AgentExecutorRequest]) -> None:
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        await ctx.send_message(AgentExecutorRequest(messages=[Message("user", text=render_packet_prompt(self.state, draft, created_at))], should_respond=True))

    @handler
    async def on_packet(self, response: AgentExecutorResponse, ctx: WorkflowContext) -> None:
        self.state.packet_attempts += 1
        packet = parse_structured(response.agent_response.text, getattr(response.agent_response, "value", None), HandoffPacket)
        if packet is None:
            packet = HandoffPacket(case_id=self.state.intake.case_id, participant_id=self.state.intake.participant_id, lob=self.state.lob,
                                   summary=response.agent_response.text or "", participant_goals=[], facts_gathered=[], options_discussed=[],
                                   open_questions=["packet did not parse as JSON; advisor to review the raw summary"],
                                   recommended_next_step_for_advisor="Review the raw summary.", compliance_flags=list(self.state.compliance_flags),
                                   created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        data = packet.model_dump(mode="json")
        data["compliance_flags"] = sorted(set(data.get("compliance_flags", [])) | set(self.state.compliance_flags))
        if guardrails.contains_recommendation(" ".join(data.get("options_discussed", []) + [data.get("summary", "")])):
            data["compliance_flags"].append("heuristic: packet text contains recommendation language")
        data["packet_attempts"] = self.state.packet_attempts
        self.last_packet = data
        await ctx.request_info(request_data=AdvisorReviewRequest(case_id=data["case_id"], prompt=render_advisor_prompt(data), packet=data), response_type=str)

    @response_handler
    async def on_advisor_decision(self, original_request: AdvisorReviewRequest, feedback: str, ctx: WorkflowContext[AgentExecutorRequest, dict]) -> None:
        decision, note = parse_decision(feedback)
        print(f"{TAG} advisor decision for {original_request.case_id}: {decision}" + (f" ({note})" if note else ""), flush=True)
        if decision in {"approve", "decline"}:
            await ctx.yield_output(finalize_packet(original_request.packet, decision, note, self.state.packet_attempts))
            return
        await ctx.send_message(AgentExecutorRequest(messages=[Message("user", text=f"Advisor feedback: {note or feedback}. "
                                                                       "Revise the packet and return the full HandoffPacket again.")], should_respond=True))


# ---------- graph ----------
def build_workflow(agents: dict[str, Any], *, checkpoint_dir: Path | None = None):
    """agents: {"marketplace-guide": Agent, "accounts-assistant": Agent, "compliance-reviewer": Agent, "advisor-handoff": Agent}.
    Returns (workflow, state). Build one per case: the CaseState is not shared between sessions."""
    state = CaseState()
    intake, merge, gate, coordinator = IntakeExecutor(state), SpecialistMerge(state), ComplianceGate(state), AdvisorCoordinator(state)
    # VERIFY against https://learn.microsoft.com/en-us/agent-framework/workflows/agents-in-workflows that AgentExecutor(agent, id=...)
    # is the explicit wrapper (passing the Agent to add_edge wraps it with id=agent.name).
    marketplace = AgentExecutor(agents[MARKETPLACE], id=MARKETPLACE)
    accounts = AgentExecutor(agents[ACCOUNTS], id=ACCOUNTS)
    reviewer = AgentExecutor(agents[REVIEWER], id=REVIEWER)
    handoff = AgentExecutor(agents[HANDOFF], id=HANDOFF)

    builder = (
        WorkflowBuilder(start_executor=intake)
        .add_edge(intake, marketplace).add_edge(intake, accounts)        # fan-out (target_id picks the in-scope ones)
        .add_edge(marketplace, merge).add_edge(accounts, merge)          # fan-in by counting in SpecialistMerge
        .add_edge(merge, reviewer).add_edge(reviewer, gate)              # compliance review
        .add_edge(gate, marketplace).add_edge(gate, accounts)            # one revision pass (reflection)
        .add_edge(gate, coordinator)                                     # approved draft
        .add_edge(coordinator, handoff).add_edge(handoff, coordinator)   # packet, then request_info to the human
    )
    if checkpoint_dir is not None:
        # VERIFY against https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints before delivery:
        # FileCheckpointStorage(storage_path=...) and WorkflowBuilder.with_checkpointing(checkpoint_storage=...);
        # resume with workflow.run(checkpoint_id=..., responses=..., stream=True).
        from agent_framework import FileCheckpointStorage

        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        builder = builder.with_checkpointing(checkpoint_storage=FileCheckpointStorage(storage_path=str(checkpoint_dir)))
    return builder.build(), state


# ---------- run until the human is needed, resume when the human answers ----------
@dataclass
class RunOutcome:
    """Either a pending advisor request (request_id + packet) or the final packet (output)."""

    pending_request_id: str | None = None
    pending: AdvisorReviewRequest | None = None
    output: dict | None = None
    events: int = 0


def _collect(events: list) -> RunOutcome:
    outcome = RunOutcome(events=len(events))
    for event in events:
        etype = getattr(event, "type", None)
        if etype == "request_info":
            outcome.pending_request_id, outcome.pending = event.request_id, event.data
        elif etype == "output":
            outcome.output = event.data
    if outcome.output is None and outcome.pending is None:
        raise RuntimeError(f"{TAG} workflow stopped with no output and no pending request ({len(events)} events)")
    return outcome


async def start_case(workflow, intake: CaseIntake) -> RunOutcome:
    """Run from intake until the coordinator asks the advisor (request_info) or, unusually, finishes."""
    events = [event async for event in workflow.run(intake, stream=True)]
    return _collect(events)


async def resume_case(workflow, request_id: str, feedback: str) -> RunOutcome:
    """Feed the advisor's answer back. approve/decline yields the final packet; revise pauses again."""
    events = [event async for event in workflow.run(responses={request_id: feedback}, stream=True)]
    return _collect(events)
