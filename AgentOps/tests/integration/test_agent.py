# Integration test — builds the agent and runs one turn against the Foundry project.
# Skipped automatically when no Foundry endpoint is configured.
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "agents"))
load_dotenv(ROOT.parent / ".env")  # workshop root .env
load_dotenv(ROOT / ".env")          # AgentOps-local .env (if any)

pytestmark = pytest.mark.skipif(
    not (os.environ.get("AI_FOUNDRY_PROJECT_ENDPOINT") or os.environ.get("FOUNDRY_PROJECT_ENDPOINT")),
    reason="No Foundry endpoint configured",
)


async def test_agent_runs_one_turn():
    from agent import build_agent

    agent = build_agent()
    result = await agent.run("Name one employee benefit category in one word.")
    text = getattr(result, "text", None) or str(result)
    assert text and text.strip()
