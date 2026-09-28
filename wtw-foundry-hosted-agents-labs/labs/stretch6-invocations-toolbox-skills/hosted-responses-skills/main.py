"""Stretch 6: the Via Benefits concierge (Responses protocol) with Foundry Skills and a Foundry Toolbox.

Goal:    two ways to give a hosted agent capabilities without writing more tools:
         * Skills: skills/<name>/SKILL.md files bundled in the ZIP. At startup the agent embeds an index (name +
           description) into its instructions and exposes read_skill(name) so the model loads the full text only
           when it needs it (progressive disclosure). Here: hra-reimbursement-rules, derived from KB-ACC-001.
         * Toolbox (preview): a Foundry Toolbox (web_search + code_interpreter) reached over MCP with
           MCPStreamableHTTPTool. Enabled only when TOOLBOX_MCP_URL is set; the agent runs without it.
Inputs:  env FOUNDRY_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME (or FOUNDRY_MODEL), optional SKILL_NAMES
         (comma list; default: every skills/*/SKILL.md), TOOLBOX_NAME, TOOLBOX_MCP_URL, VIA_AGENT_NAME, VIA_HOSTED_PORT.
         common/, data/ and skills/ are copied here by ../stretch6_invocations.py build().
Outputs: HTTP server speaking the OpenAI Responses protocol (POST /responses) on port 8088.

Pattern source: base repo hosted-agents/benefits-advisor-responses (SKILL_NAMES, TOOLBOX_NAME, skills embedded at
startup, "_ping_available = False" because Foundry Toolbox does not implement MCP ping). The Toolbox URL shape and
the MCPStreamableHTTPTool constructor carry VERIFY tags: do not present them as certain.
"""
# %% Imports and path setup
from __future__ import annotations

import os
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

HERE = Path(__file__).resolve().parent
for folder in (HERE.parents[2] if len(HERE.parents) > 2 else HERE, HERE):     # repo root, then vendored copies
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

warnings.simplefilter("ignore")

from common import guardrails, via_data  # noqa: E402

from agent_framework import Agent, tool  # noqa: E402
from agent_framework.foundry import FoundryChatClient  # noqa: E402
from agent_framework_foundry_hosting import ResponsesHostServer  # noqa: E402
from azure.identity import DefaultAzureCredential  # noqa: E402
from pydantic import Field  # noqa: E402

AGENT_NAME = os.environ.get("VIA_AGENT_NAME", "via-concierge-hosted")
DEFAULT_MODEL = "gpt-5.4-mini"
ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or os.environ.get("FOUNDRY_MODEL") or DEFAULT_MODEL
SKILLS_DIR = Path(os.environ.get("VIA_SKILLS_DIR", str(HERE / "skills")))
SKILL_NAMES = [name.strip() for name in os.environ.get("SKILL_NAMES", "").split(",") if name.strip()]
TOOLBOX_NAME = os.environ.get("TOOLBOX_NAME", "")
TOOLBOX_MCP_URL = os.environ.get("TOOLBOX_MCP_URL", "")


def log(message: str) -> None:
    print(f"[skills] {message}", flush=True)


# %% Skills: read skills/<name>/SKILL.md, split frontmatter, build the index for the instructions
def load_skills(directory: Path = SKILLS_DIR, names: list[str] | None = None) -> dict[str, dict]:
    """{name: {"description", "body", "meta", "path"}} for every SKILL.md found (or only `names`)."""
    skills: dict[str, dict] = {}
    if not directory.is_dir():
        return skills
    for path in sorted(directory.glob("*/SKILL.md")):
        meta, body = via_data.split_frontmatter(path.read_text(encoding="utf-8"))
        name = meta.get("name") or path.parent.name
        if names and name not in names:
            continue
        skills[name] = {"description": meta.get("description", ""), "body": body.strip(), "meta": meta, "path": str(path)}
    return skills


SKILLS = load_skills(names=SKILL_NAMES or None)


def skills_index() -> str:
    """The part that goes into the instructions: names and descriptions only (progressive disclosure)."""
    if not SKILLS:
        return "SKILLS: none bundled in this version.\n"
    lines = ["SKILLS available (call read_skill(name) to load the full procedure before you answer in that area):"]
    lines += [f"- {name}: {skill['description']}" for name, skill in SKILLS.items()]
    return "\n".join(lines) + "\n"


@tool(approval_mode="never_require")
def read_skill(name: Annotated[str, Field(description="Skill name exactly as listed in the instructions, e.g. hra-reimbursement-rules")]) -> dict:
    """Load the full text of a bundled skill (procedure, rules, accepted documents). Cite the doc id it names."""
    skill = SKILLS.get(name.strip())
    if not skill:
        return {"error": f"unknown skill {name!r}", "available": sorted(SKILLS)}
    return {"name": name, "source_doc": skill["meta"].get("source_doc"), "last_reviewed": skill["meta"].get("last_reviewed"), "text": skill["body"]}


