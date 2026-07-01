"""Register the bundled SKILL.md skills with the Foundry project (beta.skills).

The agent embeds skill content locally at startup (see main.py), so this script is
optional. Run it when you want the skills managed as first-class Foundry resources
(visible in the portal, reusable across agents). Requires the preview Skills feature
(azure-ai-projects >= 2.2.0, allow_preview=True) and `az login`.

Run:  python hosted-agents/benefits-advisor-responses/provision_skills.py

Learn more: https://learn.microsoft.com/azure/ai-foundry/agents/concepts/skills
"""
from __future__ import annotations

import os
import warnings
from pathlib import Path

warnings.simplefilter("ignore")

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import SkillInlineContent
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path(__file__).resolve().parents[2] / ".env")  # workshop root .env fallback

SKILLS_DIR = Path(__file__).parent / "skills"


def _parse_skill(skill_md: Path) -> tuple[str, str, str]:
    """Return (name, description, instructions) from a SKILL.md (YAML frontmatter + body)."""
    text = skill_md.read_text(encoding="utf-8")
    name, description, body = skill_md.parent.name, "", text
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            front, body = text[3:end], text[end + 3:].strip()
            for line in front.splitlines():
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
    return name, description, body


def main() -> None:
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or os.environ["AI_FOUNDRY_PROJECT_ENDPOINT"]
    with AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True) as client:
        for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
            name, description, instructions = _parse_skill(skill_md)
            version = client.beta.skills.create(
                name,
                inline_content=SkillInlineContent(description=description, instructions=instructions),
                default=True,
            )
            print(f"Registered skill '{name}' -> version {version.version}")


if __name__ == "__main__":
    main()
