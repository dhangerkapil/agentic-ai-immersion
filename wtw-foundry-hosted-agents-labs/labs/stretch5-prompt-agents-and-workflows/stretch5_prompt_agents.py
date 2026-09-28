# %% [markdown]
# # Stretch 5: Prompt agents and a declarative workflow (platform-managed), called from the hosted agent
#
# **Where this runs.** This notebook runs on your workstation. Everything it creates runs inside the Foundry
# project: prompt agents (`PromptAgentDefinition`) and the workflow agent (`WorkflowAgentDefinition`, preview).
# No container is built here. The last cell shows how the **hosted** agent from Lab 2 gets a `run_triage_workflow`
# tool that calls the workflow agent with `responses.create(..., agent_reference=...)`: see `hosted_tool_snippet.py`.
#
# **Checkpoint artifact.** `artifacts/stretch5/agents.json` (every agent name and version, the workflow agent,
# the S1 handoff packet path) and `artifacts/stretch5/handoff_packets/S1.json`.
"""Stretch 5: Prompt agents (platform-managed) and the declarative triage workflow, condensed from the former Labs 1 and 3.

Goal:    Create via-concierge (FunctionTools), the four specialists (triage twin, marketplace-guide with the knowledge
         MCP tool, accounts-assistant, compliance-reviewer, advisor-handoff) and the via-triage-workflow agent from
         via_triage_workflow.yaml. Run S1 through the workflow with streaming and save the handoff packet. Then read
         hosted_tool_snippet.py: the hosted agent delegates to this workflow with one @tool.
Inputs:  artifacts/lab2/knowledge.json (knowledge base MCP endpoint + project connection)
Outputs: artifacts/stretch5/agents.json, artifacts/stretch5/workflow.yaml, artifacts/stretch5/handoff_packets/S1.json
Time:    60 min (teach 10, demo 10, do 35, checkpoint 5); build takes about 1 min, the S1 run 1 to 2 min

Run:     python stretch5_prompt_agents.py [--build-only] [--demo-only] [--concierge-turn]
"""
# %% Imports and environment
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # wtw-foundry-hosted-agents-labs/ (common/ and data/ live here)
sys.path.insert(0, str(ROOT))
from common import via_data, foundry_env, guardrails  # noqa: E402

LABS_DIR = Path(__file__).resolve().parents[1]  # labs/ (lab_helpers.py, catch_up.py, artifacts/)
sys.path.insert(0, str(LABS_DIR))
import lab_helpers as helpers  # noqa: E402

import yaml  # noqa: E402
from azure.ai.projects.models import MCPTool, PromptAgentDefinition, WorkflowAgentDefinition  # noqa: E402

ENV = foundry_env.load_env()
MODEL = helpers.pick_model(ENV)
LAB = "stretch5"
HERE = Path(__file__).resolve().parent
WORKFLOW_TEMPLATE = HERE / "via_triage_workflow.yaml"
CONCIERGE, TRIAGE, MARKETPLACE = "via-concierge", "via-concierge-triage", "marketplace-guide"
ACCOUNTS, COMPLIANCE, HANDOFF, WORKFLOW = "accounts-assistant", "compliance-reviewer", "advisor-handoff", "via-triage-workflow"
PACKET_FIELDS = ["case_id", "participant_id", "lob", "summary", "participant_goals", "facts_gathered", "options_discussed",
                 "open_questions", "recommended_next_step_for_advisor", "compliance_flags", "created_at"]

