# Copilot Instructions for Agentic AI Immersion Day

## Project Overview

This is a hands-on workshop repository for building AI agents with Microsoft Azure AI Foundry. It covers Azure AI Agents SDK, Microsoft Agent Framework, observability, evaluations, and hosted agents.

### Repository Structure

```
azure-ai-agents/           # Azure AI Agents notebooks (basics, tools, search, MCP, IQ, memory, hosted-skills)
agent-framework/            # Microsoft Agent Framework notebooks
  agents/                   #   Agent providers (Azure AI, OpenAI, etc.)
  workflows/                #   Multi-agent workflows (sequential, magentic, human-in-the-loop)
  middleware/                #   Function/class/decorator middleware patterns
  threads/                  #   Custom thread stores (Redis, suspend/resume)
  context-providers/         #   Context providers (simple, AI Search agentic retrieval)
  skills/                   #   Agent Skills (file-based, code-defined, FSI scenarios)
  observability/             #   Tracing with Foundry & OpenTelemetry
observability-and-evaluations/  # Telemetry, agent evaluation, red-team testing
byouc/                      # Bring Your Own Use Case templates
```

### Key SDK Packages (Python)

| Package | Purpose |
|---------|---------|
| `azure-ai-projects` | **Recommended entry point** — AIProjectClient for agents, evals, connections |
| `azure-ai-agents` | Low-level AgentsClient (auto-installed as dependency, access via `project_client.agents`) |
| `azure-ai-evaluation` | Agent evaluation, red-teaming, quality metrics |
| `azure-search-documents` | Azure AI Search SDK for vector/hybrid/agentic retrieval |
| `azure-identity` | DefaultAzureCredential for authentication |
| `microsoft-agent-framework` | Agent Framework for persistent agents, workflows, middleware |

### Authentication Pattern

Always use `DefaultAzureCredential`. The project endpoint is in `.env` as `AI_FOUNDRY_PROJECT_ENDPOINT`:

```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

project_client = AIProjectClient(
    endpoint=os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
agents_client = project_client.agents  # access agents via project client
```

### Environment Variables

All config is in `.env` at the repo root. Key variables:
- `AI_FOUNDRY_PROJECT_ENDPOINT` — Foundry project endpoint
- `AZURE_AI_MODEL_DEPLOYMENT_NAME` — Model deployment (gpt-5.4)
- `AZURE_AI_SEARCH_ENDPOINT` / `AZURE_SEARCH_INDEX_NAME` — AI Search config
- `FOUNDRY_MCP_CONNECTION_ID` — MCP server connection

## ⚠️ Fresh Information First

**Azure SDKs and Foundry APIs change constantly. Never work with stale knowledge.**

Before implementing anything with Azure/Foundry SDKs:

1. **Search official docs first** — Use the Microsoft Docs MCP (`microsoft-docs`) to get current API signatures, parameters, and patterns
2. **Verify SDK versions** — Check `pip show <package>` for installed versions; APIs differ between versions
3. **Don't trust cached knowledge** — Your training data is outdated. The SDK you "know" may have breaking changes.

**If you skip this step and use outdated patterns, you will produce broken code.**

---

## Core Principles

Apply these principles to every task.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- If you write 200 lines and it could be 50, rewrite it.

**The test:** Would a senior engineer say this is overcomplicated? If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

**The test:** Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution (TDD)

**Define success criteria. Loop until verified.**

| Instead of... | Transform to... |
|---------------|-----------------|
| "Add validation" | "Write tests for invalid inputs, then make them pass" |
| "Fix the bug" | "Write a test that reproduces it, then make it pass" |
| "Refactor X" | "Ensure tests pass before and after" |

---

## Installed Skills

Skills are domain-specific knowledge packages. Each has a `SKILL.md` with YAML frontmatter for discovery.

### Foundry Skills (`.github/plugins/azure-skills/skills/`)

| Skill | Purpose | Maps To |
|-------|---------|---------|
| `microsoft-foundry` | **Orchestrator** — routes intent to sub-skills | All Foundry notebooks |
| `foundry-hosted-agents` | Build/deploy containerized agents | `hosted-agents/` |
| `foundry-toolboxes` | Intent-based Toolboxes (MCP, AI Search, Code Interpreter) | Tool integration |
| `foundry-workflows` | Multi-agent orchestration & Connected Agents | `agent-framework/workflows/` |
| `foundry-iq-knowledge-bases` | Agentic retrieval pipelines | `azure-ai-agents/8-foundry-IQ-agents.ipynb` |
| `foundry-memory` | Long-term memory across sessions | `azure-ai-agents/9-agent-memory-search.ipynb` |
| `foundry-observability` | Tracing, eval-trace correlation, batch evals | `observability-and-evaluations/` |
| `foundry-governance` | RBAC, RAI policies, AI Gateway | Security & governance |
| `foundry-managed-skills` | SKILL.md as Foundry-side resource | Managed skills |
| `foundry-projects-resources` | Provision resources, connections, networking | Project setup |
| `foundry-models` | Model deployment, capacity, quota | Model management |

### Python SDK Skills (`.github/plugins/azure-sdk-python/skills/`)

