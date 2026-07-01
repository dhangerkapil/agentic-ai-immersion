"""Smoke test — build the agent and run one turn against the Foundry project.

In a full pipeline this runs against the *deployed* agent URL after each deployment.
Here it builds the agent from the versioned artefacts and exercises one turn, which
validates auth, the project endpoint, the model deployment, and the prompts.

Run:  python scripts/smoke_test.py
"""
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "agents"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")            # AgentOps-local .env (if any)
load_dotenv(ROOT.parent / ".env")     # workshop root .env (fallback)

from agent import build_agent  # noqa: E402


async def main() -> int:
    agent = build_agent()
    result = await agent.run("Which benefits categories do you help with? Answer in one sentence.")
    text = getattr(result, "text", None) or str(result)
    ok = bool(text and len(text.strip()) > 10)
    print("SMOKE:", "PASS" if ok else "FAIL", "->", text[:160])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