# %% Instructions. Every agent ends with guardrails.COMPLIANCE_INSTRUCTIONS. Specialists carry TRIAGE MODE because
# a workflow runs on the platform with nobody there to answer a client-side function_call: the caller pre-fetches
# the facts into the TRIAGE CASE header and the agents work from those plus the knowledge base (server-side MCP).
TRIAGE_MODE = """
TRIAGE MODE
- A message starting with "TRIAGE CASE" comes from the triage workflow, not a participant. Facts from systems of
  record are included; do not call function tools unless a fact is missing. Write for the participant, second person.
"""
INSTRUCTIONS = {
    CONCIERGE: """You are "Via Concierge", the front door for Via Benefits, WTW's Individual Marketplace.
- Confirm identity with participant_id and ZIP code only, then look the participant up with get_participant.
- Enrollment timing: get_enrollment_window (window name, dates, what it allows). Account basics: get_hra_account.
- Plan comparisons are done by a Marketplace specialist; you have no plan tool, say so and offer to connect them.
- Recommendation, enrollment or judgment call: offer a licensed benefit advisor handoff.
- Call a tool before stating any fact. Under 120 words. End with one next step.

""",
    TRIAGE: """You are "Via Concierge" in triage mode. You receive one TRIAGE CASE (participant words + verified facts).
You have no tools and never invent facts. Reply in exactly this shape:
ROUTE: marketplace | accounts | both
INTENT: one sentence.
PARTICIPANT_GOALS:
- one per line
NEEDS_ADVISOR: yes | no, followed by the reason
CASE:
(copy the TRIAGE CASE below this line unchanged)
Routing: marketplace = plans, premiums, formularies, networks, enrollment periods, ACA, turning 65; accounts = HRA,
claims, denials, proof of payment, debit card, auto-reimbursement; both when the case touches both or when unsure.
Never answer the participant yourself.

""",
    MARKETPLACE: """You are "Marketplace Guide" for Via Benefits. You educate about Medicare Advantage, Medigap, Part D and ACA
plans and compare them neutrally.
- knowledge_base_retrieve (server side): call it FIRST for how plans, enrollment periods, subsidies or comparisons
  work; cite the doc id, for example [KB-MKT-002].
- search_plans / compare_plans / get_enrollment_window when facts are missing from the case.
- Comparisons: compact table (plan, carrier, type, premium, deductible, max out of pocket, stars, network, drug
  coverage, named drug tier), then neutral trade-offs. Never rank, never "best". Doctor networks: the participant
  must confirm with the carrier or an advisor.
- In TRIAGE MODE reply exactly NO_MARKETPLACE_QUESTION when the case has no marketplace part.
""" + TRIAGE_MODE,
    ACCOUNTS: """You are "Accounts Assistant" for Via Benefits: HRA balance, claim status, denial reasons, accepted proof of
payment, debit card, premium auto-reimbursement.
- knowledge_base_retrieve FIRST for rules and documents; cite [KB-ACC-001] style doc ids.
- get_hra_account, get_claim_status, list_eligible_expenses when facts are missing from the case.
- Denied claim: reason in plain words, the exact document that fixes it, offer to flag for resubmission.
- Quote numbers from tools or case facts only. Card: last 4 digits at most. Plan choice questions go to the
  Marketplace specialist or a licensed advisor. Under 150 words, one next step.
- In TRIAGE MODE reply exactly NO_ACCOUNTS_QUESTION when the case has no accounts part.
""" + TRIAGE_MODE,
    COMPLIANCE: """You are "Compliance Reviewer" for Via Benefits. You review drafts (MARKETPLACE DRAFT, ACCOUNTS DRAFT) in a
COMPLIANCE REVIEW REQUEST against the COMPLIANCE RULES and the case facts. Ignore drafts that read NO_*_QUESTION.
Check: rule 1 recommendation or ranking; rule 2 missing advisor handoff when asked to choose or enroll; rule 3 PII;
rules 4 and 5 uncited or unsupported facts; rule 6 medical advice, guarantees, "doctor is in network".
Reply exactly:
COMPLIANCE REVIEW
verdict: pass | revise
flags:
- rule <n>: <what and where>   (or "- none")
revised_reply:
<one merged participant-facing reply with every flagged sentence fixed, citations kept>

""",
    HANDOFF: """You are "Advisor Handoff" for Via Benefits. From a BUILD HANDOFF PACKET message (triage summary, case facts,
drafts, COMPLIANCE REVIEW) write ONE JSON object and nothing else, no fences. Fields, all required:
case_id, participant_id, lob (marketplace|accounts|both), summary (2-4 sentences), participant_goals [str],
facts_gathered [{"fact","source"}] (source = tool name, KB doc id or "participant statement"), options_discussed [str]
(neutral, never a preference), open_questions [str], recommended_next_step_for_advisor (a process step, never a
plan choice), compliance_flags [str] (copy from the review, [] when none), created_at (ISO 8601 UTC).
Never include a date of birth, SSN, Medicare number or card number. Use only facts present in the input.

""",
}
SPECS = {                                        # agent -> (function tools, uses the knowledge MCP tool)
    CONCIERGE: (["get_participant", "get_enrollment_window", "get_hra_account"], False),
    TRIAGE: ([], False),
    MARKETPLACE: (["search_plans", "compare_plans", "get_enrollment_window"], True),
    ACCOUNTS: (["get_hra_account", "get_claim_status", "list_eligible_expenses"], True),
    COMPLIANCE: ([], False),
    HANDOFF: ([], False),
}


