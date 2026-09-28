# %% [markdown]
# # Lab 2: Hosted agent with Foundry IQ knowledge and external session state
#
# **Where this runs.** This notebook runs on your workstation (the dev container kernel, `az login`).
# It builds the Foundry IQ knowledge base in Azure AI Search, vendors `common/` and `data/` into `hosted/`,
# then starts `hosted/main.py` as a local process on port 8088 and talks to it over `POST /responses`.
# `hosted/main.py` is the product: the same file is what `azd up` ships to Foundry as a container.
#
# **Checkpoint artifacts.** `artifacts/lab2/knowledge.json` (kb name, MCP endpoint, project connection),
# `artifacts/lab2/hosted.json` (agent name, local url, azd commands), `artifacts/lab2/sessions/` and
# `artifacts/lab2/transcripts.md` (the kill-and-restart transcript with the continuity check).
"""Lab 2: Hosted agent with Foundry IQ knowledge and external session state.

Goal:    Build the knowledge base (knowledge_base.py), then run via-concierge-hosted v2 (hosted/main.py) locally:
         two turns on one session id, kill the process, start it again, a third turn that depends on memory.
         Print the continuity check. Then print the azd commands that deploy the same folder as a new version.
Inputs:  artifacts/lab1/hosted.json (Lab 1 deployed the basics agent); data/knowledge through via_data
Outputs: artifacts/lab2/knowledge.json, hosted.json, sessions/<session>.json, message_store/ (file fallback),
         transcripts.md
Time:    60 min (teach 10, demo 10, do 35, checkpoint 5); the index build itself takes 1 to 2 min

Run:     python lab2_hosted_knowledge.py                 build + demo
         python lab2_hosted_knowledge.py --build-only    knowledge base + vendoring + hosted.json
         python lab2_hosted_knowledge.py --demo-only     reuse artifacts/lab2/knowledge.json
         python lab2_hosted_knowledge.py --deploy        print the azd commands (nothing is executed)
         python lab2_hosted_knowledge.py --demo-only --session-id S1-evelyn --no-restart
"""
# %% Imports and environment
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # wtw-foundry-hosted-agents-labs/ (common/ and data/ live here)
sys.path.insert(0, str(ROOT))
from common import via_data, foundry_env, guardrails  # noqa: E402

LABS_DIR = Path(__file__).resolve().parents[1]  # labs/ (lab_helpers.py, catch_up.py, artifacts/)
sys.path.insert(0, str(LABS_DIR))
import lab_helpers as helpers  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import knowledge_base  # noqa: E402  (the notebook part: indexes, knowledge sources, kb, project connection)

ENV = foundry_env.load_env()
MODEL = helpers.pick_model(ENV)
LAB = "lab2"
AGENT_NAME = "via-concierge-hosted"
HOSTED_DIR = HERE / "hosted"
DEFAULT_PORT = 8088
DEFAULT_SESSION_ID = "S1-evelyn"


# %% build(): knowledge base + project connection, vendor common/ and data/, record the hosted agent
def build(skip_connection: bool = False) -> dict:
    knowledge = knowledge_base.build(skip_connection=skip_connection)
    vendored = helpers.load_lab_module("lab2-hosted-knowledge-sessions/hosted/prepare.py").vendor()
    env_for_container = {
        "AZURE_AI_MODEL_DEPLOYMENT_NAME": MODEL,
        "VIA_KB_MCP_URL": knowledge["mcp_endpoint"],
        "VIA_REDIS_URL": "<rediss://... Azure Managed Redis, or leave unset for the file store>",
        "VIA_TODAY": ENV.get("VIA_TODAY", "2026-10-06"),
    }
    info = {
        "lab": LAB, "agent_name": AGENT_NAME, "version_label": "v2 (knowledge + sessions)", "protocol": "responses",
        "entry_point": "labs/lab2-hosted-knowledge-sessions/hosted/main.py", "local_url": f"http://localhost:{DEFAULT_PORT}",
        "model": MODEL, "tools": ["get_participant", "get_enrollment_window", "get_hra_account", "search_plans", "compare_plans",
                                  "knowledge_base_retrieve (MCP via-kb)"],
        "vendored": vendored, "env_for_container": env_for_container, "azd_commands": azd_commands(env_for_container),
        "status": "not deployed", "created_at": helpers.now_iso(),
    }
    path = helpers.artifact_path(LAB, "hosted.json")
    if path.exists():
        info = {**foundry_env.load_artifact(path), **info}
    foundry_env.save_artifact(path, info)
    print(f"[lab2] saved {path.relative_to(LABS_DIR)}")
    return info


