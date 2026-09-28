"""Lab 1: Hosted agent basics. The Via Benefits concierge as a Foundry Hosted Agent (Responses protocol).

Goal     Build, run and call the smallest complete hosted agent: Agent Framework `Agent` + `FoundryChatClient`
         + three `@tool` functions over the systems of record + the shared compliance block, served by
         `ResponsesHostServer`. Run it locally on port 8088, chat S1 and S2 through POST /responses, then
         deploy the same folder from source with `azd ai agent init` + `azd up` and invoke the version.
Inputs   .env (FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME, PROJECT_RESOURCE_ID for --deploy);
         common/ and data/ (vendored into hosted/ by build()).
Outputs  labs/artifacts/lab1/hosted.json (agent name, protocol, model, endpoints, deployed version),
         labs/artifacts/lab1/transcripts.md (S1 and S2, PII-redacted), labs/artifacts/lab1/hosted_local.log
Time     60 min (teach 10, demo 10, do 35, checkpoint 5)

Run top to bottom:   python lab1_hosted_basics.py [--skip-demo] [--base http://localhost:8088] [--deployed]
                     python lab1_hosted_basics.py --deploy                 (prints the azd commands)
                     python lab1_hosted_basics.py --record-version 2       (after azd up: store the version)
Run cell by cell:    open lab1_walkthrough.ipynb, or use the "# %%" cells in VS Code.
"""
# %% [markdown]
# # Lab 1: Hosted agent basics
#
# **Where this runs.** This notebook is the learner's cockpit: it runs on your workstation (dev container or
# venv), vendors `common/` and `data/` into `hosted/`, starts `hosted/main.py` as a local process on port 8088,
# calls `POST /responses`, and prints the azd commands that deploy the very same folder to Microsoft Foundry.
# `hosted/main.py` is the product: Foundry builds a container from the ZIP azd uploads, runs it, scales it and
# gives it an identity. Nothing customer-facing runs in this notebook.
#
# **Checkpoint artifact.** `labs/artifacts/lab1/hosted.json` (agent `via-concierge-hosted`, protocol, model,
# deployed version once you ran `azd up`) and `labs/artifacts/lab1/transcripts.md`. Lab 2 starts from hosted.json.

# %% Imports and paths
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # WTW-Foundry-Agents-Labs/
LABS_DIR = ROOT / "labs"
LAB_DIR = Path(__file__).resolve().parent
for folder in (ROOT, LABS_DIR):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
from common import foundry_env, guardrails, via_data  # noqa: E402

import lab_helpers  # noqa: E402

LAB = "lab1"
AGENT_NAME = "via-concierge-hosted"
HOSTED_DIR = LAB_DIR / "hosted"
ARTIFACTS = lab_helpers.artifact_path(LAB)
HOSTED_RECORD = ARTIFACTS / "hosted.json"
TRANSCRIPTS = ARTIFACTS / "transcripts.md"
SERVER_LOG = ARTIFACTS / "hosted_local.log"
PORT = int(os.environ.get("VIA_HOSTED_PORT", "8088"))
LOCAL_BASE = f"http://localhost:{PORT}"


def log(message: str) -> None:
    print(f"[{LAB}] {message}", flush=True)


# %% Scenarios (BRIEF-shared section 2): S1 AEP shopper, S2 denied claim. Identity = participant_id + ZIP only.
SCENARIOS: dict[str, dict] = {
    "S1": {"participant_id": "P-1001", "title": "AEP shopper (Evelyn Marsh)",
           "turns": ["When can I change my plan this year? I am on MA-CONTOSO-HMO-01 and I would like a lower drug "
                     "cost for atorvastatin while keeping my cardiologist.",
                     "Just tell me which plan I should pick."]},
    "S2": {"participant_id": "P-1003", "title": "Denied claim (Harold Bing)",
           "turns": ["My claim CLM-9003 was denied. What is my HRA balance, and what does the account show about that claim?"]},
}


