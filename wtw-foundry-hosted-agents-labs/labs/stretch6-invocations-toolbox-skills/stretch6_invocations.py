"""Stretch 6: Invocations protocol, Foundry Toolbox and Skills. The second hosting protocol, compared with the first.

Goal     Build and call a hosted agent on the INVOCATIONS protocol (one structured request -> one structured
         response): denied-claims-review over a list of claim ids. Then run the Responses concierge with a bundled
         Skill (hra-reimbursement-rules) and, when configured, a Foundry Toolbox. Compare the two protocols.
Inputs   labs/artifacts/lab1/hosted.json (or `python catch_up.py --through 1`), .env; optional TOOLBOX_NAME,
         TOOLBOX_MCP_URL, SKILL_NAMES for the skills agent.
Outputs  labs/artifacts/stretch6/invocations.json (both agents, protocol comparison, sample batch result),
         labs/artifacts/stretch6/claim_reviews/*.json, labs/artifacts/stretch6/*_local.log
Time     45-60 min (stretch)

Run top to bottom:   python stretch6_invocations.py                  (invocations agent locally + one batch)
                     python stretch6_invocations.py --offline        (no model: deterministic packets only)
                     python stretch6_invocations.py --skills-demo    (responses + skills agent locally, S2 question)
                     python stretch6_invocations.py --deploy         (azd commands for both agents)
Run cell by cell:    open stretch6_walkthrough.ipynb, or use the "# %%" cells in VS Code.
"""
# %% [markdown]
# # Stretch 6: Invocations, Toolbox and Skills
#
# **Where this runs.** This notebook (workstation) vendors `common/`, `data/` and `skills/` into the two hosted
# folders, starts each `main.py` locally on port 8088 and calls it: the Invocations agent with a JSON batch of claim
# ids, the Responses agent with a participant question that makes it read the bundled skill. Both folders deploy to
# Foundry with `azd` (`--protocol invocations` and `--protocol responses`); Foundry Toolbox and Skills are preview.
#
# **Checkpoint artifact.** `labs/artifacts/stretch6/invocations.json` (agent names, protocol comparison, one batch
# result) and `labs/artifacts/stretch6/claim_reviews/CLM-*.json`.

