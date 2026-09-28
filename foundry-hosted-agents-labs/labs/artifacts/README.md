# Artifacts: the chain between labs

Every lab writes its checkpoint here and the next lab starts by reading it. Nothing in this folder is a secret
(agent names and versions, endpoints already in `.env`, synthetic transcripts passed through `redact_pii`). If a
file is missing, the lab stops with the one command that recreates it: `python catch_up.py --through N`.

| Folder | Written by | Files | Read by |
|---|---|---|---|
| `lab1/` | `lab1-hosted-agent-basics/lab1_hosted_basics.py` | `hosted.json` (agent name, version, endpoint, model), `transcripts.md` | Lab 2 (chain check), `catch_up.py` |
| `lab2/` | `lab2-hosted-knowledge-sessions/lab2_hosted_knowledge.py` (+ `knowledge_base.py`) | `knowledge.json` (indexes, knowledge sources, kb name, MCP endpoint, project connection), `hosted.json` (v2 record, azd commands, last demo), `sessions/<id>.json` (session map, file store), `message_store/` (history, file fallback), `transcripts.md` (kill-and-restart transcript with the continuity check) | Lab 3 (knowledge tool), Lab 4 (target, `BENEFITS_KB_MCP_URL`), Stretch 5 (MCPTool connection), CI deploy job |
| `lab3/` | `lab3-hosted-multi-agent-handoff/lab3_hosted_multi_agent.py` | `hosted.json` (benefits-triage-hosted), `handoff_packets/S1..S3.json` | Lab 4 (chain check) |
| `lab4/` | `lab4-operate-hosted-agents/lab4_operate.py`, `eval_gate.py`, `promote.py` | `operate.json` (target, tracing, evaluators), `eval_results.jsonl`, `eval_report.md`, `pipeline.md` (generated from `agent-ci.yml`), `gate_result.json`, `promotions.jsonl` | `promote.py` (gate), CI evaluate job (uploads), Stretch 5 (none) |
| `stretch5/` | `stretch5-prompt-agents-and-workflows/stretch5_prompt_agents.py` | `agents.json` (six prompt agents + workflow agent versions), `workflow.yaml` (deployed definition), `handoff_packets/S1.json` | `hosted_tool_snippet.py` (workflow name for the hosted agent) |
| `stretch6/` | `stretch6-invocations-toolbox-skills/stretch6_invocations.py` | `invocations.json` | none |

## Rules
- Labs write with `foundry_env.save_artifact` and read with `lab_helpers.require_artifact(lab, name, through, caller)`, which prints the catch-up command when the file is missing.
- Rerunning a lab creates new agent versions and overwrites the JSON record; earlier versions stay in the portal.
- `sessions/` and `message_store/` are the file-store fallbacks. When `BENEFITS_REDIS_URL` is set nothing is written here for them: the state is in Redis, which is the point of Lab 2.
- Delete this folder's contents (keep this README) to start the day clean. `git status` should show only this README tracked.