def first_turn(scenario: dict) -> str:
    return f"{lab_helpers.identity_line(scenario['participant_id'])} {scenario['turns'][0]}"


# %% build(): vendor common/ and data/ into hosted/, write the checkpoint (catch_up.py imports and calls this)
def build(*, vendor: bool = True) -> dict:
    """Prepare the flat deployable folder and record what Lab 2 needs. Never calls Azure."""
    env = foundry_env.load_env()
    counts: dict[str, int] = {}
    if vendor:
        prepare = lab_helpers.load_lab_module(f"{LAB_DIR.name}/hosted/prepare.py")
        counts = prepare.vendor()
    previous = json.loads(HOSTED_RECORD.read_text(encoding="utf-8")) if HOSTED_RECORD.exists() else {}
    record = {
        "lab": LAB,
        "agent_name": AGENT_NAME,
        "protocol": "responses",
        "model": lab_helpers.pick_model(env),
        "runtime": "python_3_14",
        "entry_point": "main.py",
        "hosted_dir": str(HOSTED_DIR.relative_to(ROOT)),
        "local_endpoint": f"{LOCAL_BASE}/responses",
        "project_endpoint": env.get("FOUNDRY_PROJECT_ENDPOINT", ""),
        "tools": ["get_participant", "get_enrollment_window", "get_hra_account"],
        "vendored": counts or previous.get("vendored", {}),
        "deployed": previous.get("deployed") or {"version": None, "status": "not deployed", "recorded_at": None},
        "built_at": lab_helpers.now_iso(),
    }
    foundry_env.save_artifact(HOSTED_RECORD, record)
    log(f"wrote {HOSTED_RECORD.relative_to(LABS_DIR)} (agent {AGENT_NAME}, model {record['model']}, "
        f"deployed version {record['deployed']['version'] or 'none yet'})")
    return record


# %% The local server: hosted/main.py as a child process on port 8088 (Foundry does this for you in the cloud)
class HostedProcess:
    """Start and stop hosted/main.py. Logs go to artifacts/lab1/hosted_local.log so the room can read them."""

    def __init__(self, hosted_dir: Path = HOSTED_DIR, port: int = PORT, log_path: Path = SERVER_LOG):
        self.hosted_dir, self.port, self.log_path = hosted_dir, port, log_path
        self.process: subprocess.Popen | None = None

    def start(self, timeout: float = 90.0) -> "HostedProcess":
        env = {**os.environ, **foundry_env.load_env(), "VIA_HOSTED_PORT": str(self.port), "PYTHONUNBUFFERED": "1"}
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.log_path.open("w", encoding="utf-8")
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
                    log("server is accepting connections")
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


# %% Calling the Responses protocol: the same body a web chat backend would send
def output_text(payload: dict) -> str:
    """output_text when the server includes it, else the text parts of the output message items."""
    if payload.get("output_text"):
        return payload["output_text"]
    parts = []
    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts)


def post_responses(base: str, text: str, *, previous_response_id: str | None = None, session_id: str | None = None) -> dict:
    """POST /responses with the OpenAI Responses request shape. Returns {"text", "id", "raw"}.

    Multi-turn: the OpenAI Responses way is previous_response_id (the id of the last response). The host server
    may also accept a session identifier that maps to its own session; we send both when given.
    """
    import httpx

    # VERIFY against https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents before delivery:
    # the exact path (/responses) and whether ResponsesHostServer surfaces a session/conversation id in the
    # response (for example a `conversation` field or a header) or relies only on previous_response_id.
    body: dict = {"input": text, "stream": False}
    if previous_response_id:
        body["previous_response_id"] = previous_response_id
    if session_id:
        body["session_id"] = session_id                  # VERIFY: request field name for the host's session
    response = httpx.post(f"{base.rstrip('/')}/responses", json=body, timeout=180.0)
    response.raise_for_status()
    payload = response.json()
    return {"text": output_text(payload), "id": payload.get("id"), "raw": payload}


