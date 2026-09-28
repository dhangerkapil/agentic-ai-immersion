---
title: "foundry-hosted-agents-labs: add labs/artifacts/targets.md template"
labels: enhancement, foundry-hosted-agents-labs
---

## Context

Part of the Foundry Hosted Agents labs merge (`foundry-hosted-agents-labs/`). Issues are
disabled on this repo, so this is filed as a drafted issue instead; open a real issue from this
file's content once issues are available, then delete this file.

## Gap

`labs/artifacts/` collects per-lab outputs (`hosted.json`, `transcripts.md`, logs) but there is no
place for a learner to write down what "good" looks like before they start measuring against it.

## Ask

Add a `labs/artifacts/targets.md` template with three rows a learner fills in before Lab 2:

| Dimension | Target | Actual | Notes |
|---|---|---|---|
| Quality | e.g. Groundedness >= 4/5 on S1-S3 | | |
| Cost | e.g. est_cost per scenario <= $X | | |
| Speed | e.g. wall time per scenario <= Ns | | |

The template should note that Cost/Speed rows are only meaningful once
`common/cost_ledger.py` (see sibling issue `foundry-hosted-agents-labs-01-cost-ledger.md`) is writing real numbers,
and should point at `labs/artifacts/cost_ledger.jsonl` as the source of truth once it exists.