def azd_commands(env_for_container: dict) -> list[str]:
    """Deploy from source: no Dockerfile, Foundry builds the container from the ZIP azd uploads."""
    commands = ["cd labs/lab2-hosted-knowledge-sessions/hosted", "python prepare.py",
                "azd config set auth.useAzCliAuth true", "azd extension install azure.ai.agents",
                f"azd ai agent init --no-prompt --project-id $PROJECT_RESOURCE_ID --agent-name {AGENT_NAME} "
                f"--model-deployment {env_for_container['AZURE_AI_MODEL_DEPLOYMENT_NAME']} --protocol responses "
                "--deploy-mode code --runtime python_3_14 --entry-point main.py --dep-resolution remote_build"]
    # VERIFY against https://learn.microsoft.com/azure/foundry/agents/how-to/hosted-agents before delivery: azd env
    # values become container environment variables through the agent.yaml environment block that init writes.
    commands += [f"azd env set {key} \"{value}\"" for key, value in env_for_container.items() if not value.startswith("<")]
    commands += ["azd up", "python test_local.py --deployed"]
    return commands


# %% The local server: hosted/main.py as a subprocess (what Foundry does for you in the cloud)
def port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def start_server(knowledge: dict, port: int = DEFAULT_PORT, timeout_s: int = 90) -> subprocess.Popen:
    if port_open(port):
        raise SystemExit(f"[lab2] port {port} is already in use: stop the other main.py (or pass --port)")
    env = {**os.environ, **{k: v for k, v in ENV.items() if v}}
    env.update({"VIA_KB_MCP_URL": knowledge.get("mcp_endpoint", ""), "VIA_HOSTED_PORT": str(port),
                "VIA_MESSAGE_STORE_DIR": str(helpers.artifact_path(LAB, "message_store")),
                "VIA_SESSION_DIR": str(helpers.artifact_path(LAB, "sessions"))})
    proc = subprocess.Popen([sys.executable, str(HOSTED_DIR / "main.py")], cwd=str(HOSTED_DIR), env=env)
    started = time.time()
    while time.time() - started < timeout_s:
        if proc.poll() is not None:
            raise SystemExit(f"[lab2] main.py exited early with code {proc.returncode}; read its output above")
        if port_open(port):
            print(f"[lab2] main.py pid {proc.pid} listening on http://localhost:{port} after {time.time() - started:.0f}s")
            return proc
        time.sleep(1)
    proc.kill()
    raise SystemExit(f"[lab2] main.py did not open port {port} within {timeout_s}s")