| Skill | Purpose | Maps To |
|-------|---------|---------|
| `azure-ai-projects-py` | **Recommended** — AIProjectClient for agents, evals, connections | All notebooks |
| `agent-framework-azure-ai-py` | Agent Framework with AzureAIAgentsProvider | `agent-framework/` |
| `azure-search-documents-py` | AI Search SDK for vector/hybrid/agentic retrieval | `azure-ai-agents/5-agents-aisearch.ipynb` |
| `azure-identity-py` | DefaultAzureCredential authentication | All notebooks |

### Core Skills (`.github/skills/`)

| Skill | Purpose | Maps To |
|-------|---------|---------|
| `cloud-solution-architect` | Azure architecture design, WAF reviews, design patterns, technology choices | Architecture decisions |
| `mcp-builder` | Building MCP servers | `azure-ai-agents/7-mcp-tools.ipynb` |
| `skill-creator` | Creating new custom skills | Extending the repo |

### Skill Selection

Only load skills relevant to the current task. Loading all skills causes context rot.

---

## MCP Servers

Pre-configured Model Context Protocol servers in `.vscode/mcp.json`:

### Documentation & Search

| MCP | Purpose |
|-----|---------|
| `microsoft-docs` | **Search Microsoft Learn** — Official Azure/Foundry docs. Use this FIRST. |
| `context7` | Indexed documentation with semantic search |
| `deepwiki` | Ask questions about GitHub repositories |

### Development Tools

| MCP | Purpose |
|-----|---------|
| `github` | GitHub API operations |
| `playwright` | Browser automation and testing |

### Utilities

| MCP | Purpose |
|-----|---------|
| `sequentialthinking` | Step-by-step reasoning for complex problems |
| `markitdown` | Convert documents to markdown |
| `memory` | Persistent memory across sessions |

**Usage:** Use `microsoft-docs` to search official documentation before implementing Azure SDK code.

---

## SDK Quick Reference

| Package | Purpose | Install |
|---------|---------|---------|
| `azure-ai-projects` | Foundry project client, agents, evals, connections | `pip install azure-ai-projects` |
| `azure-ai-agents` | Standalone agents client (use via projects) | `pip install azure-ai-agents` |
| `azure-search-documents` | Azure AI Search SDK | `pip install azure-search-documents` |
| `azure-identity` | Authentication | `pip install azure-identity` |

### Authentication Pattern

Always use `DefaultAzureCredential` for production:

```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

credential = DefaultAzureCredential()
client = AIProjectClient(
    endpoint="https://<resource>.services.ai.azure.com/api/projects/<project>",
    credential=credential
)
```

### Environment Variables

```bash
AI_FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-5.4
```

---

## Conventions

### Code Style

- Prefer `async/await` for all Azure SDK I/O
- Use context managers: `with client:` or `async with client:`
- Close clients explicitly or use context managers
- Use `create_or_update_*` for idempotent operations
- Use type hints on all function signatures

### Git & GitHub

- Always use `gh` CLI for GitHub operations (PRs, issues, etc.) — never the MCP `github-create_pull_request` tool
- Use `gh pr create` for pull requests, `gh issue create` for issues

### Clean Code Checklist

Before completing any code change:

- [ ] Functions do one thing
- [ ] Names are descriptive and intention-revealing
- [ ] No magic numbers or strings (use constants)
- [ ] Error handling is explicit (no empty catch blocks)
- [ ] No commented-out code
- [ ] Tests cover the change

### Testing Patterns

```python
# Arrange
service = ProjectService()
expected = Project(id="123", name="test")

# Act  
result = await service.get_project("123")

# Assert
assert result == expected
```

---

## Creating New Skills

1. Create a new directory under `.github/skills/<skill-name>/`
   - Use language suffix: `-py`, `-dotnet`, `-ts`, `-java`
   - Core/cross-language skills have no suffix
   - Example: `azure-cosmos-db-py`, `azure-ai-inference-dotnet`, `mcp-builder`
2. Add a `SKILL.md` file with YAML frontmatter:
   ```yaml
   ---
   name: skill-name-py
   description: Brief description of what the skill does and when to use it
   ---
   ```
3. Add detailed instructions in the markdown body
4. Keep skills focused on a single domain
5. Reference official docs via `microsoft-docs` MCP for current API patterns

---

## Do's and Don'ts

### Do

- ✅ Use `DefaultAzureCredential` for authentication
- ✅ Use async/await for all Azure SDK operations
- ✅ Write tests before or alongside implementation
- ✅ Keep functions small and focused
- ✅ Match existing patterns in the codebase
- ✅ Use `gh` CLI for all GitHub operations (PRs, issues, releases)

### Don't

- ❌ Hardcode credentials or endpoints
- ❌ Suppress type errors (`as any`, `@ts-ignore`, `# type: ignore`)
- ❌ Leave empty exception handlers
- ❌ Refactor unrelated code while fixing bugs
- ❌ Add dependencies without justification
- ❌ Use GitHub MCP tools for write operations (enterprise token restrictions)

---

## Success Indicators

These principles are working if you see:

- Fewer unnecessary changes in diffs
- Fewer rewrites due to overcomplication
- Clarifying questions come before implementation (not after mistakes)
- Clean, minimal PRs without drive-by refactoring
- Tests that document expected behavior
