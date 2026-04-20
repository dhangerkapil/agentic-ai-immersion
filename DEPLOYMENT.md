# Workshop Deployment Guide

## Overview

Two deployment modes exist across two branches. Choose based on whether participants
have identities in your Azure Entra tenant.

| | **Method 1 — Entra** | **Method 2 — Non-Entra** |
|---|---|---|
| Branch | `main` | `non-entra` |
| Participant auth | `az login` (their own identity) | Shared Service Principal in `.env` |
| Requires Entra accounts | Yes | No |
| Per-user RBAC | Yes | No — single SP used by all |
| Best for | Internal teams, corporate tenants | External participants, isolated sandbox |

---

## Method 1 — Entra Authentication (`main`)

### Prerequisites

- Instructor has **Owner** or **User Access Administrator** role on the subscription
- Each participant has an account in the Azure Entra tenant
- PowerShell 7+ (`pwsh`) installed on the instructor's machine, or use `setup-env.sh` on Mac/Linux

### Step 1 — Provision Azure resources (instructor)

```powershell
pwsh provision.ps1
```

Follow the prompts. The script creates:
- Resource group
- Azure AI Foundry account and project
- AI Search instance (optional)
- Bing grounding connection (optional)
- Application Insights

When prompted **"Create a shared Service Principal?"** — answer **N**. Not needed for this method.

On completion a `.env` file is written to the repo root.

### Step 2 — Grant participant access (instructor)

```powershell
# From a file
pwsh grant-access.ps1 -EmailFile emails.txt

# Or paste emails interactively
pwsh grant-access.ps1
```

This assigns **Cognitive Services User** at both the AIServices account scope and the
project scope. Both are required — the project endpoint enforces its own RBAC check.

Allow **1–5 minutes** for RBAC propagation before participants begin.

### Step 3 — Participant setup

1. Clone the repo (`main` branch)
2. Open the folder in VS Code
3. Click **Reopen in Container** when prompted
4. Wait for the container to pull and attach — the startup log shows environment versions
5. A **Workshop** terminal opens automatically
6. A browser tab opens for `az login` — sign in with their Entra account
7. The terminal confirms the subscription and drops to a bash prompt

No `.env` file is needed — participants authenticate as themselves.

### Cleanup (instructor)

```powershell
# Remove participant role assignments
pwsh revoke-access.ps1 -EmailFile emails.txt

# Tear down all Azure resources
pwsh teardown.ps1
```

---

## Method 2 — Shared Service Principal (`non-entra`)

### Prerequisites

- Instructor has **Owner** or **User Access Administrator** role on the subscription
- Participants do **not** need Entra identities
- PowerShell 7+ (`pwsh`) on the instructor's machine

### Step 1 — Provision Azure resources + Service Principal (instructor)

```powershell
pwsh provision.ps1
```

When prompted **"Create a shared Service Principal?"** — accept the default **Y**.

Additional prompts:
- **Secret expiry date** — defaults to 5 days from today. Extend if the workshop runs longer.

The script creates the SP, assigns **Cognitive Services User** at account and project scope,
and writes the following to `.env`:

```
AZURE_CLIENT_ID=<sp-app-id>
AZURE_CLIENT_SECRET=<sp-client-secret>
AZURE_TENANT_ID=<tenant-id>
```

`DefaultAzureCredential` (used by all notebooks on this branch) picks these up automatically
via `EnvironmentCredential` — no `az login` required.

### Step 2 — Distribute the `.env` file (instructor)

The `.env` file contains secrets and is gitignored. Distribute it to participants securely:

- Share via a password manager or secrets vault link
- Drop into a private Teams/Slack message
- Place in a protected file share

Each participant must place the file at the **root of their local clone** before opening
the devcontainer.

> **Secret expiry reminder:** the SP client secret expires on the date chosen during
> provisioning. Rotate it before expiry with:
> ```bash
> az ad app credential reset --id <AZURE_CLIENT_ID> --end-date YYYY-MM-DD --append
> ```
> Then redistribute the updated `.env`.

### Step 3 — Participant setup

1. Clone the repo — **`non-entra` branch**:
   ```bash
   git clone -b non-entra <repo-url>
   ```
2. Place the `.env` file in the repo root
3. Open the folder in VS Code
4. Click **Reopen in Container** when prompted
5. Wait for the container to pull and attach
6. A **Workshop** terminal opens — no browser login is required
7. The terminal confirms the environment and drops to a bash prompt

### Cleanup (instructor)

```powershell
# Revoke role assignments and optionally delete the Service Principal
pwsh revoke-access.ps1

# Tear down all Azure resources
pwsh teardown.ps1
```

`revoke-access.ps1` will detect `AZURE_CLIENT_ID` in `.env` and offer to delete the SP.
Accept — the SP should not outlive the workshop.

---

## WebSearchAgent Deployment (Instructor)

The `hosted-agents/` directory contains a **WebSearchAgent** that runs as a
containerized hosted agent in Microsoft Foundry. It uses Bing Grounding for
real-time web search and is demonstrated in the hosted-agents section of the
workshop.

This is a **separate deployment** from `provision.ps1`. Run it once after
provisioning — participants do not need to do this step.

### Prerequisites

- `provision.ps1` completed (`.env` exists with Bing Grounding values)
- [Azure Developer CLI (`azd`)](https://aka.ms/install-azd) installed
- AI Foundry project in a [supported region](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/hosted-agents?view=foundry&tabs=cli#region-availability) — this workshop uses **East US 2**

### Deploy

```powershell
pwsh deploy-hosted-agents.ps1
```

The script:
1. Installs the `azure.ai.agents` azd extension if needed
2. Reads resource values from `.env` and sets them in the azd environment
3. Runs `azd ai agent init` — **interactive**: accept the recommended values shown on screen
4. Runs `azd deploy` — builds the container, pushes to registry, and deploys (5–10 min)

On completion, the output includes the **Agent playground URL** for testing.

### Tear down

```powershell
pwsh deploy-hosted-agents.ps1 -Down
```

This removes the hosted agent container and associated resources. It does **not**
delete the AI Foundry project or any resources created by `provision.ps1`.

### Notes

- The hosted agent uses a separate `gpt-4o` model deployment (10K TPM capacity)
  provisioned by azd — independent of the workshop's `gpt-5.1` deployment
- The `BING_CONNECTION_ID` from `.env` is passed automatically
- Detailed docs: [`hosted-agents/README.md`](hosted-agents/README.md)

---

## Quick Reference

### Instructor commands

| Task | Command |
|------|---------|
| Provision | `pwsh provision.ps1` |
| Deploy hosted agent | `pwsh deploy-hosted-agents.ps1` |
| Remove hosted agent | `pwsh deploy-hosted-agents.ps1 -Down` |
| Grant access (Entra) | `pwsh grant-access.ps1 -EmailFile emails.txt` |
| Revoke access | `pwsh revoke-access.ps1 -EmailFile emails.txt` |
| Tear down | `pwsh teardown.ps1` |
| Rotate SP secret | `az ad app credential reset --id <CLIENT_ID> --end-date YYYY-MM-DD --append` |

### Choosing a secret expiry

| Workshop length | Recommended expiry |
|---|---|
| Half day | 1 day |
| Full day | 2 days |
| Multi-day | Days + 1 buffer |
| Recurring | 30 days max, rotate between sessions |

### Branch summary

```
main          Entra auth — participants sign in as themselves
non-entra     SP auth — shared credentials distributed via .env
```

Shared fixes (content, dependencies, Python version) are committed to `main` and
merged into `non-entra`. Never merge `non-entra` into `main`.
