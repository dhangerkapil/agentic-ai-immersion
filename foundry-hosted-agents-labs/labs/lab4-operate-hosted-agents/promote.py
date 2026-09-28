"""Lab 4: promote the hosted agent between environments.

Runs on: the learner workstation (the pipeline does the same through workflow_dispatch).
Goal     dev -> test -> prod with one command per hop. A promotion is: the eval gate passed, a git tag marks the
         exact source, and azd deploys that tag with the target environment's values. Default is a dry run that
         prints the commands; --execute runs them from labs/lab2-hosted-knowledge-sessions/hosted.
Inputs   artifacts/lab4/gate_result.json, envs/.env.<target>.example
Outputs  artifacts/lab4/promotions.jsonl (one line per promotion or dry run)
Run:  python promote.py --to test [--execute] [--tag benefits-concierge-test-2026.10.06]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABS_DIR = HERE.parent
ROOT = LABS_DIR.parent
GATE_PATH = LABS_DIR / "artifacts" / "lab4" / "gate_result.json"
PROMOTIONS_PATH = LABS_DIR / "artifacts" / "lab4" / "promotions.jsonl"
HOSTED_DIR = LABS_DIR / "lab2-hosted-knowledge-sessions" / "hosted"
ENVS_DIR = HERE / "envs"
ORDER = ["dev", "test", "prod"]
LAB = "lab4-promote"


def check_gate() -> dict:
    if not GATE_PATH.exists():
        sys.exit(f"[{LAB}] no gate result. Run: python eval_gate.py --run   (from labs/lab4-operate-hosted-agents)")
    gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
    if not gate.get("passed"):
        sys.exit(f"[{LAB}] gate FAILED at {gate.get('evaluated_at')}: {gate.get('failures')}. Fix, re-run the gate, then promote.")
    print(f"[{LAB}] gate passed at {gate['evaluated_at']}: {gate['questions']} questions, 0 violations, 0 leaks")
    return gate


def commands(target: str, tag: str) -> list[list[str]]:
    env_file = ENVS_DIR / f".env.{target}.example"
    if not env_file.exists():
        sys.exit(f"[{LAB}] missing {env_file}")
    return [
        ["git", "tag", "-f", tag],
        ["cp", str(env_file), str(ROOT / ".env")],          # then fill the endpoint values for the target
        [sys.executable, str(HOSTED_DIR / "prepare.py")],
        ["azd", "env", "select", f"benefits-concierge-{target}"],
        ["azd", "up", "--no-prompt"],
        [sys.executable, str(HOSTED_DIR / "test_local.py"), "--deployed"],
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--to", choices=ORDER, required=True, help="target environment")
    parser.add_argument("--execute", action="store_true", help="run the commands (default: print them)")
    parser.add_argument("--tag", default=None, help="git tag to create for this promotion")
    args = parser.parse_args()
    source = ORDER[max(ORDER.index(args.to) - 1, 0)]
    tag = args.tag or f"benefits-concierge-{args.to}-{datetime.now(timezone.utc).strftime('%Y.%m.%d-%H%M')}"
    gate = check_gate()
    print(f"[{LAB}] promoting {source} -> {args.to} as {tag} ({'EXECUTE' if args.execute else 'dry run'})")
    outcome = "dry-run"
    for command in commands(args.to, tag):
        print(f"[{LAB}]   $ {' '.join(command)}")
        if args.execute:
            completed = subprocess.run(command, cwd=str(HOSTED_DIR), check=False)
            if completed.returncode != 0:
                outcome = f"failed at: {' '.join(command)}"
                print(f"[{LAB}] {outcome}")
                break
    else:
        outcome = "promoted" if args.execute else "dry-run"
    PROMOTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROMOTIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "from": source, "to": args.to,
                                 "tag": tag, "gate_evaluated_at": gate["evaluated_at"], "outcome": outcome}) + "\n")
    print(f"[{LAB}] recorded in {PROMOTIONS_PATH.relative_to(LABS_DIR)}")
    return 0 if outcome in {"promoted", "dry-run"} else 1


if __name__ == "__main__":
    sys.exit(main())
