"""Config validation for the Benefits Concierge agent — runs in CI on every PR.

Checks that the agent's versioned artefacts (config + prompts) are present and
well-formed before anything is built or deployed.

Run:  python scripts/validate_agent.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    errors: list[str] = []

    cfg_path = ROOT / "src" / "agents" / "agent_config.json"
    if not cfg_path.is_file():
        errors.append(f"missing {cfg_path.relative_to(ROOT)}")
    else:
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            for key in ("name", "model", "protocol"):
                if key not in cfg:
                    errors.append(f"agent_config.json missing required key '{key}'")
        except json.JSONDecodeError as exc:
            errors.append(f"agent_config.json is not valid JSON: {exc}")

    for rel in ("src/prompts/system.txt", "src/prompts/instructions.txt"):
        if not (ROOT / rel).is_file():
            errors.append(f"missing prompt file {rel}")

    system_txt = ROOT / "src" / "prompts" / "system.txt"
    if system_txt.is_file() and len(system_txt.read_text(encoding="utf-8").strip()) < 20:
        errors.append("system.txt looks too short to be a real system prompt")

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK: agent config and prompts are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
