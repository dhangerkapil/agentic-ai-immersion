"""Stretch 5: the `run_triage_workflow` tool for the hosted agent.

Runs on: inside the hosted container (Lab 2 `hosted/main.py`) once you paste it there; this file is also importable
on the workstation for a quick check (`python hosted_tool_snippet.py`).

What it teaches: a hosted (code) agent and a platform-managed workflow agent are not rivals. The hosted agent owns
the participant conversation, session state and the custom Python; when a case needs the governed triage flow
(specialists, compliance review, advisor packet), it delegates with ONE Responses call bound by `agent_reference`
to the workflow agent Stretch 5 created. The workflow runs on the platform with its own versions and portal graph.

How to wire it into Lab 2 hosted/main.py:
    1. copy the block between the markers into main.py after the other @tool functions
    2. FUNCTION_TOOLS.append(run_triage_workflow)
    3. add to ROLE_INSTRUCTIONS: "When the participant accepts an advisor handoff, call run_triage_workflow with a
       short case summary (participant id, LOB, what was asked, facts already gathered)."
    4. give the container the workflow name: azd env set VIA_WORKFLOW_AGENT_NAME via-triage-workflow (or vendor
       artifacts/stretch5/agents.json next to main.py), azd up
The hosted agent's managed identity needs Azure AI User on the project to call the workflow agent.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Annotated

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from common import guardrails  # noqa: E402

try:
    from pydantic import Field
    from agent_framework import tool
except ImportError:                              # workstation check without agent_framework / pydantic installed
    def Field(**kwargs):                         # type: ignore[misc]  # noqa: N802
        return kwargs.get("description")

    def tool(**_kwargs):                         # type: ignore[misc]
        return lambda fn: fn

ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
AGENTS_FILE_CANDIDATES = (HERE / "agents.json", HERE.parents[0] / "artifacts" / "stretch5" / "agents.json")

# ---- paste from here into hosted/main.py -----------------------------------------------------------------------


def load_workflow_reference() -> dict | None:
    """Workflow agent name/version from env or artifacts/stretch5/agents.json. None when unavailable."""
    name = os.environ.get("VIA_WORKFLOW_AGENT_NAME")
    if name:
        return {"workflow_name": name, "workflow_version": os.environ.get("VIA_WORKFLOW_AGENT_VERSION")}
    for path in AGENTS_FILE_CANDIDATES:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                continue
            if data.get("workflow_name"):
                return {"workflow_name": data["workflow_name"], "workflow_version": data.get("workflow_version"), "source": str(path)}
    return None


WORKFLOW = load_workflow_reference()
_openai_client = None


def openai_client():
    """OpenAI client bound to the Foundry project, created on first use with the container's identity."""
    global _openai_client
    if _openai_client is None:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential

        project = AIProjectClient(endpoint=ENDPOINT, credential=DefaultAzureCredential(), allow_preview=True)
        _openai_client = project.get_openai_client()
    return _openai_client


def _extract_packet(text: str) -> dict | None:
    """The workflow ends with the advisor-handoff packet as JSON (sometimes fenced)."""
    candidate = text.strip().strip("`")
    for attempt in (candidate, candidate[candidate.find("{"): candidate.rfind("}") + 1]):
        try:
            packet = json.loads(attempt)
        except (ValueError, TypeError):
            continue
        if isinstance(packet, dict) and "participant_id" in packet:
            return packet
    return None


@tool(approval_mode="never_require")
def run_triage_workflow(case_text: Annotated[str, Field(description="Case summary for the advisor: participant id, LOB, what was asked, "
                                                                    "facts already gathered, what needs a licensed advisor")]) -> dict:
    """Send a case through the Via Benefits triage workflow (platform workflow agent) and return the advisor handoff packet."""
    if not WORKFLOW:
        return {"error": "The triage workflow agent is not available in this deployment. Run Stretch 5 so that "
                         "artifacts/stretch5/agents.json exists (or set VIA_WORKFLOW_AGENT_NAME), then redeploy.",
                "next_step": "Tell the participant a licensed benefit advisor will follow up and note the case details."}
    if not ENDPOINT:
        return {"error": "FOUNDRY_PROJECT_ENDPOINT is not set; cannot reach the workflow agent."}
    client = openai_client()
    conversation = client.conversations.create()
    try:
        # One Responses call, no streaming: agent_reference binds it to the server-side workflow agent by name
        # (latest version). The workflow does triage -> specialists -> compliance -> packet on the platform.
        response = client.responses.create(input=case_text, conversation=conversation.id,
                                           extra_body={"agent_reference": {"name": WORKFLOW["workflow_name"], "type": "agent_reference"}})
        text = response.output_text or ""
    except Exception as exc:                     # noqa: BLE001  (the model gets a plain explanation, not a stack trace)
        return {"error": f"workflow call failed: {type(exc).__name__}: {str(exc)[:200]}", "workflow": WORKFLOW["workflow_name"]}
    finally:
        try:
            client.conversations.delete(conversation_id=conversation.id)
        except Exception:                        # noqa: BLE001
            pass
    return {"workflow": WORKFLOW["workflow_name"], "workflow_version": WORKFLOW.get("workflow_version"),
            "conversation_id": conversation.id, "packet": _extract_packet(text), "output_text": guardrails.redact_pii(text)[:2000],
            "note": "Packet is for the licensed advisor; summarise it for the participant without repeating internal fields."}


# ---- paste until here --------------------------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"[stretch5] workflow reference: {WORKFLOW or 'not found (run stretch5_prompt_agents.py or set VIA_WORKFLOW_AGENT_NAME)'}")
    print("[stretch5] tool ready:", getattr(run_triage_workflow, "name", None) or run_triage_workflow.__name__)
    if WORKFLOW and ENDPOINT and "--call" in sys.argv:
        result = run_triage_workflow("TRIAGE CASE demo\nparticipant_id: P-1003\nparticipant_message: \"My claim CLM-9003 was denied, "
                                     "why and what do I send?\"\nfacts: claim CLM-9003 denied missing_proof_of_payment")
        print(json.dumps({k: v for k, v in result.items() if k != "output_text"}, indent=2, default=str)[:1500])