# %% Imports and paths
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]      # WTW-Foundry-Agents-Labs/
LABS_DIR = ROOT / "labs"
LAB_DIR = Path(__file__).resolve().parent
for folder in (ROOT, LABS_DIR, LAB_DIR / "hosted-invocations"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
from common import foundry_env, guardrails, via_data  # noqa: E402

import lab_helpers  # noqa: E402
from claims_review import hra_rules, review_claims  # noqa: E402  (pure Python; the same code the agent calls as a tool)

LAB = "stretch6"
INVOCATIONS_AGENT = "via-claims-review-invocations"
SKILLS_AGENT = os.environ.get("VIA_AGENT_NAME", "via-concierge-hosted")
INVOCATIONS_DIR = LAB_DIR / "hosted-invocations"
SKILLS_HOST_DIR = LAB_DIR / "hosted-responses-skills"
SKILLS_SRC = LAB_DIR / "skills"
ARTIFACTS = lab_helpers.artifact_path(LAB)
RECORD = ARTIFACTS / "invocations.json"
REVIEWS_DIR = ARTIFACTS / "claim_reviews"
PORT = int(os.environ.get("VIA_HOSTED_PORT", "8088"))
LOCAL_BASE = f"http://localhost:{PORT}"
BATCH = ["CLM-9003", "CLM-9021", "CLM-9001"]      # denied with a fix, denied without a fix, paid
S2_QUESTION = "Hi, this is P-1003, ZIP 84604. My claim CLM-9003 was denied. Why, and what exactly do I need to send?"


def log(message: str) -> None:
    print(f"[{LAB}] {message}", flush=True)


# %% The comparison the README teaches (also written into the artifact)
PROTOCOLS = [
    {"dimension": "Interaction", "invocations": "one structured request -> one structured response", "responses": "multi-turn conversation"},
    {"dimension": "Tool use", "invocations": "deterministic; the model fills in prose only", "responses": "model-directed: decides when to call tools, skills, toolbox"},
    {"dimension": "Streaming", "invocations": "no (batch result)", "responses": "token by token (OpenAI compatible)"},
    {"dimension": "State", "invocations": "stateless", "responses": "session history (Lab 2 message store)"},
    {"dimension": "Request body", "invocations": '{"message": "<json string>"}  (VERIFY path)', "responses": '{"input": "...", "previous_response_id"?}  POST /responses'},
    {"dimension": "Best for", "invocations": "batch jobs, API-to-API, nightly reviews, pipelines", "responses": "advisor and participant chat, research"},
    {"dimension": "Host server", "invocations": "InvocationsHostServer(agent)", "responses": "ResponsesHostServer(agent)"},
    {"dimension": "Via Benefits example", "invocations": "denied-claims-review over the day's denials", "responses": "via-concierge-hosted, via-triage-hosted"},
]


# %% build(): vendor into both hosted folders, copy skills/, write the checkpoint (catch_up.py imports and calls this)
def build(*, vendor: bool = True) -> dict:
    env = foundry_env.load_env()
    previous = lab_helpers.artifact_path("lab1", "hosted.json")
    lab1 = foundry_env.load_artifact(previous) if previous.exists() else {}
    if not lab1:
        log("artifacts/lab1/hosted.json missing (run Lab 1 or `python catch_up.py --through 1`); continuing, S6 does not depend on it")
    counts: dict[str, dict] = {}
    if vendor:
        prepare = lab_helpers.load_lab_module(f"{LAB_DIR.name}/hosted-invocations/prepare.py")
        counts["hosted-invocations"] = prepare.vendor()
        counts["hosted-responses-skills"] = vendor_into(SKILLS_HOST_DIR)
        target = SKILLS_HOST_DIR / "skills"
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(SKILLS_SRC, target, dirs_exist_ok=True)
        counts["hosted-responses-skills"]["skills"] = sum(1 for p in target.rglob("SKILL.md"))
        log(f"copied skills/ into hosted-responses-skills/ ({counts['hosted-responses-skills']['skills']} SKILL.md)")
    skills = sorted(p.parent.name for p in SKILLS_SRC.glob("*/SKILL.md"))
    existing = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.exists() else {}
    record = {
        "lab": LAB, "preview": ["Foundry Toolbox", "Foundry Skills"],
        "agents": {
            "invocations": {"agent_name": INVOCATIONS_AGENT, "protocol": "invocations", "hosted_dir": str(INVOCATIONS_DIR.relative_to(ROOT)),
                            "operation": "denied-claims-review", "input": {"claim_ids": ["CLM-9003", "..."]},
                            "output": "ClaimReviewBatch {reviewed_at, reviews[]}", "knowledge": hra_rules()["doc_id"],
                            "deployed": (existing.get("agents", {}).get("invocations") or {}).get("deployed") or {"version": None, "status": "not deployed"}},
            "responses_skills": {"agent_name": SKILLS_AGENT, "protocol": "responses", "hosted_dir": str(SKILLS_HOST_DIR.relative_to(ROOT)),
                                 "skills": skills, "toolbox": env.get("TOOLBOX_NAME") or None, "toolbox_mcp_url_set": bool(env.get("TOOLBOX_MCP_URL")),
                                 "deployed": (existing.get("agents", {}).get("responses_skills") or {}).get("deployed") or {"version": None, "status": "not deployed"}},
        },
        "model": lab_helpers.pick_model(env), "protocol_comparison": PROTOCOLS, "vendored": counts or existing.get("vendored", {}),
        "sample_run": existing.get("sample_run"), "lab1_agent": lab1.get("agent_name"), "built_at": lab_helpers.now_iso(),
    }
    foundry_env.save_artifact(RECORD, record)
    log(f"wrote {RECORD.relative_to(LABS_DIR)} (agents {INVOCATIONS_AGENT}, {SKILLS_AGENT}; skills {skills})")
    return record


def vendor_into(folder: Path) -> dict[str, int]:
    """common/ and data/ into a hosted folder that has no prepare.py of its own."""
    counts = {}
    for name in ("common", "data"):
        target = folder / name
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(ROOT / name, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".*_selftest"), dirs_exist_ok=True)
        counts[name] = sum(1 for p in target.rglob("*") if p.is_file())
        log(f"vendored {name}/ into {folder.name}/ ({counts[name]} files)")
    return counts


