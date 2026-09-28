---
title: "wtw-foundry-hosted-agents-labs: add the four Token Capital \"YOUR TURN\" items to Labs 2, 3, 4 READMEs"
labels: enhancement, wtw-foundry-hosted-agents-labs
---

## Context

Part of the WTW Foundry Hosted Agents labs merge (`wtw-foundry-hosted-agents-labs/`). Issues are
disabled on this repo, so this is filed as a drafted issue instead; open a real issue from this
file's content once issues are available, then delete this file.

## Gap

`WORKSHOP-OUTLINE-TOKEN-CAPITAL-TTE.md` (source planning doc, not copied into the repo) specifies
four Token-Capital-themed "YOUR TURN" exercises that were never folded into the lab READMEs /
walkthrough notebooks themselves. They depend on `common/cost_ledger.py` and
`labs/artifacts/targets.md` (see the two sibling issues), so they should land after those.

## Ask

Add these four exercises, verbatim in spirit, to the READMEs/notebooks below:

1. **Lab 2 — detect the valley.** Edit `last_reviewed` on one knowledge doc to a date before today
   and change one accepted-document line; do not rebuild; ask the question; then rebuild and ask
   again. Write down which answer a participant would have received. Ledger: append S1 rows for v2
   with and without knowledge; note prompt tokens per turn.
2. **Lab 3 — the price of governance.** Run S1 through Lab 1/Section 2's single agent and through
   the Lab 3 workflow; record tokens, api calls, wall time and gate pass for both in the ledger;
   write one sentence on why the workflow is still worth it here.
3. **Lab 3 — route by stage.** Set the intake and specialist model to `gpt-5.4-nano` or `-mini` and
   the packet writer to `gpt-5.4` via env (this is what `wtw-labs-03-per-stage-model-selection.md`
   wires up); rerun S1; compare the ledger row and the compliance flags with the all-mini run.
   Cheaper only counts if the gate still passes.
4. **Lab 4 — cost per outcome and climb once.** From spans and the ledger, compute `est_cost` per
   gate-passing scenario for the Lab 3 agent and workflow; write both against the Lab 1/Section 1
   cost target in `artifacts/targets.md`; state whether you are at, above or below the peak. Then:
   pick the lowest-scoring golden question, change one instruction, rerun `--limit 8 --skip-judges`,
   redeploy as a new version if the gate passes, and record the before/after in the ledger. If it
   did not improve, roll back and record that too.
