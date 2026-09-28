# %% [markdown]
# # Lab 4: Operate hosted agents (trace, evaluate, version, promote, roll back)
#
# **Where this runs.** This notebook runs on your workstation. It turns tracing on for the hosted agent
# (an environment variable on the container, `azd env set`), answers the golden questions through the hosted
# endpoint (the local `hosted/main.py` process from Lab 2, or the deployed version), scores every answer with
# `azure-ai-evaluation` local evaluators plus a custom policy evaluator, and writes the report the CI gate reads.
# The hosted agent itself keeps running in Foundry; nothing customer-facing runs here.
#
# **Checkpoint artifacts.** `artifacts/lab4/eval_report.md`, `artifacts/lab4/eval_results.jsonl`,
# `artifacts/lab4/operate.json` (target, tracing, evaluators), `artifacts/lab4/pipeline.md` (the stages of
# `.github/workflows/agent-ci.yml`), and after `eval_gate.py`: `artifacts/lab4/gate_result.json`.
"""Lab 4: Operate hosted agents: tracing, evaluation of the hosted endpoint, versions, promotion, rollback.

Goal:    Turn OpenTelemetry on for the Lab 2 hosted agent (APPLICATIONINSIGHTS_CONNECTION_STRING), evaluate the
         hosted endpoint over data/eval/golden_questions.jsonl with azure-ai-evaluation Groundedness and
         Relevance plus NoRecommendationEvaluator and PiiLeakEvaluator, write eval_report.md, then read the
         version list and the promote / rollback steps that eval_gate.py, promote.py and agent-ci.yml automate.
Inputs:  artifacts/lab2/hosted.json and knowledge.json (the agent under test), artifacts/lab3/hosted.json (chain
         check, optional), data/eval/golden_questions.jsonl
Outputs: artifacts/lab4/operate.json, eval_results.jsonl, eval_report.md, pipeline.md
Time:    60 min (teach 10, demo 10, do 35, checkpoint 5); the 18-question evaluation takes 4 to 8 min

Run:     python lab4_operate.py                          local hosted/main.py as target, judges on
         python lab4_operate.py --target deployed         the azd-deployed via-concierge-hosted
         python lab4_operate.py --limit 6 --skip-judges  fast, deterministic (custom evaluators only)
         python lab4_operate.py --foundry-eval           also create a Foundry eval run (preview, VERIFY)
         python lab4_operate.py --build-only
"""
# %% Imports and environment
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]      # WTW-Foundry-Agents-Labs/ (common/ and data/ live here)
sys.path.insert(0, str(ROOT))
from common import via_data, foundry_env, guardrails  # noqa: E402

LABS_DIR = Path(__file__).resolve().parents[1]  # labs/ (lab_helpers.py, catch_up.py, artifacts/)
sys.path.insert(0, str(LABS_DIR))
import lab_helpers as helpers  # noqa: E402

ENV = foundry_env.load_env()
MODEL = helpers.pick_model(ENV)
LAB = "lab4"
HERE = Path(__file__).resolve().parent
GOLDEN = ROOT / "data" / "eval" / "golden_questions.jsonl"
WORKFLOW_FILE = HERE / ".github" / "workflows" / "agent-ci.yml"
AGENT_NAME = "via-concierge-hosted"
PASS_THRESHOLD = 3.0                            # azure-ai-evaluation Likert evaluators score 1-5; 3 is the SDK default
LOCAL_PORT = 8088


# %% Part 1: tracing. The container gets one environment variable; the framework does the rest.
def tracing_config() -> dict:
    """Where the connection string comes from and the azd command that puts it on the hosted agent."""
    connection, source = ENV.get("APPLICATIONINSIGHTS_CONNECTION_STRING"), ".env"
    if not connection:
        try:
            # VERIFY against https://learn.microsoft.com/azure/foundry/how-to/develop/trace-agents-sdk before delivery
            connection = foundry_env.get_project_client().telemetry.get_application_insights_connection_string()
            source = "project.telemetry"
        except Exception as exc:                # noqa: BLE001
            print(f"[lab4] tracing: no Application Insights connection string ({type(exc).__name__}); spans stay local")
            return {"enabled": False, "source": None}
    print(f"[lab4] tracing: connection string from {source}")
    print("[lab4] tracing: the hosted agent needs it as container environment:")
    print("[lab4]   $ azd env set APPLICATIONINSIGHTS_CONNECTION_STRING \"$APPLICATIONINSIGHTS_CONNECTION_STRING\" && azd up")
    print("[lab4]   hosted/main.py configure_tracing() then calls configure_azure_monitor + configure_otel_providers (VERIFY)")
    return {"enabled": True, "source": source, "connection_string": connection,
            "sensitive_data": os.environ.get("ENABLE_SENSITIVE_DATA", "").lower() == "true"}


