# Smoke test — post-deployment style check; builds the agent and verifies a real answer.
# Skipped automatically when no Foundry endpoint is configured.
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "agents"))
load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT / ".env")

pytestmark = pytest.mark.skipif(
    not (os.environ.get("AI_FOUNDRY_PROJECT_ENDPOINT") or os.environ.get("FOUNDRY_PROJECT_ENDPOINT")),
    reason="No Foundry endpoint configured",
)


async def test_smoke_answer():
    from agent import build_agent

    agent = build_agent()
    result = await agent.run("Which benefits categories do you help with? One sentence.")
    text = getattr(result, "text", None) or str(result)
    assert text and len(text.strip()) > 10