def call_deployed(text: str, *, previous_response_id: str | None = None) -> dict:
    """Same conversation, but against the version Foundry runs: Responses API + agent_reference (BRIEF-shared 5a)."""
    client = foundry_env.get_openai_client()
    kwargs = {"previous_response_id": previous_response_id} if previous_response_id else {}
    response = client.responses.create(input=text, extra_body=lab_helpers.agent_reference(AGENT_NAME), **kwargs)
    return {"text": response.output_text, "id": getattr(response, "id", None), "raw": None}


# %% demo(): run S1 and S2 as multi-turn conversations, print, write the redacted transcript
def run_scenario(key: str, scenario: dict, send) -> list[dict]:
    log(f"=== {key} {scenario['title']} ({scenario['participant_id']}) ===")
    turns, previous_id = [], None
    for index, text in enumerate(scenario["turns"]):
        user_text = first_turn(scenario) if index == 0 else text
        print(f"[{LAB}] participant> {user_text}")
        result = send(user_text, previous_response_id=previous_id)
        previous_id = result["id"] or previous_id
        report = lab_helpers.guardrail_report(result["text"])
        print(f"[{LAB}] {AGENT_NAME}> {result['text']}\n[{LAB}] checks: {lab_helpers.fmt_checks(report)}")
        turns.append({"user": user_text, "agent": result["text"], "response_id": result["id"], "checks": report})
    return turns


def write_transcripts(results: dict[str, list[dict]], target: str) -> Path:
    lines = [f"# Lab 1 transcripts: {AGENT_NAME} ({target})", "",
             f"Generated {lab_helpers.now_iso()}. Text passed through guardrails.redact_pii before writing.", ""]
    for key, turns in results.items():
        lines += [f"## {key}: {SCENARIOS[key]['title']}", ""]
        for turn in turns:
            lines += [f"**Participant:** {guardrails.redact_pii(turn['user'])}", "",
                      f"**{AGENT_NAME}:** {guardrails.redact_pii(turn['agent'])}", "",
                      f"_checks: {lab_helpers.fmt_checks(turn['checks'])}_", ""]
    foundry_env.save_artifact(TRANSCRIPTS, "\n".join(lines) + "\n")
    log(f"wrote {TRANSCRIPTS.relative_to(LABS_DIR)}")
    return TRANSCRIPTS


def demo(base: str | None = None, *, deployed: bool = False, scenarios: tuple[str, ...] = ("S1", "S2")) -> Path:
    """Chat S1 and S2. Default: start hosted/main.py, talk to it, stop it. --base: talk to a server you started.
    --deployed: talk to the version Foundry runs."""
    server: HostedProcess | None = None
    if deployed:
        send, target = call_deployed, "deployed version through the Foundry project"
    else:
        if base is None:
            server = HostedProcess().start()
            base = LOCAL_BASE
        send, target = (lambda text, **kw: post_responses(base, text, **kw)), f"local {base}"
    try:
        results = {key: run_scenario(key, SCENARIOS[key], send) for key in scenarios}
    finally:
        if server:
            server.stop()
    return write_transcripts(results, target)


# %% Deploy from source: Foundry builds the container from the ZIP azd uploads (no Docker on your laptop)
def deploy_commands(env: dict | None = None) -> str:
    env = env or foundry_env.load_env()
    project_id = env.get("PROJECT_RESOURCE_ID") or "<set PROJECT_RESOURCE_ID in .env: /subscriptions/.../projects/<name>>"
    model = lab_helpers.pick_model(env)
    return "\n".join([
        f"cd {HOSTED_DIR.relative_to(ROOT)}",
        "python prepare.py                       # vendor common/ and data/ (already done by build())",
        "azd config set auth.useAzCliAuth true",
        "azd extension install azure.ai.agents",
        f"azd ai agent init --no-prompt --project-id \"{project_id}\" --agent-name {AGENT_NAME} \\",
        f"   --model-deployment {model} --protocol responses --deploy-mode code --runtime python_3_14 \\",
        "   --entry-point main.py --dep-resolution remote_build",
        "azd up                                  # packages the folder, uploads, builds remotely, waits for the version",
        "# then, in the portal: Agents -> via-concierge-hosted -> Versions: wait for status active, open Logs",
        f"python ../lab1_hosted_basics.py --record-version <version>   # store it in artifacts/lab1/hosted.json",
        "python hosted/test_local.py --deployed  # smoke test the deployed version",
    ])