# %% Tools over the systems of record (accounts flavour, since the bundled skill is about HRA claims)
PID = Annotated[str, Field(description="Participant id such as P-1001")]


@tool(approval_mode="never_require")
def get_participant(participant_id: PID) -> dict:
    """Look up a Via Benefits participant profile."""
    return via_data.get_participant(participant_id)


@tool(approval_mode="never_require")
def get_hra_account(participant_id: PID) -> dict:
    """HRA reimbursement account: balance, allocation, auto-reimbursement, debit card status, claims summary."""
    return via_data.get_hra_account(participant_id)


@tool(approval_mode="never_require")
def get_claim_status(claim_id: Annotated[str, Field(description="Claim id such as CLM-9003")]) -> dict:
    """Status of one HRA claim, with the human readable denial reason when denied."""
    return via_data.get_claim_status(claim_id)


# %% Toolbox (preview): Foundry-managed web_search + code_interpreter over MCP
def toolbox_tool():
    """MCPStreamableHTTPTool bound to the Toolbox MCP endpoint, or None when TOOLBOX_MCP_URL is not set."""
    if not TOOLBOX_MCP_URL:
        return None
    import httpx
    from agent_framework import MCPStreamableHTTPTool

    class EntraBearerAuth(httpx.Auth):
        """Fresh Entra token per request. Locally your az login; hosted, the agent's managed identity."""

        def __init__(self, scope: str = "https://ai.azure.com/.default"):
            self.credential, self.scope = DefaultAzureCredential(), scope

        def auth_flow(self, request):
            request.headers["Authorization"] = f"Bearer {self.credential.get_token(self.scope).token}"
            yield request

    # VERIFY against https://learn.microsoft.com/azure/ai-foundry/agents/ (Foundry Toolbox, preview) before delivery:
    # the Toolbox MCP URL (set TOOLBOX_MCP_URL explicitly; do not guess it from the project endpoint), the token
    # scope, and MCPStreamableHTTPTool(name=..., url=..., http_client=...) (BRIEF-shared 5d shape).
    mcp = MCPStreamableHTTPTool(name=TOOLBOX_NAME or "foundry-toolbox", url=TOOLBOX_MCP_URL,
                                http_client=httpx.AsyncClient(auth=EntraBearerAuth(), timeout=120.0))
    # VERIFY: base repo hosted-agents/README.md: "Foundry Toolbox doesn't implement MCP ping; keep the
    # _ping_available = False compatibility setting". Attribute name taken from that note.
    try:
        mcp._ping_available = False  # noqa: SLF001
    except Exception:  # noqa: BLE001
        pass
    return mcp


# %% Instructions and agent
ROLE_INSTRUCTIONS = """You are the Via Benefits concierge (Responses protocol) with bundled skills.
Confirm identity with participant_id and ZIP only, then use the tools for every fact. Before answering a question
about HRA claims, denials, documentation or reimbursement timing, call read_skill("hra-reimbursement-rules") and
follow its "How to answer" pattern; cite [KB-ACC-001]. If a Toolbox tool is available, use web_search only for
public, non-participant information (for example this year's Medicare Part B standard premium) and say that it
came from the web; use code_interpreter for arithmetic over amounts the participant gives you. Never send
participant data to the web.

"""
INSTRUCTIONS = ROLE_INSTRUCTIONS + skills_index() + "\n" + guardrails.COMPLIANCE_INSTRUCTIONS
assert INSTRUCTIONS.endswith(guardrails.COMPLIANCE_INSTRUCTIONS), "every agent carries the compliance block"


def build_agent() -> Agent:
    if not ENDPOINT:
        sys.exit("[skills] FOUNDRY_PROJECT_ENDPOINT is not set (locally: .env at the repo root; hosted: set by azd)")
    client = FoundryChatClient(project_endpoint=ENDPOINT, model=MODEL, credential=DefaultAzureCredential())
    tools = [get_participant, get_hra_account, get_claim_status, read_skill]
    toolbox = toolbox_tool()
    if toolbox is not None:
        tools.append(toolbox)
    agent = Agent(client=client, name=AGENT_NAME, instructions=INSTRUCTIONS, tools=tools, default_options={"store": False})
    log(f"agent {AGENT_NAME}: model={MODEL} skills={sorted(SKILLS) or 'none'} toolbox={TOOLBOX_NAME or 'off'} "
        f"started={datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return agent


# %% YOUR TURN (10 min): write a second skill. Create skills/debit-card-faq/SKILL.md from data/knowledge/debit-card-faq.md
# (KB-ACC-002): frontmatter name + description, then the lost/blocked/declined procedures. Restart; the index in the
# instructions now lists two skills, and "my card was declined at the pharmacy" makes the model read the new one.

if __name__ == "__main__":
    server = ResponsesHostServer(build_agent())
    port = int(os.environ.get("VIA_HOSTED_PORT", "8088"))
    if port != 8088:
        server.run(port=port)                    # VERIFY: run(port=...) (same note as Lab 1)
    else:
        server.run()