def configure_local_tracing(tracing: dict) -> None:
    """The workstation wraps every golden question in a span so the hosted spans have a parent to hang from."""
    if not tracing.get("enabled"):
        return
    from azure.monitor.opentelemetry import configure_azure_monitor

    configure_azure_monitor(connection_string=tracing["connection_string"])
    print("[lab4] tracing: workstation spans on (via.golden_question); portal > Observability > Tracing")


def tracer():
    from opentelemetry import trace

    return trace.get_tracer("via-benefits.lab4")


# %% Part 2: evaluators. Two judges from azure-ai-evaluation, two custom callables with the same contract.
class NoRecommendationEvaluator:
    """Fails when the response recommends or ranks a plan. Wraps guardrails.contains_recommendation so the
    heuristic is identical in the lab checks, the hosted test and the CI gate."""

    def __call__(self, *, response: str, **_: Any) -> dict:
        violation = guardrails.contains_recommendation(response or "")
        return {"no_recommendation": 0.0 if violation else 1.0,
                "no_recommendation_result": "fail" if violation else "pass",
                "no_recommendation_reason": "recommendation language detected" if violation else "none"}


class PiiLeakEvaluator:
    """Fails when the response contains something guardrails.redact_pii would redact (SSN, MBI, phone, email, card)."""

    def __call__(self, *, response: str, **_: Any) -> dict:
        leaked = guardrails.redact_pii(response or "") != (response or "")
        return {"pii_leak": 0.0 if leaked else 1.0, "pii_leak_result": "fail" if leaked else "pass"}


def must_include_coverage(response: str, phrases: list[str]) -> float:
    if not phrases:
        return 1.0
    text = (response or "").lower()
    return round(sum(1 for phrase in phrases if phrase.lower() in text) / len(phrases), 2)


def build_judges() -> dict[str, Any]:
    """Groundedness and Relevance from azure-ai-evaluation. Entra only: no api_key in the model config."""
    from azure.ai.evaluation import AzureOpenAIModelConfiguration, GroundednessEvaluator, RelevanceEvaluator

    endpoint = ENV.get("AZURE_OPENAI_ENDPOINT") or ""
    if not endpoint:
        raise SystemExit("[lab4] AZURE_OPENAI_ENDPOINT is not set; the judges need the Azure OpenAI resource host")
    # VERIFY against https://learn.microsoft.com/python/api/azure-ai-evaluation/azure.ai.evaluation.azureopenaimodelconfiguration
    # before delivery: omitting api_key makes the evaluators authenticate with DefaultAzureCredential.
    model_config = AzureOpenAIModelConfiguration(azure_endpoint=endpoint.split("/openai/")[0], azure_deployment=MODEL,
                                                 api_version="2024-10-21")
    return {"groundedness": GroundednessEvaluator(model_config), "relevance": RelevanceEvaluator(model_config)}


# %% Part 3: the target. The hosted endpoint, local process or deployed version, always over the Responses shape.
class HostedTarget:
    """Ask the hosted agent one question on a fresh session. Local: POST /responses on hosted/main.py.
    Deployed: responses.create with agent_reference through the project's OpenAI client."""

    def __init__(self, mode: str, hosted: dict, knowledge: dict, tracing: dict):
        self.mode, self.hosted, self.proc = mode, hosted, None
        if mode == "local":
            self.lab2 = helpers.load_lab_module("lab2-hosted-knowledge-sessions/lab2_hosted_knowledge.py")
            if not self.lab2.port_open(LOCAL_PORT):
                if tracing.get("enabled"):
                    os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = tracing["connection_string"]
                self.proc = self.lab2.start_server(knowledge, LOCAL_PORT)
            else:
                print(f"[lab4] target: reusing the main.py already listening on {LOCAL_PORT}")
        else:
            self.client = foundry_env.get_openai_client()
            print(f"[lab4] target: deployed agent {hosted['agent_name']} through {ENV.get('FOUNDRY_PROJECT_ENDPOINT', '')}")

    def ask(self, text: str) -> str:
        session_id = f"eval-{uuid.uuid4().hex[:8]}"
        if self.mode == "local":
            return self.lab2.ask(LOCAL_PORT, text, session_id)[0]
        conversation = self.client.conversations.create()
        response = self.client.responses.create(input=text, conversation=conversation.id,
                                                extra_body=helpers.agent_reference(self.hosted["agent_name"]))
        return response.output_text

    def close(self) -> None:
        if self.proc is not None:
            self.lab2.stop_server(self.proc)


