# Unit tests — no network. Validate the versioned artefacts and the validate script.
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_agent_config_valid():
    cfg = json.loads((ROOT / "src" / "agents" / "agent_config.json").read_text(encoding="utf-8"))
    assert cfg["name"]
    assert cfg["model"]
    assert cfg["protocol"] == "responses"


def test_prompts_present_and_nonempty():
    assert (ROOT / "src" / "prompts" / "system.txt").read_text(encoding="utf-8").strip()
    assert (ROOT / "src" / "prompts" / "instructions.txt").is_file()


def test_validate_agent_script_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_agent.py")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
