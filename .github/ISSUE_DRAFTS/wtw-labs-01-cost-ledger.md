---
title: "wtw-foundry-hosted-agents-labs: add common/cost_ledger.py + per-run ledger entries"
labels: enhancement, wtw-foundry-hosted-agents-labs
---

## Context

Part of the WTW Foundry Hosted Agents labs merge (`wtw-foundry-hosted-agents-labs/`). Issues are
disabled on this repo, so this is filed as a drafted issue instead; open a real issue from this
file's content once issues are available, then delete this file.

## Gap

There is no cost/telemetry ledger yet. Each lab driver (`lab1_hosted_basics.py` .. `lab4_operate.py`,
the stretch drivers) runs its demo scenarios but does not record token/cost/timing data anywhere.

## Ask

- Add `common/cost_ledger.py` with an append-only JSONL writer.
- Call it from each lab driver after every scenario run, writing one line per run to
  `labs/artifacts/cost_ledger.jsonl` with at least: `section`, `scenario`, `agent_version`,
  `input_tokens`, `cached_tokens`, `output_tokens`, `api_calls`, `wall_time_seconds`, `gate_pass`,
  `est_cost` (or the literal string `"unknown"` when the value can't be computed).
- **Never** convert missing/unavailable telemetry to `0` — always write `"unknown"` so downstream
  consumers can distinguish "zero cost" from "not measured".

## Why it matters

This is what lets the Token Capital "cost per outcome" exercises (Labs 2-4 YOUR TURN items, see the
sibling issue `wtw-labs-04-token-capital-your-turn.md`) actually compute real numbers instead of
hand-waving.