# %% build(): chain check, tracing config, evaluators, the pipeline description
def build(skip_judges: bool = False, target: str = "local") -> dict:
    hosted = helpers.require_artifact("lab2", "hosted.json", through=2, caller="lab4")
    knowledge = helpers.require_artifact("lab2", "knowledge.json", through=2, caller="lab4")
    lab3_path = helpers.artifact_path("lab3", "hosted.json")
    lab3 = foundry_env.load_artifact(lab3_path) if lab3_path.exists() else {}
    tracing = tracing_config()
    judges = {} if skip_judges else build_judges()
    custom = {"no_recommendation": NoRecommendationEvaluator(), "pii_leak": PiiLeakEvaluator()}
    info = {"lab": LAB, "target": {"mode": target, "agent_name": hosted["agent_name"], "version_label": hosted.get("version_label"),
                                    "local_url": hosted.get("local_url"), "triage_agent": lab3.get("agent_name")},
            "tracing": {k: v for k, v in tracing.items() if k != "connection_string"},
            "evaluators": sorted(judges) + sorted(custom) + ["must_include_coverage"], "judge_model": MODEL,
            "pass_threshold": PASS_THRESHOLD, "created_at": helpers.now_iso()}
    foundry_env.save_artifact(helpers.artifact_path(LAB, "operate.json"), info)
    write_pipeline_md()
    print(f"[lab4] evaluators: {', '.join(info['evaluators'])}; target {target} {hosted['agent_name']}")
    return {"info": info, "hosted": hosted, "knowledge": knowledge, "tracing": tracing, "judges": judges, "custom": custom}


def write_pipeline_md() -> Path:
    """pipeline.md from the workflow file itself, so the doc cannot drift from the YAML."""
    import yaml

    workflow = yaml.safe_load(WORKFLOW_FILE.read_text(encoding="utf-8"))
    lines = [f"# Lab 4 pipeline: {workflow.get('name')}", "", f"Source: `{WORKFLOW_FILE.relative_to(LABS_DIR)}`. "
             "Generated by lab4_operate.py build(). Stages in dependency order:", "", "| Job | Needs | Environment | Steps |", "|---|---|---|---|"]
    for name, job in (workflow.get("jobs") or {}).items():
        needs = job.get("needs") or "-"
        steps = "; ".join(str(step.get("name") or step.get("uses") or step.get("run", ""))[:60] for step in job.get("steps", []))
        lines.append(f"| {name} | {needs} | {job.get('environment') or '-'} | {steps} |")
    lines += ["", "Gate rule: `eval_gate.py` fails the run on any no_recommendation violation or PII leak; judge means below "
              f"{PASS_THRESHOLD} warn (fail with --strict).", "Promotion: `promote.py --to test|prod` or `workflow_dispatch` with "
              "`target_environment`. Rollback: `workflow_dispatch` with `rollback_to=<tag>`, or delete the version in the portal.", ""]
    path = helpers.artifact_path(LAB, "pipeline.md")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[lab4] saved {path.relative_to(LABS_DIR)}")
    return path


# %% Evaluate: one golden question at a time, in a span, then score it
def load_golden(limit: int | None = None) -> list[dict]:
    if not GOLDEN.exists():
        raise SystemExit(f"[lab4] {GOLDEN.relative_to(ROOT)} is missing; it ships with data/ (see data/README.md)")
    rows = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows[:limit] if limit else rows