def record_deployment(version: str, status: str = "active") -> dict:
    record = build(vendor=False)
    record["deployed"] = {"version": str(version), "status": status, "recorded_at": lab_helpers.now_iso()}
    foundry_env.save_artifact(HOSTED_RECORD, record)
    log(f"recorded deployed version {version} ({status}) in {HOSTED_RECORD.relative_to(LABS_DIR)}")
    return record


# %% YOUR TURN (5 min): add a get_sponsor tool.
# Open hosted/main.py, wrap via_data.get_sponsor(sponsor_id) with @tool like the other three, append it to TOOLS
# (the solution is in the commented block right there), then run:
#     python lab1_hosted_basics.py --skip-demo && python lab1_hosted_basics.py
# and ask, as P-1001: "Who is my plan sponsor and how much is the HRA for the year?" (edit SCENARIOS or use
# post_responses(LOCAL_BASE, "...") from the notebook). You should see the sponsor name and the annual amount
# without the model inventing either.

# %% YOUR TURN (10 min): tighten an instruction and ship a new version.
# In hosted/main.py change rule 3 of ROLE_INSTRUCTIONS so the agent ALWAYS names the enrollment window when it
# offers an advisor. Run the demo locally and confirm S1 turn 2 now includes "AEP". Then `azd up` again from
# hosted/: Foundry creates a new version only when the ZIP hash or definition changed. In the portal compare
# the two versions; record the new one with --record-version. Old versions stay for audit and rollback (Lab 4).

# %% YOUR TURN (5 min): call the deployed endpoint from the notebook.
# After azd up and --record-version:
#     call_deployed("Hi, this is P-1005, ZIP 84010. What is my enrollment window?")["text"]
# Same agent_reference shape as any Foundry agent. If you get 403, you need Foundry Agent Consumer or Foundry
# User at project scope; if 424 session_not_ready, the container is still starting: read the version logstream.


# %% Main
def main(args: argparse.Namespace) -> None:
    if args.record_version:
        record_deployment(args.record_version, args.status)
        return
    if args.deploy:
        build(vendor=not args.no_vendor)
        print(f"\n[{LAB}] deploy from source (needs Foundry Project Manager at project scope):\n{deploy_commands()}")
        return
    log(f"data check: {via_data.get_participant('P-1001').get('first_name', '?')} (P-1001) is in data/participants.json")
    build(vendor=not args.no_vendor)
    if args.skip_demo:
        return
    demo(args.base, deployed=args.deployed)
    log("done. Checkpoint: paste the S1 turn 2 answer (the refusal to pick a plan) and your hosted.json in the room chat.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-demo", action="store_true", help="only vendor and write hosted.json")
    parser.add_argument("--no-vendor", action="store_true", help="do not re-copy common/ and data/ into hosted/")
    parser.add_argument("--base", default=None, help="talk to an already running server, e.g. http://localhost:8088")
    parser.add_argument("--deployed", action="store_true", help="run S1 and S2 against the version Foundry runs")
    parser.add_argument("--deploy", action="store_true", help="print the azd commands with your .env values")
    parser.add_argument("--record-version", default=None, help="store the deployed version number in hosted.json")
    parser.add_argument("--status", default="active", help="version status to record (default active)")
    main(parser.parse_args())
