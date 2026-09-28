---
title: "foundry-hosted-agents-labs: wire per-stage model selection in lab3 hosted/benefits_specialists.py"
labels: enhancement, foundry-hosted-agents-labs
---

## Context

Part of the Foundry Hosted Agents labs merge (`foundry-hosted-agents-labs/`). Issues are
disabled on this repo, so this is filed as a drafted issue instead; open a real issue from this
file's content once issues are available, then delete this file.

## Gap

`.env.example` documents `BENEFITS_MODEL_INTAKE`, `BENEFITS_MODEL_SPECIALIST` and `BENEFITS_MODEL_HANDOFF` (added by
the labs merge PR) as the per-stage model overrides the workshop's Token Capital narrative talks
about ("route by stage" — cheap model for intake/handoff, stronger model only where the specialist
work needs it). Today `labs/lab3-hosted-multi-agent-handoff/hosted/main.py` and
`hosted/benefits_workflow.py` build every `FoundryChatClient` with a single `MODEL`
(`AZURE_AI_MODEL_DEPLOYMENT_NAME` / `FOUNDRY_MODEL`); the three `BENEFITS_MODEL_*` vars are not read
anywhere yet.

## Ask

- In `labs/lab3-hosted-multi-agent-handoff/hosted/benefits_specialists.py` (and wherever the intake /
  specialist / handoff agents are constructed), read `BENEFITS_MODEL_INTAKE`, `BENEFITS_MODEL_SPECIALIST`,
  `BENEFITS_MODEL_HANDOFF` with a fallback to the existing `AZURE_AI_MODEL_DEPLOYMENT_NAME` /
  `FOUNDRY_MODEL` when a stage-specific var is unset, so the lab keeps working with zero new
  config for anyone who does not set them.
- Update Lab 3's README / walkthrough notebook to show the three-tier setup as a YOUR TURN or demo
  step, and log which model each stage actually used (ties into the cost ledger, see
  `foundry-hosted-agents-labs-01-cost-ledger.md`, so per-stage cost becomes visible).