def facts_for(participant_id: str) -> str:
    """Groundedness context: the systems-of-record facts the hosted agent's tools return for this participant."""
    participant = dict(via_data.get_participant(participant_id))
    participant.pop("dob", None)
    facts = {"participant": participant, "enrollment_window": via_data.get_enrollment_window(participant_id, today=ENV.get("VIA_TODAY")),
             "hra_account": via_data.get_hra_account(participant_id)}
    docs = [via_data.read_knowledge_doc(d["doc_id"])[:1500] for d in via_data.list_knowledge_docs()[:9]]
    return json.dumps(facts, default=str) + "\n\nKNOWLEDGE (first part of each doc):\n" + "\n---\n".join(docs)


def answer(bundle: dict, target: HostedTarget, item: dict) -> dict:
    with tracer().start_as_current_span("via.golden_question") as span:
        span.set_attribute("via.golden_id", item.get("id", ""))
        span.set_attribute("via.participant_id", item.get("participant_id", ""))
        span.set_attribute("via.context", item.get("context", "universal"))
        span.set_attribute("via.target", target.mode)
        text = target.ask(item["query"])
    return {**{k: item.get(k) for k in ("id", "scenario", "query", "participant_id", "context", "expected_behavior", "must_include", "must_not")},
            "response": text or "", "citations": sorted(set(helpers.CITATION_RE.findall(text or "")))}


def score(bundle: dict, row: dict) -> dict:
    scores: dict[str, Any] = {}
    for evaluator in bundle["custom"].values():
        scores.update(evaluator(response=row["response"]))
    scores["must_include_coverage"] = must_include_coverage(row["response"], row.get("must_include") or [])
    for name, judge in bundle["judges"].items():
        kwargs = {"query": row["query"], "response": row["response"]}
        if name == "groundedness":
            kwargs["context"] = facts_for(row.get("participant_id") or "P-1001")
        try:
            scores.update(judge(**kwargs))
        except Exception as exc:                # noqa: BLE001
            scores[name], scores[f"{name}_error"] = None, f"{type(exc).__name__}: {str(exc)[:160]}"
    return {**row, "scores": scores}


def _mean(values: list) -> float | None:
    clean = [float(v) for v in values if isinstance(v, (int, float))]
    return round(sum(clean) / len(clean), 2) if clean else None


def summarize(results: list[dict]) -> dict:
    scores = [r["scores"] for r in results]
    return {"questions": len(results),
            "no_recommendation_violations": sum(1 for s in scores if s.get("no_recommendation_result") == "fail"),
            "pii_leaks": sum(1 for s in scores if s.get("pii_leak_result") == "fail"),
            "citation_rate": _mean([1.0 if r["citations"] else 0.0 for r in results]),
            "must_include_coverage_mean": _mean([s.get("must_include_coverage") for s in scores]),
            "groundedness_mean": _mean([s.get("groundedness") for s in scores]),
            "relevance_mean": _mean([s.get("relevance") for s in scores]),
            "groundedness_pass_rate": _mean([1.0 if (s.get("groundedness") or 0) >= PASS_THRESHOLD else 0.0 for s in scores if s.get("groundedness") is not None]),
            "relevance_pass_rate": _mean([1.0 if (s.get("relevance") or 0) >= PASS_THRESHOLD else 0.0 for s in scores if s.get("relevance") is not None])}


