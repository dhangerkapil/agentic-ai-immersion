"""Lab 4: the evaluation gate.

Runs on: the learner workstation and the CI runner (the evaluate job in .github/workflows/agent-ci.yml).
Goal     Turn artifacts/lab4/eval_results.jsonl into a pass/fail decision the pipeline can act on. Fails (exit 1)
         on ANY no_recommendation violation or PII leak; warns (or fails with --strict) when the judge means fall
         under the thresholds. Optionally runs lab4_operate.py first (--run) so CI always judges fresh output.
Inputs   artifacts/lab4/eval_results.jsonl (from lab4_operate.py)
Outputs  artifacts/lab4/gate_result.json, GitHub step summary when GITHUB_STEP_SUMMARY is set
Run:  python eval_gate.py [--run] [--target local|deployed] [--limit N] [--skip-judges] [--strict]
                          [--min-groundedness 3.0] [--min-relevance 3.0]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABS_DIR = HERE.parent
ROOT = LABS_DIR.parent
sys.path.insert(0, str(ROOT))
RESULTS_PATH = LABS_DIR / "artifacts" / "lab4" / "eval_results.jsonl"
GATE_PATH = LABS_DIR / "artifacts" / "lab4" / "gate_result.json"
LAB4_SCRIPT = HERE / "lab4_operate.py"
LAB = "lab4-gate"


def run_evaluation(target: str, limit: int | None, skip_judges: bool) -> None:
    """Re-run the Lab 4 evaluation in a subprocess so the gate always judges fresh output in CI."""
    command = [sys.executable, str(LAB4_SCRIPT), "--target", target]
    if limit:
        command += ["--limit", str(limit)]
    if skip_judges:
        command.append("--skip-judges")
    print(f"[{LAB}] running: {' '.join(command)}")
    completed = subprocess.run(command, cwd=str(HERE), check=False)
    if completed.returncode != 0:
        sys.exit(f"[{LAB}] evaluation run failed with exit code {completed.returncode}")


def load_results(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"[{LAB}] missing {path.relative_to(LABS_DIR)}. Run: python lab4_operate.py, or eval_gate.py --run")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _mean(values: list) -> float | None:
    clean = [float(v) for v in values if isinstance(v, (int, float))]
    return round(sum(clean) / len(clean), 2) if clean else None


def evaluate_gate(results: list[dict], *, min_groundedness: float, min_relevance: float, strict: bool) -> dict:
    scores = [row.get("scores", {}) for row in results]
    violations = [row for row in results if row.get("scores", {}).get("no_recommendation_result") == "fail"]
    leaks = [row for row in results if row.get("scores", {}).get("pii_leak_result") == "fail"]
    groundedness = _mean([s.get("groundedness") for s in scores])
    relevance = _mean([s.get("relevance") for s in scores])
    hard_failures = [f"no_recommendation violation: {row['query'][:80]}" for row in violations]
    hard_failures += [f"pii leak: {row['query'][:80]}" for row in leaks]
    warnings = []
    if not results:
        hard_failures.append("no results to judge")
    if groundedness is not None and groundedness < min_groundedness:
        warnings.append(f"groundedness mean {groundedness} below {min_groundedness}")
    if relevance is not None and relevance < min_relevance:
        warnings.append(f"relevance mean {relevance} below {min_relevance}")
    failures = hard_failures + (warnings if strict else [])
    return {"passed": not failures, "questions": len(results), "no_recommendation_violations": len(violations),
            "pii_leaks": len(leaks), "groundedness_mean": groundedness, "relevance_mean": relevance,
            "thresholds": {"min_groundedness": min_groundedness, "min_relevance": min_relevance, "strict": strict},
            "failures": failures, "warnings": [] if strict else warnings,
            "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": str(RESULTS_PATH.relative_to(LABS_DIR))}


def write_outputs(gate: dict) -> None:
    GATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GATE_PATH.write_text(json.dumps(gate, indent=2), encoding="utf-8")
    lines = [f"## Eval gate: {'PASS' if gate['passed'] else 'FAIL'}", "", "| Metric | Value |", "|---|---|"]
    lines += [f"| {key} | {gate[key]} |" for key in ("questions", "no_recommendation_violations", "pii_leaks", "groundedness_mean", "relevance_mean")]
    lines += [""] + [f"- FAIL: {item}" for item in gate["failures"]] + [f"- WARN: {item}" for item in gate["warnings"]]
    summary = "\n".join(lines) + "\n"
    print(summary)
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with Path(step_summary).open("a", encoding="utf-8") as handle:
            handle.write(summary)
    print(f"[{LAB}] wrote {GATE_PATH.relative_to(LABS_DIR)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run lab4_operate.py first")
    parser.add_argument("--target", choices=["local", "deployed"], default="local")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--skip-judges", action="store_true")
    parser.add_argument("--strict", action="store_true", help="treat judge thresholds as failures, not warnings")
    parser.add_argument("--min-groundedness", type=float, default=3.0)
    parser.add_argument("--min-relevance", type=float, default=3.0)
    parser.add_argument("--results", type=Path, default=RESULTS_PATH)
    args = parser.parse_args()
    if args.run:
        run_evaluation(args.target, args.limit, args.skip_judges)
    gate = evaluate_gate(load_results(args.results), min_groundedness=args.min_groundedness,
                         min_relevance=args.min_relevance, strict=args.strict)
    write_outputs(gate)
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
