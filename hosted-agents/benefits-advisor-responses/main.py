# Employee Benefits Cost Advisor — Foundry Hosted Agent (RESPONSES protocol)
"""Foundry Hosted Agent — Employee Benefits Cost Advisor using the RESPONSES protocol.

Contrasts with the Benefits Review agent (../benefits-review-invocations), which uses
the Invocations protocol. This agent demonstrates three Foundry hosting features:

  * Responses protocol  — multi-turn, streaming, model-directed tool use.
  * Foundry Toolbox     — web_search + code_interpreter exposed over MCP; the model
                          decides when to call them at runtime.
  * Foundry Skills      — SKILL.md domain knowledge embedded into the system
                          instructions (progressive disclosure).

Required environment variables:
    FOUNDRY_PROJECT_ENDPOINT        Foundry project endpoint (auto-injected when hosted)
    AZURE_AI_MODEL_DEPLOYMENT_NAME  Chat model deployment name
    TOOLBOX_NAME                    Foundry Toolbox with web_search + code_interpreter (optional)
    SKILL_NAMES                     Comma-separated skill names to embed at startup (optional)

Learn more:
    Hosted agents:   https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents
    Foundry Toolbox: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/toolbox
    Responses API:   https://learn.microsoft.com/azure/ai-foundry/openai/how-to/responses
"""
from __future__ import annotations

import logging
import os
import warnings
from pathlib import Path
from typing import Final

# Silence the SDK ExperimentalWarning emitted at import time (preview features).
warnings.simplefilter("ignore")

import httpx
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("benefits-advisor")

# Skills are baked into the container image at /app/skills/<name>/SKILL.md.
BUNDLED_SKILLS_DIR: Final = Path(__file__).parent / "skills"

SYSTEM_INSTRUCTIONS = """\
You are a Senior Employee Benefits Cost Advisor. You help HR leaders and benefits
managers understand, benchmark, and optimize their employee benefits programs.

## Your Capabilities
- **Market Research**: Use web_search to find current market trends, salary surveys, and benchmarks.
- **Cost Analysis**: Use code_interpreter to run calculations, projections, comparison tables, and charts.
- **Methodology**: Apply the cost-analysis-methodology knowledge below for structured frameworks.
- **Regulatory Knowledge**: Apply the regulatory-guidance knowledge below for statutory considerations.

## Interaction Style
- Act immediately — do NOT ask clarifying questions. Make reasonable assumptions based on typical
  market norms and state them clearly.
- Always show your work (calculations, sources, assumptions).
- Use tables for comparisons and proactively suggest follow-up analyses at the end.
- Express costs in a generic currency unit (CU) unless the user specifies a currency.

## Rules
- Never fabricate market data — use web_search to verify current figures.
- Attribute regulatory points to the relevant statutory concept.
- State assumptions clearly for any projection.
"""


def _load_skill_content(skill_names: list[str], skills_dir: Path) -> str:
    """Read each SKILL.md, strip its YAML frontmatter, and format as knowledge sections."""
    sections: list[str] = []
    for name in skill_names:
        skill_path = skills_dir / name / "SKILL.md"
        if skill_path.is_file():
            content = skill_path.read_text(encoding="utf-8")
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    content = content[end + 3:].strip()
            sections.append(f"\n## Knowledge: {name}\n\n{content}")
    return "\n".join(sections)


def _resolved_env(name: str) -> str:
    """Return an env var value, treating un-substituted ${VAR}/{{VAR}} placeholders as empty."""
    value = os.environ.get(name, "").strip()
    if (value.startswith("${") and value.endswith("}")) or (
        value.startswith("{{") and value.endswith("}}")
    ):
        return ""
    return value


def _project_endpoint() -> str:
    """Foundry project endpoint (injected when hosted; falls back to the workshop var locally)."""
    return os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"]


def _toolbox_endpoint(toolbox_name: str) -> str:
    """Resolve the Foundry Toolbox MCP endpoint URL from the project endpoint."""
    project_endpoint = _project_endpoint().rstrip("/")
    return f"{project_endpoint}/toolboxes/{toolbox_name}/mcp?api-version=v1"


class _ToolboxAuth(httpx.Auth):
    """Inject a fresh Entra bearer token on every Toolbox MCP request."""

    def __init__(self, token_provider) -> None:
        self._get_token = token_provider

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self._get_token()}"
        yield request


def main() -> None:
    """Embed skills, connect the toolbox, and start the Responses host server."""
    project_endpoint = _project_endpoint()
    model = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    credential = DefaultAzureCredential()

    # --- Foundry Skills: embed SKILL.md knowledge directly into the instructions ---
    skill_names = [n.strip() for n in _resolved_env("SKILL_NAMES").split(",") if n.strip()]
    instructions = SYSTEM_INSTRUCTIONS
    if skill_names and all((BUNDLED_SKILLS_DIR / n / "SKILL.md").is_file() for n in skill_names):
        instructions += _load_skill_content(skill_names, BUNDLED_SKILLS_DIR)
        logger.info("Embedded skills: %s", skill_names)
    else:
        logger.info("Running without skills (SKILL_NAMES=%s).", skill_names or "none")

    # --- Foundry Toolbox: connect over MCP so the model can call web_search / code_interpreter ---
    toolbox_name = _resolved_env("TOOLBOX_NAME")
    tools = None
    if toolbox_name:
        token_provider = get_bearer_token_provider(credential, "https://ai.azure.com/.default")
        http_client = httpx.AsyncClient(
            auth=_ToolboxAuth(token_provider),
            headers={"Foundry-Features": "Toolboxes=V1Preview"},
            timeout=120.0,
        )
        tools = [
            MCPStreamableHTTPTool(
                name=toolbox_name,
                url=_toolbox_endpoint(toolbox_name),
                http_client=http_client,
                load_prompts=False,
            )
        ]
        logger.info("Connected Toolbox '%s'.", toolbox_name)
    else:
        logger.info("Running without a Toolbox (TOOLBOX_NAME unset).")

    # --- Agent + Responses host server (POST /responses, OpenAI-compatible) ---
    client = FoundryChatClient(project_endpoint=project_endpoint, model=model, credential=credential)
    agent = Agent(client=client, instructions=instructions, tools=tools, default_options={"store": False})
    logger.info("Employee Benefits Cost Advisor starting — Responses protocol | model=%s", model)
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