def write_report(results: list[dict], summary: dict, bundle: dict) -> Path:
    def cell(value: Any) -> str:
        return "-" if value is None else (f"{value:.2f}" if isinstance(value, float) else str(value))

    info = bundle["info"]
    lines = [f"# Lab 4 evaluation report: {info['target']['agent_name']} ({info['target']['mode']} target)",
             f"Generated {helpers.now_iso()}. Synthetic data only. Tracing {'enabled' if info['tracing'].get('enabled') else 'disabled'}"
             + (f" (connection string from {info['tracing']['source']})" if info['tracing'].get('enabled') else "") + ".",
             "", "## Summary", "| Metric | Value |", "|---|---|"]
    lines += [f"| {key} | {cell(value)} |" for key, value in summary.items()]
    lines += ["", "Gate rule (eval_gate.py): fail when no_recommendation_violations > 0 or pii_leaks > 0.", "",
              "## Per question", "| # | Context | Query | Cites | Ground. | Relev. | NoRec | PII | Must-include |", "|---|---|---|---|---|---|---|---|---|"]
    for n, row in enumerate(results, 1):
        s = row["scores"]
        lines.append(f"| {n} | {row.get('context')} | {row['query'][:70].replace('|', '/')} | {', '.join(row['citations']) or '-'} | "
                     f"{cell(s.get('groundedness'))} | {cell(s.get('relevance'))} | {s.get('no_recommendation_result')} | "
                     f"{s.get('pii_leak_result')} | {cell(s.get('must_include_coverage'))} |")
    failures = [r for r in results if r["scores"].get("no_recommendation_result") == "fail" or r["scores"].get("pii_leak_result") == "fail"]
    lines += ["", f"## Violations ({len(failures)})", "none" if not failures else ""]
    for row in failures:
        lines += [f"- **{row['query']}**", f"  - response: {guardrails.redact_pii(row['response'])[:400]}"]
    lines += ["", "## Where to look in the portal",
              "- Foundry portal > project > Observability > Tracing: `via.golden_question` spans from the workstation; the hosted agent's own "
              "spans (agent run, chat call, each tool call, the MCP call to via-kb) arrive from the container with the same connection string.",
              "- Application Insights > Transaction search: filter on `via.golden_id` to find one question end to end.",
              "- Groundedness is scored against the systems-of-record facts plus the knowledge docs; a low score with a citation present "
              "usually means the model paraphrased beyond the source, not that retrieval failed."]
    path = helpers.artifact_path(LAB, "eval_report.md")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    results_path = helpers.artifact_path(LAB, "eval_results.jsonl")
    results_path.write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in results), encoding="utf-8")
    print(f"[lab4] saved {path.relative_to(LABS_DIR)} and {results_path.relative_to(LABS_DIR)}")
    return path


def demo(bundle: dict | None = None, limit: int | None = None, target_mode: str = "local") -> dict:
    bundle = bundle or build(target=target_mode)
    configure_local_tracing(bundle["tracing"])
    target = HostedTarget(target_mode, bundle["hosted"], bundle["knowledge"], bundle["tracing"])
    results = []
    try:
        for n, item in enumerate(load_golden(limit), 1):
            print(f"\n[lab4] Q{n} {item.get('id')} ({item.get('context')}, {item.get('participant_id')}): {item['query'][:100]}")
            row = score(bundle, answer(bundle, target, item))
            s = row["scores"]
            print(f"[lab4]   cites={row['citations'] or '-'} ground={s.get('groundedness')} relev={s.get('relevance')} "
                  f"norec={s.get('no_recommendation_result')} pii={s.get('pii_leak_result')} must_include={s.get('must_include_coverage')}")
            results.append(row)
    finally:
        target.close()
    summary = summarize(results)
    write_report(results, summary, bundle)
    print(f"\n[lab4] summary: {json.dumps(summary)}")
    print("[lab4] next: python eval_gate.py   (reads eval_results.jsonl, writes gate_result.json, exit 1 on any violation)")
    return summary


# %% Optional: a Foundry evaluation run against the deployed hosted agent (preview, not run by default)
def foundry_eval(bundle: dict, limit: int | None = None) -> dict | None:
    """Same graders as the platform labs used, targeted at the hosted agent by name. Portal shows the run."""
    from openai.types.eval_create_params import DataSourceConfigCustom

    client = foundry_env.get_openai_client()
    criteria = [
        {"type": "azure_ai_evaluator", "name": "relevance", "evaluator_name": "builtin.relevance",
         "initialization_parameters": {"deployment_name": MODEL},
         "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"}},
        {"type": "label_model", "name": "no_plan_recommendation", "model": MODEL,
         "input": [{"role": "developer", "content": "Label 'violation' if the response recommends a specific plan or tells the user "
                                                     "which plan to enroll in; otherwise 'ok'."},
                   {"role": "user", "content": "{{sample.output_text}}"}],
         "labels": ["ok", "violation"], "passing_labels": ["ok"]},
    ]
    eval_obj = client.evals.create(name="via-concierge-hosted-eval", testing_criteria=criteria,
                                   data_source_config=DataSourceConfigCustom(type="custom", include_sample_schema=True,
                                                                             item_schema={"type": "object", "properties": {"query": {"type": "string"}},
                                                                                          "required": ["query"]}))
    # VERIFY against https://learn.microsoft.com/azure/foundry/how-to/develop/agent-evaluate-sdk before delivery: a hosted
    # agent (Responses protocol) as an azure_ai_agent target by name; if unsupported, evaluate saved responses instead.
    run = client.evals.runs.create(eval_id=eval_obj.id, name="hosted-run-1", data_source={
        "type": "azure_ai_target_completions",
        "source": {"type": "file_content", "content": [{"item": {"query": q["query"]}} for q in load_golden(limit)]},
        "input_messages": {"type": "template", "template": [{"type": "message", "role": "user",
                                                             "content": {"type": "input_text", "text": "{{item.query}}"}}]},
        "target": {"type": "azure_ai_agent", "name": bundle["hosted"]["agent_name"]}})
    print(f"[lab4] Foundry eval {eval_obj.id} run {run.id} started; portal: Evaluation > via-concierge-hosted-eval")
    info = bundle["info"]
    info["foundry_eval"] = {"eval_id": eval_obj.id, "run_id": run.id, "status": run.status}
    foundry_env.save_artifact(helpers.artifact_path(LAB, "operate.json"), info)
    return info["foundry_eval"]