def knowledge_tool(knowledge: dict) -> MCPTool:
    connection_id = (knowledge.get("connection") or {}).get("connection_id")
    if not knowledge.get("mcp_endpoint") or not connection_id:
        raise SystemExit("[stretch5] artifacts/lab2/knowledge.json has no mcp_endpoint or connection. Run: python catch_up.py --through 2")
    # VERIFY before delivery: project_connection_id takes the connection resource id (else pass connection_name).
    return MCPTool(server_label="via-kb", server_url=knowledge["mcp_endpoint"], require_approval="never",
                   project_connection_id=connection_id)


def render_workflow() -> str:
    text = WORKFLOW_TEMPLATE.read_text(encoding="utf-8").format(triage=TRIAGE, marketplace=MARKETPLACE, accounts=ACCOUNTS,
                                                                 compliance=COMPLIANCE, handoff=HANDOFF)
    parsed = yaml.safe_load(text)                # fail here, locally, not at create_version
    assert parsed["kind"] == "workflow" and parsed["trigger"]["kind"] == "OnConversationStart"
    return text


# %% build(): six prompt agent versions + the workflow agent version, then the checkpoint artifact
def build(project=None, overrides: dict[str, str] | None = None) -> dict:
    knowledge = helpers.require_artifact("lab2", "knowledge.json", through=2, caller="stretch5")
    project = project or foundry_env.get_project_client()
    agents = {}
    for name, (tool_names, uses_kb) in SPECS.items():
        instructions = (overrides or {}).get(name) or INSTRUCTIONS[name] + guardrails.COMPLIANCE_INSTRUCTIONS
        assert instructions.endswith(guardrails.COMPLIANCE_INSTRUCTIONS), "every agent carries the compliance block"
        tools = helpers.function_tools(tool_names) + ([knowledge_tool(knowledge)] if uses_kb else [])
        agent = project.agents.create_version(agent_name=name, definition=PromptAgentDefinition(model=MODEL, instructions=instructions, tools=tools))
        agents[name] = {"agent_version": agent.version, "agent_id": agent.id, "function_tools": tool_names, "knowledge": uses_kb}
        print(f"[stretch5] created prompt agent {name} v{agent.version} (tools: {', '.join(tool_names) or 'none'}{', via-kb' if uses_kb else ''})")
    text = render_workflow()
    workflow = project.agents.create_version(agent_name=WORKFLOW, definition=WorkflowAgentDefinition(workflow=text))
    helpers.artifact_path(LAB, "workflow.yaml").write_text(text, encoding="utf-8")
    print(f"[stretch5] created workflow agent {WORKFLOW} v{workflow.version} (preview)")
    info = {"lab": LAB, "model": MODEL, "agents": agents, "workflow_name": workflow.name, "workflow_version": workflow.version,
            "workflow_id": workflow.id, "knowledge_base": knowledge.get("kb_name"), "packet_fields": PACKET_FIELDS,
            "hosted_tool": "hosted_tool_snippet.run_triage_workflow reads workflow_name from this file", "created_at": helpers.now_iso()}
    path = helpers.artifact_path(LAB, "agents.json")
    foundry_env.save_artifact(path, info)
    print(f"[stretch5] saved {path.relative_to(LABS_DIR)}; portal: Agents shows {len(agents)} prompt agents + the workflow graph")
    return info


