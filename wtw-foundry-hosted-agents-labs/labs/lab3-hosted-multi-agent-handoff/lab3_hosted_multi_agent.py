"""Lab 3: Hosted multi-agent handoff. A workflow inside the container, human approval across HTTP turns.

Goal     Run the Via Benefits triage workflow (intake -> marketplace-guide + accounts-assistant -> compliance
         review -> advisor-handoff packet) inside a hosted agent, and approve, revise or decline the packet from
         the client on the NEXT turn. Run S1, S2, S3 locally against hosted/main.py, then deploy via-triage-hosted.
Inputs   labs/artifacts/lab2/hosted.json or knowledge.json (Lab 2; `--standalone` to skip), .env
Outputs  labs/artifacts/lab3/handoff_packets/S1.json S2.json S3.json (final packets, written by this client),
         labs/artifacts/lab3/hosted.json, labs/artifacts/lab3/hosted_local.log
Time     60 min (teach 10, demo 10, do 35, checkpoint 5)

Run top to bottom:   python lab3_hosted_multi_agent.py --auto-approve [--scenario S1|S2|S3|all]
                     python lab3_hosted_multi_agent.py                      (you are the advisor: type approve | revise: ... | decline: ...)
                     python lab3_hosted_multi_agent.py --auto-approve --restart-between-turns   (kill the server between turns)
                     python lab3_hosted_multi_agent.py --deploy
Run cell by cell:    open lab3_walkthrough.ipynb, or use the "# %%" cells in VS Code.
"""
# %% [markdown]
# # Lab 3: Hosted multi-agent handoff
#
# **Where this runs.** This notebook (workstation) vendors `common/` and `data/` into `hosted/`, starts
# `hosted/main.py` locally on port 8088 and plays two roles against it: the participant (turn 1, a case envelope)
# and the licensed advisor (turn 2+, `approve` / `revise: ...` / `decline: ...`). `hosted/main.py` is the product:
# inside it an Agent Framework `WorkflowBuilder` graph runs four specialist agents and pauses at `request_info`;
# Foundry runs that container once you `azd up`.
#
# **Checkpoint artifact.** `labs/artifacts/lab3/handoff_packets/S1.json`, `S2.json`, `S3.json` (final packets with
# `advisor_decision`) and `labs/artifacts/lab3/hosted.json`. Lab 4 evaluates and operates this agent.

# %% Imports and paths
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # wtw-foundry-hosted-agents-labs/
LABS_DIR = ROOT / "labs"
LAB_DIR = Path(__file__).resolve().parent
for folder in (ROOT, LABS_DIR):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
from common import foundry_env, guardrails, via_data  # noqa: E402

import lab_helpers  # noqa: E402

LAB = "lab3"
AGENT_NAME = "via-triage-hosted"
HOSTED_DIR = LAB_DIR / "hosted"
ARTIFACTS = lab_helpers.artifact_path(LAB)
PACKETS_DIR = ARTIFACTS / "handoff_packets"
HOSTED_RECORD = ARTIFACTS / "hosted.json"
SERVER_LOG = ARTIFACTS / "hosted_local.log"
PORT = int(os.environ.get("VIA_HOSTED_PORT", "8088"))
LOCAL_BASE = f"http://localhost:{PORT}"
PENDING = "pending_advisor_approval"


def log(message: str) -> None:
    print(f"[{LAB}] {message}", flush=True)


def require_previous_lab(standalone: bool = False) -> dict:
    """Lab 2 deployed via-concierge-hosted v2 with the knowledge base. Lab 3 reads its record for continuity."""
    for name in ("hosted.json", "knowledge.json"):
        path = lab_helpers.artifact_path("lab2", name)
        if path.exists():
            return foundry_env.load_artifact(path)
    if standalone:
        log("artifacts/lab2 missing; --standalone given, continuing with the local knowledge search")
        return {}
    return lab_helpers.require_artifact("lab2", "hosted.json", 2, LAB)


# %% Scenarios (BRIEF-shared section 2) and the advisor decisions used in --auto-approve mode
SCENARIOS: dict[str, dict] = {
    "S1": {"participant_id": "P-1001", "title": "AEP shopper", "expected_lob": "marketplace",
           "message": "I am on MA-CONTOSO-HMO-01. Is there a plan with a lower drug cost for my atorvastatin where I can "
                      "keep my cardiologist, Dr. Osei? And when could I switch?",
           "auto_decisions": ["approve"]},
    "S2": {"participant_id": "P-1003", "title": "Denied claim", "expected_lob": "accounts",
           "message": "My claim CLM-9003 was denied and I do not understand why. What do I need to send to get it paid?",
           "auto_decisions": ["approve"]},
    "S3": {"participant_id": "P-1005", "title": "Pre-Medicare, both LOBs", "expected_lob": "both",
           "message": "I have my sponsor's HRA and I need an ACA plan for next year. What is my HRA balance, what ACA plans "
                      "are there in my county, and what happens when I turn 65 next year? Which one should I pick?",
           "auto_decisions": ["revise: add the IEP dates for turning 65 to open_questions", "approve"]},
}