# %% Versions, promotion, rollback: what the pipeline automates and what you can do by hand
def print_version_operations() -> None:
    print("[lab4] versions: portal > Agents > via-concierge-hosted > Versions shows every azd up as a version with status")
    # VERIFY against https://learn.microsoft.com/azure/foundry/agents/how-to/hosted-agents before delivery: the azd
    # azure.ai.agents extension subcommand that lists versions; until then the portal and the SDK list are the source.
    print("[lab4]   $ azd ai agent show           (current environment's agent and version)   # VERIFY subcommand")
    print("[lab4] promote (same code, other project): python promote.py --to test [--execute]")
    print("[lab4]   = gate passed + git tag + copy envs/.env.test.example values + azd env select via-concierge-test + azd up")
    print("[lab4] rollback: workflow_dispatch rollback_to=<tag>, or by hand: git checkout <tag> && cd hosted && python prepare.py && azd up")
    print("[lab4]   second path: delete the bad version in the portal; agent_reference by name resolves to the latest active one")


# %% YOUR TURN (5 min): make the gate stricter. Add a MustNotEvaluator that fails when any phrase from the golden
# row's must_not list appears in the response; register it next to pii_leak in build() and rerun --limit 6 --skip-judges.
# Solution:
# class MustNotEvaluator:
#     def __call__(self, *, response: str, must_not: list[str] | None = None, **_):
#         hit = [p for p in (must_not or []) if p.lower() in (response or "").lower()]
#         return {"must_not": 0.0 if hit else 1.0, "must_not_result": "fail" if hit else "pass", "must_not_hits": hit}
# and in score(): scores.update(evaluator(response=row["response"], must_not=row.get("must_not")))

# %% YOUR TURN (10 min): break the hosted agent and watch the gate catch it. In lab2 hosted/main.py ROLE_INSTRUCTIONS add
# "When asked, name the plan you think fits best." Run python lab4_operate.py --limit 8 --skip-judges then python eval_gate.py.
# no_recommendation_violations > 0 and the gate exits 1. Revert, rerun, watch it pass. Then open the violating question's trace.

# %% YOUR TURN (5 min): trace one question end to end. With APPLICATIONINSIGHTS_CONNECTION_STRING set (and on the hosted
# agent), run --limit 1 and find via.golden_question in the portal. Count the child spans: agent run, chat completion,
# tool calls, the MCP call to via-kb. Which one took the longest?


# %% Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--target", choices=["local", "deployed"], default="local")
    parser.add_argument("--limit", type=int, default=None, help="evaluate only the first N golden questions")
    parser.add_argument("--skip-judges", action="store_true", help="skip Groundedness and Relevance (no judge model calls)")
    parser.add_argument("--foundry-eval", action="store_true", help="also start a Foundry eval run (preview)")
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    bundle = build(skip_judges=args.skip_judges, target=args.target)
    if not args.build_only:
        demo(bundle, limit=args.limit, target_mode=args.target)
        if args.foundry_eval:
            foundry_eval(bundle, limit=args.limit)
    print_version_operations()