# %% The case header: facts from systems of record, gathered by the caller (the workflow has no client tools)
def gather_facts(participant_id: str, claim_ids: list[str] | None = None) -> dict:
    participant = dict(via_data.get_participant(participant_id))
    for hidden in ("dob", "contact_preference"):
        participant.pop(hidden, None)
    prescriptions = (participant.get("preferences") or {}).get("prescriptions") or []
    drug = prescriptions[0].split()[0] if prescriptions else None
    plan_types = ("Medicare Advantage HMO", "Medicare Advantage PPO", "Part D") if participant.get("medicare_eligible") \
        else ("ACA Bronze", "ACA Silver", "ACA Gold")
    candidates = []
    for plan_type in plan_types:                 # two per type so a $0 HMO does not crowd out the PPOs
        candidates += via_data.search_plans(participant.get("county", ""), participant.get("state", "UT"), plan_type=plan_type, drug_name=drug)[:2]
    ids = [p["plan_id"] for p in candidates]
    if participant.get("current_plan_id") and participant["current_plan_id"] not in ids:
        ids.insert(0, participant["current_plan_id"])
    keep = ["plan_id", "carrier", "plan_name", "plan_type", "premium_monthly", "deductible_annual", "max_out_of_pocket",
            "star_rating", "network_type", "drug_coverage", "formulary_tier_examples"]
    return {"participant": participant, "sponsor": via_data.get_sponsor(participant.get("sponsor_id", "")),
            "enrollment_window": via_data.get_enrollment_window(participant_id, today=ENV.get("VIA_TODAY")),
            "hra_account": via_data.get_hra_account(participant_id), "claims": [via_data.get_claim_status(c) for c in (claim_ids or [])],
            "plan_candidates": [{k: p[k] for k in keep if k in p} for p in via_data.compare_plans(ids).get("plans", [])],
            "note": "doctor networks are NOT in the data"}


def case_header(scenario: dict) -> tuple[str, str]:
    case_id = f"{scenario['id']}-{helpers.now_iso()[:10].replace('-', '')}-{scenario['participant_id']}"
    header = "\n".join([f"TRIAGE CASE {case_id}", f"case_id: {case_id}", f"participant_id: {scenario['participant_id']}", "channel: chat",
                        f"participant_message: \"{scenario['message']}\"", "facts (systems of record, verified by the caller):",
                        json.dumps(gather_facts(scenario["participant_id"], scenario.get("claim_ids")), default=str)])
    return case_id, header


# %% Running a case with streaming: workflow_action events show the path the case took
def run_case(openai_client, workflow_name: str, header: str) -> dict:
    conversation = openai_client.conversations.create()
    stream = openai_client.responses.create(input=header, conversation=conversation.id, stream=True, extra_body=helpers.agent_reference(workflow_name))
    actions, messages, errors = [], [], []
    for event in stream:
        if event.type in ("response.output_item.added", "response.output_item.done"):
            item = event.item
            data = item.model_dump() if hasattr(item, "model_dump") else {}
            if item.type == "workflow_action":
                actions.append({k: data[k] for k in ("action_id", "kind", "status", "agent_name") if data.get(k) is not None})
                print(f"[stretch5]   workflow_action {actions[-1]}")
            elif item.type == "message" and event.type.endswith("done"):
                messages.append("".join(getattr(p, "text", "") or "" for p in (getattr(item, "content", None) or [])))
                print(f"[stretch5]   message {len(messages)}: {messages[-1][:120].replace(chr(10), ' ')}")
            elif item.type == "function_call":
                errors.append(f"unanswered function_call {getattr(item, 'name', '?')} (client tools cannot run in a workflow)")
        elif event.type in ("response.failed", "error"):
            errors.append(str(event)[:300])
    try:
        openai_client.conversations.delete(conversation_id=conversation.id)
    except Exception:                            # noqa: BLE001  (the runtime may already have closed it)
        pass
    return {"conversation_id": conversation.id, "actions": actions, "messages": messages, "errors": errors}


def extract_packet(messages: list[str]) -> dict | None:
    for text in reversed(messages):
        candidate = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        for attempt in (candidate, candidate[candidate.find("{"): candidate.rfind("}") + 1]):
            try:
                packet = json.loads(attempt)
            except (ValueError, TypeError):
                continue
            if isinstance(packet, dict) and "participant_id" in packet:
                return packet
    return None


def validate_packet(packet: dict) -> list[str]:
    problems = [f"missing field {f}" for f in PACKET_FIELDS if f not in packet]
    if packet.get("lob") not in ("marketplace", "accounts", "both"):
        problems.append(f"lob must be marketplace|accounts|both, got {packet.get('lob')!r}")
    text = json.dumps(packet)
    if guardrails.redact_pii(text) != text:
        problems.append("PII pattern found in packet")
    if guardrails.contains_recommendation(" ".join(str(packet.get(f, "")) for f in ("summary", "options_discussed", "recommended_next_step_for_advisor"))):
        problems.append("recommendation wording found in packet")
    return problems


