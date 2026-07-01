# 🧩 Bring Your Own Use Case (BYOUC)

[← Back to main README](../README.md)

Have your own agent idea? Fill in the **Agentic Use Case Spec**, then let GitHub Copilot
scaffold the MVP — matching the patterns you learned in the workshop.

> 🧭 **New here?** Finish the [main README setup](../README.md#-getting-started) (venv, `az login`,
> repo-root `.env`, permissions) first — your generated agent reuses the same `.env` and Entra auth.

## Prerequisites

- Workshop environment ready: repo-root `.venv`, `pip install -r ../requirements.txt`, `az login`, repo-root `.env` filled in.
- GitHub Copilot in VS Code (**Plan** and **Agent** modes).

## Use it in 3 steps

| Step | What you do | What Copilot does |
|------|-------------|-------------------|
| **Fill** | Complete the spec (~10 min): inputs, steps, outputs, rules, test data | — |
| **Plan** | Paste the spec into Copilot **Plan mode** (prompt is in the spec) | Drafts folder layout, modules, agent + workflow design |
| **Build** | Paste the plan into Copilot **Agent mode** (prompt is in the spec) | Implements code, tests, and docs in repo style |

## Get started

- 📄 **Markdown** → [Agentic_UseCase_Spec.md](Agentic_UseCase_Spec.md) — includes a worked example (Loan Application Risk Reviewer)
- 📝 **Word** → [Agentic_UseCase_Spec.docx](Agentic_UseCase_Spec.docx)

## 🧭 Troubleshooting

| Issue | Solution |
|-------|----------|
| **401 / 403 from the generated agent** | Role propagation — RBAC takes **5–15 min**. Wait and retry; run [setup-permissions](../README.md#step-6-required-azure-rbac-roles--storage-access) if needed. |
| **Missing config** | Your agent reads the **repo-root** `.env`; keep `AZURE_OPENAI_API_KEY` blank (Entra `az login`). |