# %% build(): vendor common/ and data/ into hosted/, write the checkpoint (catch_up.py imports and calls this)
def build(*, vendor: bool = True, standalone: bool = True) -> dict:
    env = foundry_env.load_env()
    previous = require_previous_lab(standalone=standalone)
    counts: dict[str, int] = {}
    if vendor:
        prepare = lab_helpers.load_lab_module(f"{LAB_DIR.name}/hosted/prepare.py")
        counts = prepare.vendor()
    existing = json.loads(HOSTED_RECORD.read_text(encoding="utf-8")) if HOSTED_RECORD.exists() else {}
    record = {
        "lab": LAB, "agent_name": AGENT_NAME, "protocol": "responses", "model": lab_helpers.pick_model(env),
        "runtime": "python_3_14", "entry_point": "main.py", "hosted_dir": str(HOSTED_DIR.relative_to(ROOT)),
        "local_endpoint": f"{LOCAL_BASE}/responses", "project_endpoint": env.get("FOUNDRY_PROJECT_ENDPOINT", ""),
        "workflow": {"executors": ["intake", "marketplace-guide", "accounts-assistant", "merge", "compliance-reviewer",
                                   "compliance-gate", "advisor-coordinator", "advisor-handoff"],
                     "human_in_the_loop": "request_info paused per session; resumed by the advisor's next HTTP turn"},
        "knowledge": "mcp " + env["VIA_KB_MCP_URL"] if env.get("VIA_KB_MCP_URL") else "local search over data/knowledge",
        "session_store": "redis" if env.get("VIA_REDIS_URL") else "file",
        "previous_lab": {"agent_name": previous.get("agent_name"), "deployed": previous.get("deployed")} if previous else None,
        "vendored": counts or existing.get("vendored", {}),
        "deployed": existing.get("deployed") or {"version": None, "status": "not deployed", "recorded_at": None},
        "built_at": lab_helpers.now_iso(),
    }
    foundry_env.save_artifact(HOSTED_RECORD, record)
    log(f"wrote {HOSTED_RECORD.relative_to(LABS_DIR)} (agent {AGENT_NAME}, knowledge: {record['knowledge']}, sessions: {record['session_store']})")
    return record