def stop_server(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
    print(f"[lab2] killed main.py pid {proc.pid} (exit {proc.returncode}); its memory is gone")


# %% One turn over HTTP: the OpenAI Responses shape, with our session id as the conversation
def ask(port: int, text: str, session_id: str, previous_response_id: str | None = None) -> tuple[str, dict]:
    import httpx

    body = {"input": text, "stream": False, "conversation": session_id}
    # VERIFY against https://learn.microsoft.com/azure/foundry/agents/how-to/hosted-agents before delivery: how
    # ResponsesHostServer surfaces a session/conversation id. Fallback when it ignores `conversation`: send
    # previous_response_id (only continuous while the same process is alive, which is the point of this lab).
    if previous_response_id:
        body["previous_response_id"] = previous_response_id
    response = httpx.post(f"http://localhost:{port}/responses", json=body, timeout=180.0)
    response.raise_for_status()
    payload = response.json()
    text_out = payload.get("output_text") or "\n".join(
        c.get("text", "") for item in payload.get("output", []) for c in (item.get("content") or []) if c.get("text"))
    return text_out, payload


def record_turn(store, session_id: str, participant_id: str, payload: dict, agent_version: str) -> None:
    """Client-side session map: which conversation belongs to this session, last response id, turn count."""
    rec = store.get(session_id) or helpers.SessionRecord(session_id=session_id, participant_id=participant_id,
                                                          agent_name=AGENT_NAME, agent_version=agent_version,
                                                          conversation_id=None, last_response_id=None, turn_count=0,
                                                          updated_at=helpers.now_iso(), notes={"lab": LAB})
    rec.conversation_id = payload.get("conversation") or rec.conversation_id or session_id
    rec.last_response_id = payload.get("id")
    rec.turn_count += 1
    rec.updated_at = helpers.now_iso()
    store.put(rec)


# %% demo(): S1 over three turns with a process kill in the middle
TURNS = [
    "{identity} I take atorvastatin 20mg and I am on the Contoso Advantage Choice HMO. Is there a Salt Lake County "
    "plan with a lower formulary tier for it? Show me a comparison.",
    "And when am I allowed to switch plans this year? Please cite the rule.",
    "Before we go on: remind me which drug I asked about and which plans you compared for me.",
]
MEMORY_MARKERS = ["atorvastatin"]


def demo(knowledge: dict | None = None, session_id: str = DEFAULT_SESSION_ID, port: int = DEFAULT_PORT,
         restart: bool = True) -> dict:
    knowledge = knowledge or helpers.require_artifact(LAB, "knowledge.json", through=2, caller="lab2")
    hosted = helpers.require_artifact(LAB, "hosted.json", through=2, caller="lab2")
    if not (HOSTED_DIR / "common").exists():
        helpers.load_lab_module("lab2-hosted-knowledge-sessions/hosted/prepare.py").vendor()
    store = helpers.get_session_store(helpers.artifact_path(LAB, "sessions"), log_prefix="[lab2]")
    participant_id = "P-1001"
    identity = helpers.identity_line(participant_id)
    transcript, previous = [], None
    proc = start_server(knowledge, port)
    try:
        for n, turn in enumerate(TURNS, start=1):
            if n == 3 and restart:
                stop_server(proc)
                print("[lab2] restarting main.py: a fresh process, same session id, history must come from the store")
                proc = start_server(knowledge, port)
                previous = None                  # a new process knows no response ids: only the store can help now
            text = turn.format(identity=identity)
            print(f"\n[lab2] turn {n} participant> {text}")
            reply, payload = ask(port, text, session_id, previous)
            previous = payload.get("id")
            record_turn(store, session_id, participant_id, payload, hosted.get("version_label", "v2"))
            checks = helpers.guardrail_report(reply)
            print(f"[lab2] turn {n} {AGENT_NAME}> {reply}")
            print(f"[lab2] turn {n} checks: {helpers.fmt_checks(checks)}")
            transcript.append({"turn": n, "participant": text, "agent": guardrails.redact_pii(reply), "checks": checks,
                               "process_pid": proc.pid})
    finally:
        stop_server(proc)
    continuity = all(marker in transcript[-1]["agent"].lower() for marker in MEMORY_MARKERS)
    result = {"session_id": session_id, "restarted_before_turn_3": restart, "continuity_ok": continuity,
              "pids": sorted({t["process_pid"] for t in transcript}), "turns": transcript, "finished_at": helpers.now_iso()}
    print(f"\n[lab2] continuity check: {'OK' if continuity else 'FAIL'} "
          f"(turn 3 answered by pid {transcript[-1]['process_pid']}, turns 1-2 by pid {transcript[0]['process_pid']}; "
          f"markers {MEMORY_MARKERS})")
    if not continuity:
        print("[lab2] FAIL is expected when common.message_store is absent or when the server ignored the session id: "
              "read the [hosted] history: line in the server output above")
    write_transcript(result)
    hosted["last_demo"] = {k: v for k, v in result.items() if k != "turns"}
    foundry_env.save_artifact(helpers.artifact_path(LAB, "hosted.json"), hosted)
    return result


def write_transcript(result: dict) -> Path:
    lines = [f"# Lab 2 transcript: {AGENT_NAME} v2, session {result['session_id']}", "",
             f"Generated {result['finished_at']}. Process killed before turn 3: {result['restarted_before_turn_3']}. "
             f"Continuity check: {'OK' if result['continuity_ok'] else 'FAIL'}. Text is redacted.", ""]
    for t in result["turns"]:
        lines += [f"## Turn {t['turn']} (pid {t['process_pid']})", "", f"Participant: {t['participant']}", "",
                  f"Agent: {t['agent']}", "", f"Checks: {helpers.fmt_checks(t['checks'])}", ""]
    path = helpers.artifact_path(LAB, "transcripts.md")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[lab2] saved {path.relative_to(LABS_DIR)}")
    return path


# %% --deploy: the runbook (printed, not executed; needs Foundry Project Manager on the project)
def print_deploy(hosted: dict | None = None) -> None:
    hosted = hosted or helpers.require_artifact(LAB, "hosted.json", through=2, caller="lab2")
    print("[lab2] deploy from source, then roll the version and prove sessions survive:")
    for command in hosted["azd_commands"]:
        print(f"[lab2]   $ {command}")
    print("[lab2] wait for version status `active` in the portal (Agents > via-concierge-hosted > versions).")
    print("[lab2] version roll: change one line in hosted/main.py (for example the greeting), `azd up` again, then")
    print("[lab2]   python hosted/test_local.py --deployed   with the same session: Redis keeps the history, the")
    print("[lab2]   new container answers turn 3 as if nothing happened. A 424 session_not_ready means the container")
    print("[lab2]   is still starting: read the logstream in the portal and retry.")


# %% YOUR TURN (5 min): scale out. Start Redis (docker run -d -p 6379:6379 redis:latest),
# export VIA_REDIS_URL=redis://localhost:6379/0, then run TWO servers: --port 8088 and --port 8089. Send turn 1
# to 8088 and turn 3 to 8089 with the same session id. Two replicas, one participant, one history.
# Solution (from a second terminal, after `python lab2_hosted_knowledge.py --demo-only --no-restart`):
#   VIA_REDIS_URL=redis://localhost:6379/0 VIA_HOSTED_PORT=8089 python hosted/main.py &
#   python - <<'EOF'
#   import lab2_hosted_knowledge as lab
#   print(lab.ask(8089, lab.TURNS[2], "S1-evelyn")[0])
#   EOF

# %% YOUR TURN (5 min): break it on purpose. Point VIA_MESSAGE_STORE_DIR at an empty folder for the restarted
# process only, or temporarily rename common/message_store.py in hosted/. Turn 3 now asks "which drug?" back.
# That is what a hosted agent with in-process memory does to a participant on every version roll.

# %% YOUR TURN (5 min): watch the knowledge tool work. Ask (same session) "What proof of payment do you accept
# for a premium claim?" and check the citation is [KB-ACC-001]. Then remove VIA_KB_MCP_URL from the server env
# and ask again: rule 4 makes the agent say the rule text is not at hand instead of inventing it.
# Solution:
#   print(lab.ask(8088, "What proof of payment do you accept for a premium claim?", "S1-evelyn")[0])


# %% Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--demo-only", action="store_true", help="reuse artifacts/lab2/knowledge.json and hosted.json")
    parser.add_argument("--deploy", action="store_true", help="print the azd commands and the version-roll check")
    parser.add_argument("--skip-connection", action="store_true", help="skip the ARM project connection PUT")
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-restart", action="store_true", help="keep one process for all three turns")
    args = parser.parse_args()
    if args.deploy:
        print_deploy()
    elif args.demo_only:
        demo(session_id=args.session_id, port=args.port, restart=not args.no_restart)
    else:
        build(skip_connection=args.skip_connection)
        if not args.build_only:
            demo(session_id=args.session_id, port=args.port, restart=not args.no_restart)
            print_deploy()
