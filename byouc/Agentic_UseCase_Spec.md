# Agentic Use Case Spec

**Industry-Agnostic Template**
*Microsoft Azure AI Foundry × GitHub Copilot*

> Fill this out (~10 min). We paste it directly into GitHub Copilot to scaffold your agent MVP.

---

## Contents

1. [Use Case Summary](#1--use-case-summary)
2. [Input](#2--input)
3. [Agent Steps](#3--agent-steps)
4. [Output](#4--output)
5. [Agent Behavior Rules](#5--agent-behavior-rules)
6. [Domain Context](#6--domain-context)
7. [Preferences](#7--preferences)
8. [Synthetic Data Requirements](#8--synthetic-data-requirements)
9. [Step 1: Plan (GitHub Copilot)](#9--step-1-plan-github-copilot)
10. [Step 2: Implement & Test (GitHub Copilot)](#10--step-2-implement--test-github-copilot)
- [Example (reference)](#example-for-reference--do-not-copy)

---

## Your Spec — fill in below, then copy into the prompt

---

### 1 · Use Case Summary

**Use case name**
> \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**What does the agent do?** (2-3 sentences)
> \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**What problem does this solve?** (2-3 sentences)
> \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

### 2 · Input

| Question | Your Answer |
|---|---|
| What type of input? | |
| What does one input look like? | |
| How big is a typical input? | |

---

### 3 · Agent Steps

List the steps your agent should follow (these become the agent's tools).

1. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
2. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
3. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
4. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
5. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
6. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

### 4 · Output

| Question | Your Answer |
|---|---|
| What should the output look like? | |
| Categories or severity levels? | |

---

### 5 · Agent Behavior Rules

**MUST:**
1. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
2. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
3. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**MUST NOT:**
1. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
2. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
3. \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

### 6 · Domain Context

**Key terms** (5-10 domain terms the agent should know)
> \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_
> \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

**Agent persona**
> \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_

---

### 7 · Preferences

- [ ] Notebook — a single `.ipynb` with runnable cells (execute top-to-bottom)
- [ ] Web app — standalone Python app using Gradio, FastAPI, or similar

---

### 8 · Synthetic Data Requirements

> No customer data is used. GitHub Copilot will generate synthetic test data. Describe what the test data should contain so it can build realistic samples.

*Fill in the table below (1 test sample is enough — Copilot will generate it for you):*

| Attribute | Your Spec |
|---|---|
| Number of test samples | |
| Required fields / structure | |
| Realistic value ranges | |
| Edge cases to include (optional) | |
| File format | |

---

👇 *Look at the example below for reference*

---

## Example (for reference — do not copy)

### Use Case Summary

- **Use case name:** "Loan Application Risk Reviewer"
- **What it does:** "Reviews retail/SME loan applications against credit policy and flags exceptions with risk severity and remediation guidance"
- **Problem it solves:** "Credit analysts spend 45 min per application manually checking 30+ policy parameters — error rate is 12%"

### Input

- **Input type:** PDF + spreadsheet
- **What it looks like:** Loan application form with: applicant details, income docs, CIBIL/credit score, collateral details, existing liabilities, bank statements
- **Typical size:** 10–25 pages + 3–6 months statements

### Agent Steps

1. Extract applicant details, income, liabilities, and collateral from the application PDF
2. Parse bank statements and compute average monthly balance, salary credits, and EMI outflows
3. Calculate key ratios: FOIR (Fixed Obligation to Income Ratio), LTV (Loan-to-Value), DSCR (Debt Service Coverage Ratio)
4. Check each parameter against credit policy thresholds (e.g., FOIR ≤ 60%, LTV ≤ 80%)
5. Flag policy exceptions with severity (Critical / High / Medium) and cite the specific policy clause
6. Generate a risk summary with overall recommendation: Approve / Refer to Credit Committee / Decline

### Output

- **Output format:** Policy exception report: parameter, policy threshold, actual value, breach severity, clause reference. Overall: Approve / Refer / Decline
- **Severity levels:** Critical (auto-decline) / High (committee referral) / Medium (waiver possible) / Low (observation)

### Agent Behavior Rules

**MUST:**
- Cite the exact credit policy clause number for every exception flagged
- Calculate FOIR, LTV, DSCR from source data — never accept pre-calculated values without verification
- Flag if total exposure (existing + proposed) exceeds single-borrower limit

**MUST NOT:**
- Make a final credit decision — only recommend (Approve / Refer / Decline)
- Ignore missing income documentation — flag as Critical, never infer income
- Use external data sources — work only with the provided application package

### Domain Context

- **Key terms:** FOIR, LTV, DSCR, NPA, CIBIL score, EMI, collateral coverage, single-borrower limit
- **Agent persona:** "Senior credit analyst with 10 years in retail/SME lending"

### Synthetic Data Requirements

*Example — Loan Application Reviewer:*

| Attribute | Example Spec |
|---|---|
| Number of test samples | 1 synthetic loan application (clean / approvable happy-path) |
| Required fields / structure | Applicant: name, age, employment type (salaried/self-employed), monthly income, existing debt payments, FICO score (300-850). Loan: amount, tenure, type (home/personal/vehicle). Collateral: type, market value, forced-sale value. Bank statements: 6 months of transactions with salary credits, debt payment debits, average balance. |
| Realistic value ranges | Income: $3K-$15K/month. FICO: 670-800 (good), 580-669 (fair), <580 (poor). FOIR threshold: 60%. LTV threshold: 80%. Loan amounts: $50K-$2M. |
| Edge cases to include | None for the default sample — keep it a clean happy-path approval. |
| File format | JSON or structured dict (simulating parsed PDF output). Bank statements as list of transaction dicts. |

---

## 9 · Step 1: Plan (GitHub Copilot)

Once completed, paste your filled-out spec into GitHub Copilot **plan mode** (`Ctrl+Shift+I` → select **Plan**) with this wrapper prompt. This step creates a detailed plan — no code yet:

````text
You are a senior Python architect. Build a detailed implementation plan for a Microsoft Foundry agent MVP based on this use case spec.

IMPORTANT CONSTRAINTS — follow these exactly:
1. Create a NEW folder at the repository root level named after the use case (e.g., `my-use-case/`). All generated code MUST go in this folder.
2. Do NOT create a new virtual environment. Reuse the existing `.venv` at the repo root (already activated).
3. Before planning, study the existing code in this repository for reference patterns.
4. Match the SDK patterns, imports, auth, and .env loading conventions already used in this repo.

Tech stack (must use):
- Python 3.12
- azure-ai-projects SDK (AIProjectClient, PromptAgentDefinition, WorkflowAgentDefinition)
- OpenAI Responses API (responses.create with agent_reference + conversation)
- AzureCliCredential for authentication
- If user chose "Web app" in §7: build a web UI using Gradio, FastAPI, or similar framework
- If user chose "Notebook" in §7: create a single Jupyter notebook (.ipynb) with all code in runnable cells so the user can execute it top-to-bottom and see results inline
- FunctionTool definitions with Annotated type hints and Pydantic Field descriptions
- dotenv for environment variable loading (AI_FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME, TENANT_ID)

Plan deliverables — output a numbered plan covering:
a) Folder structure under the new root-level folder (e.g., `<use-case-name>/src/`, `<use-case-name>/tests/`, etc.)
b) Each Python module to create: filename, purpose, key classes/functions
c) Agent definitions: system prompt, tools (JSON schemas + implementations), model config
d) Workflow orchestration: sequential/parallel agent steps, data flow between agents
e) If Web app: UI framework choice, layout, input/output components, event handlers
   If Notebook: cell-by-cell breakdown — setup, agent creation, invocation, results display
f) Requirements: only list NEW packages not already in the repo's requirements.txt
g) .env variables needed (reuse existing ones where possible)

Use the synthetic test data from §8 to plan how the agent will be validated with a single happy-path test.

Do NOT write code yet — only produce the plan. I will implement in the next step.

<paste completed spec here>
````

**What Copilot will produce from the Plan step:**

| Your Spec Section | → | Copilot Output |
|---|---|---|
| Steps (§3) | → | Folder structure + module breakdown with tool schemas |
| Rules (§5) + Persona (§6) | → | System prompt design + agent orchestration plan |
| Input description (§2) | → | Sample input data for testing |
| Output format (§4) | → | Output formatting plan (web UI or notebook cells) |
| Domain terms (§6) | → | Canonical glossary for system prompt |
| Preferences (§7) | → | UI choice: Web app (Gradio/FastAPI) or Jupyter Notebook |
| Synthetic Data Spec (§8) | → | Plan synthetic test data generation based on user requirements |

---

## 10 · Step 2: Implement & Test End-to-End

After reviewing the plan from Step 1, switch to Copilot **agent mode** (`Ctrl+Shift+I` → select **Agent**) and paste this implementation prompt:

````text
You are a senior Python developer. Implement the plan from the previous step end-to-end.

CRITICAL INSTRUCTIONS:
1. All code goes in the folder created during planning (at the repo root level).
2. Use the existing `.venv` — do NOT create a new environment. Only install new packages if needed via `pip install`.
3. Follow the EXACT same SDK patterns, imports, and conventions as the existing code in this repository:
   - Use `AIProjectClient` from `azure.ai.projects` for agent management
   - Use `PromptAgentDefinition` / `WorkflowAgentDefinition` for agent definitions
   - Use `openai_client.responses.create()` with `agent_reference` for invocation
   - Use `AzureCliCredential` for authentication
   - Load env vars with `dotenv` using relative path resolution: `load_dotenv(Path().absolute().parent / '.env')`
   - Define tools as Python functions with `Annotated[type, Field(description="...")]` parameters
4. Implement EVERY module from the plan — do not skip any file.
   - If the plan specifies a Web app: build the web UI (Gradio, FastAPI, etc.) as a standalone Python app.
   - If the plan specifies a Notebook: create a single .ipynb notebook with all code organized in runnable cells (setup, agent creation, tool definitions, invocation, results display). The user will run the notebook top-to-bottom to see the agent in action.
5. After writing all code, create a `run_tests.py` script in the use-case folder that:
   - Tests each tool function independently with sample input data
   - Tests agent creation and basic invocation
   - Tests the full end-to-end workflow with a happy-path scenario
   - Prints clear PASS/FAIL results for each test
6. Create a `README.md` in the use-case folder with:
   - Setup instructions (referencing the existing .venv)
   - How to run the agent
   - How to run tests
   - Architecture overview

After implementation, run the tests and fix any issues until all tests pass.
````

**What Copilot will produce from the Implementation step:**

| Plan Element | → | Copilot Output |
|---|---|---|
| Plan → Code | → | All Python modules implemented in the new root-level folder |
| Tools (§3) → Functions | → | Fully implemented tool functions with Annotated type hints |
| Agent Config → Agent | → | Agent definitions matching repo patterns (PromptAgentDefinition / WorkflowAgentDefinition) |
| Synthetic Data (§8) → Tests | → | Generate test data per §8 spec, `run_tests.py` with happy-path end-to-end validation |
| UI (§7) | → | Web app (standalone Python app) or Notebook (`.ipynb` with runnable cells) |
| Docs → README | → | `README.md` with setup, run, test, and architecture instructions |

---

*— Microsoft Azure AI Foundry —*