# %% The local server (same lifecycle as Lab 1)
class HostedProcess:
    def __init__(self, hosted_dir: Path = HOSTED_DIR, port: int = PORT, log_path: Path = SERVER_LOG):
        self.hosted_dir, self.port, self.log_path = hosted_dir, port, log_path
        self.process: subprocess.Popen | None = None

    def start(self, timeout: float = 120.0) -> "HostedProcess":
        env = {**os.environ, **foundry_env.load_env(), "VIA_HOSTED_PORT": str(self.port), "PYTHONUNBUFFERED": "1"}
        env.setdefault("VIA_SESSION_DIR", str(ARTIFACTS / "sessions"))          # session map visible next to the packets
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.log_path.open("a", encoding="utf-8")
        self.process = subprocess.Popen([sys.executable, str(self.hosted_dir / "main.py")], cwd=str(self.hosted_dir),
                                        env=env, stdout=handle, stderr=subprocess.STDOUT)
        log(f"started hosted/main.py (pid {self.process.pid}) on port {self.port}; log -> {self.log_path.relative_to(LABS_DIR)}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise SystemExit(f"[{LAB}] hosted/main.py exited early (code {self.process.returncode}). Read {self.log_path}")
            with socket.socket() as probe:
                probe.settimeout(1.0)
                if probe.connect_ex(("127.0.0.1", self.port)) == 0:
                    return self
            time.sleep(1.0)
        self.stop()
        raise SystemExit(f"[{LAB}] server did not open port {self.port} within {timeout:.0f}s. Read {self.log_path}")

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
            log(f"stopped hosted/main.py (pid {self.process.pid})")


# %% Talking to via-triage-hosted: the envelope goes in the Responses `input`, JSON comes back as the text
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


def post_turn(base: str, text: str, previous_response_id: str | None = None) -> tuple[dict, str | None]:
    import httpx

    # VERIFY: POST /responses body and previous_response_id handling (see Lab 1 post_responses)
    body: dict = {"input": text, "stream": False}
    if previous_response_id:
        body["previous_response_id"] = previous_response_id
    response = httpx.post(f"{base.rstrip('/')}/responses", json=body, timeout=600.0)
    response.raise_for_status()
    payload = response.json()
    return parse_reply(output_text(payload)), payload.get("id")


def deployed_turn(text: str, previous_response_id: str | None = None) -> tuple[dict, str | None]:
    client = foundry_env.get_openai_client()
    kwargs = {"previous_response_id": previous_response_id} if previous_response_id else {}
    response = client.responses.create(input=text, extra_body=lab_helpers.agent_reference(AGENT_NAME), **kwargs)
    return parse_reply(response.output_text), getattr(response, "id", None)


# %% demo(): S1, S2, S3 with the advisor decisions, final packets written here (the client owns the artifact)
def interactive_decider(reply: dict) -> str:
    print(f"\n[{LAB}] ----- ADVISOR REVIEW ({reply.get('case_id')}) -----\n{reply.get('advisor_prompt')}")
    while True:
        answer = input(f"[{LAB}] advisor> ").strip()
        if answer:
            return answer


def save_packet(key: str, packet: dict) -> Path:
    path = PACKETS_DIR / f"{key}.json"
    foundry_env.save_artifact(path, packet)
    log(f"wrote {path.relative_to(LABS_DIR)} (decision {packet.get('advisor_decision')}, status {packet.get('status')}, "
        f"flags {len(packet.get('compliance_flags', []))}, facts {len(packet.get('facts_gathered', []))}, attempts {packet.get('packet_attempts')})")
    return path


def run_scenario(key: str, send, *, auto: bool, restart: "callable | None" = None) -> dict:
    scenario = SCENARIOS[key]
    session_id = f"{key}-{uuid.uuid4().hex[:8]}"
    log(f"=== {key} {scenario['title']} ({scenario['participant_id']}) session {session_id} ===")
    envelope = json.dumps({"session_id": session_id, "participant_id": scenario["participant_id"], "scenario": key, "message": scenario["message"]})
    print(f"[{LAB}] participant> {scenario['message']}")
    reply, response_id = send(envelope)
    decisions = list(scenario["auto_decisions"])
    for _ in range(6):
        if reply.get("status") != PENDING:
            break
        packet = reply.get("packet", {})
        print(f"[{LAB}] {AGENT_NAME}> status={reply['status']} lob={packet.get('lob')} attempts={packet.get('packet_attempts')} "
              f"flags={packet.get('compliance_flags')} resume_path={reply.get('resume_path')}")
        if restart:
            restart()                                        # the point of the exercise: the packet survives the process
        decision = decisions.pop(0) if auto and decisions else ("approve" if auto else interactive_decider(reply))
        print(f"[{LAB}] advisor> {decision}")
        reply, response_id = send(json.dumps({"session_id": session_id, "advisor": decision}), response_id)
    if reply.get("status") in {"approved", "declined"}:
        final = reply["packet"]
        final["session_id"] = session_id
        if guardrails.contains_recommendation(json.dumps(final.get("options_discussed", []))):
            log("WARNING: packet options contain recommendation language; check compliance_flags")
        save_packet(key, final)
        return final
    raise SystemExit(f"[{LAB}] {key} did not finish: {json.dumps(reply)[:400]}")


def demo(base: str | None = None, *, scenarios: tuple[str, ...] = ("S1", "S2", "S3"), auto: bool = False,
         deployed: bool = False, restart_between_turns: bool = False) -> dict[str, dict]:
    server: HostedProcess | None = None
    restart = None
    if deployed:
        send = deployed_turn
    else:
        if base is None:
            server = HostedProcess().start()
            base = LOCAL_BASE
            if restart_between_turns:
                def restart() -> None:
                    log("restarting the server between the participant turn and the advisor turn")
                    server.stop()
                    server.start()
        send = lambda text, prev=None: post_turn(base, text, prev)  # noqa: E731
    results = {}
    try:
        for key in scenarios:
            results[key] = run_scenario(key, send, auto=auto, restart=restart)
    finally:
        if server:
            server.stop()
    return results


# %% Deploy from source (same commands as Lab 1, different agent name)
def deploy_commands(env: dict | None = None) -> str:
    env = env or foundry_env.load_env()
    project_id = env.get("PROJECT_RESOURCE_ID") or "<set PROJECT_RESOURCE_ID in .env>"
    return "\n".join([
        f"cd {HOSTED_DIR.relative_to(ROOT)}",
        "python prepare.py",
        "azd config set auth.useAzCliAuth true && azd extension install azure.ai.agents",
        f"azd ai agent init --no-prompt --project-id \"{project_id}\" --agent-name {AGENT_NAME} \\",
        f"   --model-deployment {lab_helpers.pick_model(env)} --protocol responses --deploy-mode code --runtime python_3_14 \\",
        "   --entry-point main.py --dep-resolution remote_build",
        "# optional env on the hosted agent: VIA_REDIS_URL (shared session map), VIA_KB_MCP_URL (Lab 2 knowledge base)",
        "azd up",
        f"python ../lab3_hosted_multi_agent.py --record-version <version>",
        "python test_local.py --deployed",
    ])


def record_deployment(version: str, status: str = "active") -> dict:
    record = build(vendor=False, standalone=True)
    record["deployed"] = {"version": str(version), "status": status, "recorded_at": lab_helpers.now_iso()}
    foundry_env.save_artifact(HOSTED_RECORD, record)
    log(f"recorded deployed version {version} ({status})")
    return record


# %% YOUR TURN (10 min): revise instead of approve.
# Run without --auto-approve. At the S3 prompt type:  revise: add the IEP dates for turning 65 to open_questions
# Watch the server log: the coordinator sends your note to advisor-handoff and comes back with packet_attempts 2.
# Then approve. Compare S3.json with a teammate who approved on the first pass.

# %% YOUR TURN (10 min): lose the process, keep the case.
# Run: python lab3_hosted_multi_agent.py --auto-approve --scenario S2 --restart-between-turns
# The server is killed after the pending packet and started again before "approve". The reply shows
# resume_path=session_store: the paused workflow is gone, the packet in common.session_store is not, so the
# decision still completes. Then set VIA_REDIS_URL (docker run -d -p 6379:6379 redis:latest) and run again:
# now a second replica could have answered. Read artifacts/lab3/sessions/*.json to see what was stored.

# %% YOUR TURN (10 min): replace the keyword classifier with a model.
# via_workflow.classify_lob() is a keyword list: fine for three scenarios, wrong for the fourth. In
# IntakeExecutor.start ask a small structured-output agent instead and keep classify_lob() as the fallback:
#   class LobCall(BaseModel): lob: Literal["marketplace", "accounts", "both"]; reason: str
#   classifier = client.as_agent(name="lob-classifier", instructions="Classify by line of business. " + guardrails.COMPLIANCE_INSTRUCTIONS,
#                                default_options={"response_format": LobCall})
#   lob = (await classifier.run(intake.message)).value.lob
# Try: "My card was declined at the pharmacy when I picked up my atorvastatin." Keyword says both; is that right?


# %% Main
def main(args: argparse.Namespace) -> None:
    if args.record_version:
        record_deployment(args.record_version, args.status)
        return
    if args.deploy:
        build(vendor=not args.no_vendor, standalone=True)
        print(f"\n[{LAB}] deploy from source:\n{deploy_commands()}")
        return
    log(f"data check: {via_data.get_participant('P-1005').get('first_name', '?')} (P-1005) is in data/participants.json")
    build(vendor=not args.no_vendor, standalone=args.standalone)
    if args.skip_demo:
        return
    scenarios = tuple(SCENARIOS) if args.scenario == "all" else (args.scenario,)
    demo(args.base, scenarios=scenarios, auto=args.auto_approve, deployed=args.deployed, restart_between_turns=args.restart_between_turns)
    log("done. Checkpoint: paste S3.json's open_questions, compliance_flags and advisor_decision in the room chat.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenario", choices=["S1", "S2", "S3", "all"], default="all")
    parser.add_argument("--auto-approve", action="store_true", help="scripted advisor decisions (catch-up, CI)")
    parser.add_argument("--restart-between-turns", action="store_true", help="kill and restart the server before each advisor turn")
    parser.add_argument("--skip-demo", action="store_true")
    parser.add_argument("--no-vendor", action="store_true")
    parser.add_argument("--standalone", action="store_true", help="do not require artifacts/lab2")
    parser.add_argument("--base", default=None, help="talk to an already running server")
    parser.add_argument("--deployed", action="store_true", help="talk to the version Foundry runs")
    parser.add_argument("--deploy", action="store_true", help="print the azd commands")
    parser.add_argument("--record-version", default=None)
    parser.add_argument("--status", default="active")
    main(parser.parse_args())