# %% demo(): S1 through the workflow, plus one concierge turn to show a plain prompt agent with function tools
S1 = {"id": "S1", "title": "AEP shopper", "participant_id": "P-1001",
      "message": "I am on the Contoso Advantage Choice HMO. Is there a plan with a lower cost for my atorvastatin where I could keep "
                 "my cardiologist, Dr. Osei? And when am I allowed to switch?"}


def demo(info: dict | None = None, concierge_turn: bool = False) -> dict:
    info = info or helpers.require_artifact(LAB, "agents.json", through=5, caller="stretch5")
    openai_client = foundry_env.get_openai_client()
    if concierge_turn:                           # the Lab-1 style loop: platform runs the model, we run the tools
        conversation = openai_client.conversations.create()
        text, calls = helpers.run_turn(openai_client, CONCIERGE, conversation.id,
                                       helpers.identity_line("P-1001") + " When can I change my Medicare plan?", log_prefix="[stretch5]")
        print(f"[stretch5] {CONCIERGE}> {text[:300]}\n[stretch5] checks: {helpers.fmt_checks(helpers.guardrail_report(text))}")
    case_id, header = case_header(S1)
    print(f"[stretch5] S1 {S1['title']} ({S1['participant_id']}) case {case_id} -> {info['workflow_name']} v{info['workflow_version']}")
    run = run_case(openai_client, info["workflow_name"], header)
    packet = extract_packet(run["messages"])
    problems = ["no JSON packet found"] if packet is None else validate_packet(packet)
    if packet is not None:
        packet.setdefault("created_at", helpers.now_iso())
        path = helpers.artifact_path(LAB, "handoff_packets", "S1.json")
        foundry_env.save_artifact(path, packet)
        print(f"[stretch5] saved {path.relative_to(LABS_DIR)} (lob={packet.get('lob')}, flags={len(packet.get('compliance_flags') or [])})")
    print(f"[stretch5] actions={len(run['actions'])} messages={len(run['messages'])} problems={problems or 'none'} errors={run['errors'] or 'none'}")
    print("[stretch5] portal: Agents > via-triage-workflow shows the graph; the conversation shows the actions in order")
    print("[stretch5] next: read hosted_tool_snippet.py, the @tool that lets the hosted agent call this workflow")
    info["last_run"] = {"case_id": case_id, "conversation_id": run["conversation_id"], "packet_saved": packet is not None,
                        "problems": problems, "actions": len(run["actions"]), "finished_at": helpers.now_iso()}
    foundry_env.save_artifact(helpers.artifact_path(LAB, "agents.json"), info)
    return info


# %% YOUR TURN (5 min): change an instruction in the portal, not in code. Open Agents > via-concierge, edit the
# instructions (add "Always greet the participant by first name") and save: a new version appears. Rerun
# --demo-only --concierge-turn. agent_reference by name resolves to the latest version. That is the point of a
# platform-managed prompt agent: business owners change behaviour with governance, without a deployment.

# %% YOUR TURN (5 min): break the router on purpose. Rebuild only the triage agent with ROUTE forced to accounts and
# rerun S1: marketplace questions go unanswered and the packet's open_questions grows. Restore afterwards.
# Solution:
#   broken = INSTRUCTIONS[TRIAGE].replace("ROUTE: marketplace | accounts | both", "ROUTE: accounts (always)") + guardrails.COMPLIANCE_INSTRUCTIONS
#   project = foundry_env.get_project_client()
#   project.agents.create_version(agent_name=TRIAGE, definition=PromptAgentDefinition(model=MODEL, instructions=broken))
#   demo(); build()      # the second build restores every agent

# %% Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--demo-only", action="store_true", help="reuse artifacts/stretch5/agents.json")
    parser.add_argument("--concierge-turn", action="store_true", help="also run one function-call turn on via-concierge")
    args = parser.parse_args()
    if args.demo_only:
        demo(concierge_turn=args.concierge_turn)
    else:
        info = build()
        if not args.build_only:
            demo(info, concierge_turn=args.concierge_turn)
