# Employee Benefits Concierge — Foundry Hosted Agent (operated via GitOps).
"""Foundry hosted agent for the AgentOps GitOps example.

Everything that affects this agent's behaviour is a file in source control:
  * persona      -> src/prompts/system.txt + instructions.txt
  * settings     -> src/agents/agent_config.json
  * tools        -> src/tools/toolbox_config.py (versioned Foundry Toolbox)

It serves the Responses protocol via agent-framework-foundry-hosting. See ../../README.md
for the full GitOps delivery model.

Learn more: https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents
"""
from __future__ import annotations

import json
import logging
import os
import warnings
from pathlib import Path

warnings.simplefilter("ignore")

import httpx
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("benefits-concierge")

_HERE = Path(__file__).parent
_PROMPTS = _HERE.parent / "prompts"
_CONFIG = _HERE / "agent_config.json"


def _project_endpoint() -> str:
    """Foundry project endpoint (injected when hosted; workshop var locally)."""
    return os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"]


def load_config() -> dict:
    """Load versioned agent settings from agent_config.json."""
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


def load_instructions() -> str:
    """Assemble the system prompt from the versioned prompt files."""
    system = (_PROMPTS / "system.txt").read_text(encoding="utf-8").strip()
    extra = _PROMPTS / "instructions.txt"
    if extra.is_file():
        system += "\n\n" + extra.read_text(encoding="utf-8").strip()
    return system


class _ToolboxAuth(httpx.Auth):
    """Inject a fresh Entra bearer token on every Toolbox MCP request."""

    def __init__(self, token_provider) -> None:
        self._get_token = token_provider

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self._get_token()}"
        yield request


def build_agent() -> Agent:
    """Build the agent from versioned prompts/config, optionally attaching the Toolbox."""
    cfg = load_config()
    model = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or cfg.get("model", "gpt-4.1-mini")
    credential = DefaultAzureCredential()

    tools = None
    toolbox_name = os.environ.get("TOOLBOX_NAME", "").strip()
    if toolbox_name and not toolbox_name.startswith("${"):
        token_provider = get_bearer_token_provider(credential, "https://ai.azure.com/.default")
        http_client = httpx.AsyncClient(
            auth=_ToolboxAuth(token_provider),
            headers={"Foundry-Features": "Toolboxes=V1Preview"},
            timeout=120.0,
        )
        url = f"{_project_endpoint().rstrip('/')}/toolboxes/{toolbox_name}/mcp?api-version=v1"
        tools = [MCPStreamableHTTPTool(name=toolbox_name, url=url, http_client=http_client, load_prompts=False)]
        logger.info("Toolbox '%s' connected.", toolbox_name)

    client = FoundryChatClient(project_endpoint=_project_endpoint(), model=model, credential=credential)
    return Agent(client=client, instructions=load_instructions(), tools=tools, default_options={"store": False})


def main() -> None:
    logger.info("Employee Benefits Concierge starting (Responses protocol).")
    ResponsesHostServer(build_agent()).run()


if __name__ == "__main__":
    main()