# %% Local server (same lifecycle as Labs 1 and 3, parameterised by folder)
class HostedProcess:
    def __init__(self, hosted_dir: Path, port: int = PORT, extra_env: dict | None = None):
        self.hosted_dir, self.port, self.extra_env = hosted_dir, port, extra_env or {}
        self.log_path = ARTIFACTS / f"{hosted_dir.name}_local.log"
        self.process: subprocess.Popen | None = None

    def start(self, timeout: float = 120.0) -> "HostedProcess":
        env = {**os.environ, **foundry_env.load_env(), **self.extra_env, "VIA_HOSTED_PORT": str(self.port), "PYTHONUNBUFFERED": "1"}
        handle = self.log_path.open("w", encoding="utf-8")
        self.process = subprocess.Popen([sys.executable, str(self.hosted_dir / "main.py")], cwd=str(self.hosted_dir), env=env,
                                        stdout=handle, stderr=subprocess.STDOUT)
        log(f"started {self.hosted_dir.name}/main.py (pid {self.process.pid}) on port {self.port}; log -> {self.log_path.relative_to(LABS_DIR)}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise SystemExit(f"[{LAB}] main.py exited early (code {self.process.returncode}). Read {self.log_path}")
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
            log(f"stopped {self.hosted_dir.name}/main.py")


# %% Calling the Invocations protocol
def call_invocations(base: str, claim_ids: list[str]) -> tuple[list[dict], str]:
    """POST the batch. Body per the base repo README: {"message": "<text>"}; we put the JSON request in the text."""
    test_local = lab_helpers.load_lab_module(f"{LAB_DIR.name}/hosted-invocations/test_local.py")
    import httpx

    body = {"message": json.dumps({"claim_ids": claim_ids})}
    for path in test_local.PATH_CANDIDATES:                   # VERIFY: the served path (see test_local.py)
        response = httpx.post(f"{base.rstrip('/')}{path}", json=body, timeout=180.0)
        if response.status_code == 404:
            continue
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        return test_local.extract_reviews(payload), path
    raise SystemExit(f"[{LAB}] no invocations path answered; set VIA_INVOCATIONS_PATH")


def save_reviews(reviews: list[dict], source: str) -> None:
    for review in reviews:
        path = REVIEWS_DIR / f"{review.get('claim_id', 'unknown')}.json"
        foundry_env.save_artifact(path, json.loads(guardrails.redact_pii(json.dumps({**review, "source": source}, default=str))))
    log(f"wrote {len(reviews)} packets to {REVIEWS_DIR.relative_to(LABS_DIR)}/ ({source})")


# %% demo(): the Invocations agent, one batch
def demo(base: str | None = None, *, offline: bool = False, claim_ids: list[str] = BATCH) -> dict:
    if offline:
        reviews, source, path = review_claims(claim_ids), "offline (claims_review.py, no model)", None
    else:
        server = None
        if base is None:
            server = HostedProcess(INVOCATIONS_DIR).start()
            base = LOCAL_BASE
        try:
            reviews, path = call_invocations(base, claim_ids)
        finally:
            if server:
                server.stop()
        source = f"local {base}{path}"
    for review in reviews:
        line = f"{review.get('claim_id')}: {review.get('status')} -> {review.get('review')}"
        if review.get("participant_explanation"):
            line += f"\n[{LAB}]     {review['participant_explanation']}"
        print(f"[{LAB}] {line}")
    save_reviews(reviews, source)
    record = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.exists() else build(vendor=False)
    record["sample_run"] = {"source": source, "claim_ids": claim_ids, "reviews": len(reviews),
                            "denied_with_fix": [r["claim_id"] for r in reviews if r.get("review") == "resubmit"],
                            "denied_no_fix": [r["claim_id"] for r in reviews if r.get("review") == "no_fix"], "at": lab_helpers.now_iso()}
    foundry_env.save_artifact(RECORD, record)
    return record["sample_run"]


# %% skills_demo(): the Responses agent with the bundled skill answers S2
def skills_demo(base: str | None = None) -> str:
    lab1 = lab_helpers.load_lab_module("lab1-hosted-agent-basics/lab1_hosted_basics.py")   # reuse post_responses()
    server = None
    if base is None:
        server = HostedProcess(SKILLS_HOST_DIR).start()
        base = LOCAL_BASE
    try:
        print(f"[{LAB}] participant> {S2_QUESTION}")
        result = lab1.post_responses(base, S2_QUESTION)
    finally:
        if server:
            server.stop()
    text = result["text"]
    report = lab_helpers.guardrail_report(text)
    print(f"[{LAB}] {SKILLS_AGENT}> {text}\n[{LAB}] checks: {lab_helpers.fmt_checks(report)}")
    if "KB-ACC-001" not in text:
        log("WARNING: the answer does not cite [KB-ACC-001]; check the server log for the read_skill call")
    foundry_env.save_artifact(ARTIFACTS / "skills_transcript.md",
                              f"# Stretch 6 skills transcript\n\n**Participant:** {S2_QUESTION}\n\n**{SKILLS_AGENT}:** {guardrails.redact_pii(text)}\n")
    return text


# %% Deploy both (invocations and responses protocols)
def deploy_commands(env: dict | None = None) -> str:
    env = env or foundry_env.load_env()
    project_id = env.get("PROJECT_RESOURCE_ID") or "<set PROJECT_RESOURCE_ID in .env>"
    model = lab_helpers.pick_model(env)
    lines = ["azd config set auth.useAzCliAuth true && azd extension install azure.ai.agents", ""]
    for folder, name, protocol in ((INVOCATIONS_DIR, INVOCATIONS_AGENT, "invocations"), (SKILLS_HOST_DIR, SKILLS_AGENT, "responses")):
        lines += [f"cd {folder.relative_to(ROOT)}",
                  f"azd ai agent init --no-prompt --project-id \"{project_id}\" --agent-name {name} \\",
                  f"   --model-deployment {model} --protocol {protocol} --deploy-mode code --runtime python_3_14 \\",
                  "   --entry-point main.py --dep-resolution remote_build"]
        if protocol == "responses":
            lines.append("# env on the hosted agent: SKILL_NAMES=hra-reimbursement-rules  TOOLBOX_NAME=<toolbox>  TOOLBOX_MCP_URL=<mcp url>  (preview)")
        lines += ["azd up", ""]
    return "\n".join(lines)


# %% YOUR TURN (10 min): nightly denials. Change BATCH to every denied claim id in data/hra_accounts.json
# (via_data.get_hra_account(pid)["claims_summary"]["denied_claim_ids"] for each participant) and run the batch.
# That is the shape of a Routine or a pipeline step: no chat, one request, one JSON answer per claim.

# %% YOUR TURN (10 min): a second skill. Write skills/debit-card-faq/SKILL.md from data/knowledge/debit-card-faq.md,
# re-run build(), start the skills agent and ask "my card was declined at the pharmacy". Watch read_skill in the log.


# %% Main
def main(args: argparse.Namespace) -> None:
    if args.deploy:
        build(vendor=not args.no_vendor)
        print(f"\n[{LAB}] deploy from source (two agents, two protocols):\n{deploy_commands()}")
        return
    log(f"data check: {via_data.get_claim_status('CLM-9003').get('status')} claim CLM-9003 is in data/hra_accounts.json")
    build(vendor=not args.no_vendor)
    if args.skip_demo:
        return
    demo(args.base, offline=args.offline)
    if args.skills_demo:
        skills_demo(args.base)
    log("done. Checkpoint: paste the CLM-9003 participant_explanation and the protocol comparison row you found most useful.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true", help="no model: deterministic review packets only")
    parser.add_argument("--skills-demo", action="store_true", help="also run the Responses + Skills agent on S2")
    parser.add_argument("--skip-demo", action="store_true")
    parser.add_argument("--no-vendor", action="store_true")
    parser.add_argument("--base", default=None, help="talk to an already running server")
    parser.add_argument("--deploy", action="store_true")
    main(parser.parse_args())
