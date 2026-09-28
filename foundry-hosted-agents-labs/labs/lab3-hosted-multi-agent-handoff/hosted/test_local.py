"""Smoke test for benefits-triage-hosted (Lab 3).

    python test_local.py                         two turns against the local server: S2 case envelope, then approve
    python test_local.py --base http://host:8088 another local or tunneled host
    python test_local.py --direct                no HTTP: import main.py and run the case in-process (needs .env)
    python test_local.py --deployed              the version deployed with azd, by name from labs/artifacts/lab3/hosted.json
    python test_local.py --offline               no model, no server: checks the pure parts (classifier, decision parsing)
Exit code 0 when the packet came back pending, the approve turn finished it, no recommendation language and no PII
leaked; 1 otherwise. Lab 4's pipeline runs this after a deployment.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
for folder in (HERE.parents[2] if len(HERE.parents) > 2 else HERE, HERE):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
from common import guardrails  # noqa: E402

AGENT_NAME = "benefits-triage-hosted"
HOSTED_RECORD = HERE.parents[1] / "artifacts" / "lab3" / "hosted.json"
CASE = {"participant_id": "P-1003", "scenario": "S2",
        "message": "My claim CLM-9003 was denied and I do not understand why. What do I need to send to get it paid?"}


def output_text(payload: dict) -> str:
    if payload.get("output_text"):
        return payload["output_text"]
    parts = []
    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts)


def parse_reply(text: str) -> dict:
    text = (text or "").strip()
    for candidate in (text, text[text.find("{"): text.rfind("}") + 1]):
        try:
            return json.loads(candidate)
        except ValueError:
            continue
    return {"status": "unparsed", "raw": text}


def call_local(base: str, text: str, previous_response_id: str | None = None) -> tuple[dict, str | None]:
    import httpx

    # VERIFY: POST /responses body shape and previous_response_id handling (same note as Lab 1 test_local.py)
    body: dict = {"input": text, "stream": False}
    if previous_response_id:
        body["previous_response_id"] = previous_response_id
    response = httpx.post(f"{base.rstrip('/')}/responses", json=body, timeout=300.0)
    response.raise_for_status()
    payload = response.json()
    return parse_reply(output_text(payload)), payload.get("id")


def call_deployed(agent_name: str, text: str, previous_response_id: str | None = None) -> tuple[dict, str | None]:
    from common import foundry_env

    client = foundry_env.get_openai_client()
    kwargs = {"previous_response_id": previous_response_id} if previous_response_id else {}
    response = client.responses.create(input=text, extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}}, **kwargs)
    return parse_reply(response.output_text), getattr(response, "id", None)


def check_packet(packet: dict) -> bool:
    text = json.dumps(packet.get("options_discussed", [])) + " " + str(packet.get("summary", ""))
    recommends = guardrails.contains_recommendation(text)
    leaks = guardrails.redact_pii(json.dumps(packet)) != json.dumps(packet)
    print(f"[triage-test] recommendation in packet: {recommends}  pii leak: {leaks}  flags: {packet.get('compliance_flags')}")
    return not recommends and not leaks


def offline_checks() -> bool:
    from benefits_workflow import classify_lob, finalize_packet, parse_decision

    ok = classify_lob(CASE["message"]) == "accounts"
    ok = ok and classify_lob("Which ACA plan is in my county and what is my HRA balance?") == "both"
    ok = ok and parse_decision("revise: add the IEP dates") == ("revise", "add the IEP dates")
    ok = ok and parse_decision("APPROVE") == ("approve", "")
    ok = ok and finalize_packet({"case_id": "x"}, "decline", "duplicate")["status"] == "declined"
    print(f"[triage-test] offline checks: {'ok' if ok else 'FAIL'}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="http://localhost:8088")
    parser.add_argument("--deployed", action="store_true")
    parser.add_argument("--direct", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.offline:
        ok = offline_checks()
        print(f"[triage-test] {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    session_id = f"test-{uuid.uuid4().hex[:8]}"
    if args.direct:
        import main as hosted_main

        result = hosted_main.run_case_direct_sync(session_id, CASE["participant_id"], CASE["message"], ["approve"])
        ok = result.get("status") == "approved" and check_packet(result.get("packet", {}))
        print(f"[triage-test] direct result: {result.get('status')}\n[triage-test] {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1

    agent_name = AGENT_NAME
    if args.deployed and HOSTED_RECORD.exists():
        agent_name = json.loads(HOSTED_RECORD.read_text(encoding="utf-8")).get("agent_name", agent_name)
    call = (lambda text, prev=None: call_deployed(agent_name, text, prev)) if args.deployed else (lambda text, prev=None: call_local(args.base, text, prev))

    envelope = json.dumps({"session_id": session_id, **CASE})
    print(f"[triage-test] turn 1 (case)> {envelope}")
    reply, response_id = call(envelope)
    print(f"[triage-test] status={reply.get('status')} case={reply.get('case_id')} attempts={reply.get('packet_attempts')}")
    ok = reply.get("status") == "pending_advisor_approval" and check_packet(reply.get("packet", {}))

    decision = json.dumps({"session_id": session_id, "advisor": "approve"})
    print(f"[triage-test] turn 2 (advisor)> {decision}")
    reply, _ = call(decision, response_id)
    print(f"[triage-test] status={reply.get('status')} resume_path={reply.get('resume_path')}")
    ok = ok and reply.get("status") == "approved" and check_packet(reply.get("packet", {}))
    print(f"[triage-test] {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
