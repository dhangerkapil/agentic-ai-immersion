"""Environment loading and Azure client factories shared by every lab.

* load_env()                     reads .env files (base repo root, then this folder, then cwd) and returns the
                                 workshop variables with defaults. Never overrides variables already exported.
* get_credential()               AzureCliCredential (honours TENANT_ID). Entra only; no keys anywhere.
* get_project_client()           AIProjectClient for FOUNDRY_PROJECT_ENDPOINT with allow_preview=True
* get_openai_client()            project_client.get_openai_client() (Responses, Conversations, Evals)
* get_foundry_chat_client()      agent_framework.foundry.FoundryChatClient for the hosted agents (Agent Framework)
* artifacts_dir(folder, lab)     <folder>/artifacts/labN/ (created on demand; the labs pass labs/)
* save_artifact / load_artifact  JSON (or text) checkpoints that chain one lab to the next

Azure SDKs are imported inside the functions that need them, so `import foundry_env` and load_env()
work on a machine with no Azure packages installed (via_data's self-test relies on that).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]          # wtw-foundry-hosted-agents-labs/
BASE_REPO_ROOT = ROOT.parent                        # agentic-ai-immersion/ when dropped into the base repo

DEFAULTS: dict[str, str] = {
    "FOUNDRY_PROJECT_ENDPOINT": "",
    "AZURE_AI_MODEL_DEPLOYMENT_NAME": "gpt-5.4-mini",
    "FOUNDRY_MODEL": "",                            # falls back to AZURE_AI_MODEL_DEPLOYMENT_NAME
    "EMBEDDING_MODEL_DEPLOYMENT_NAME": "text-embedding-3-large",
    "AZURE_AI_SEARCH_ENDPOINT": "",
    "AZURE_OPENAI_ENDPOINT": "",
    "PROJECT_RESOURCE_ID": "",
    "TENANT_ID": "",
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "",
    "VIA_TODAY": "2026-10-06",
}
ENV_FILE_CANDIDATES = (BASE_REPO_ROOT / ".env", ROOT / ".env", Path.cwd() / ".env")


# ---------------------------------------------------------------------------
# .env handling (dependency-free; python-dotenv is used when installed)
# ---------------------------------------------------------------------------
def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if value[:1] in ("'", '"') and value[-1:] == value[:1] and len(value) >= 2:
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def _load_file(path: Path) -> list[str]:
    """Apply one .env file without overriding exported variables. Returns the keys it set."""
    if not path.is_file():
        return []
    try:
        from dotenv import dotenv_values         # type: ignore
        values = {k: v for k, v in dotenv_values(path).items() if v is not None}
    except ImportError:
        values = _parse_env_file(path)
    applied = []
    for key, value in values.items():
        if key not in os.environ:
            os.environ[key] = value
            applied.append(key)
    return applied


def load_env(verbose: bool = False) -> dict[str, str]:
    """Load .env files and return the workshop variables with defaults applied.

    Precedence (highest first): variables already exported in the process, then the base repo root
    .env, then wtw-foundry-hosted-agents-labs/.env, then ./.env. Values are also placed in os.environ so
    Azure SDKs and the labs' own os.environ.get(...) calls see the same thing.
    """
    seen: set[Path] = set()
    for candidate in ENV_FILE_CANDIDATES:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        applied = _load_file(resolved)
        if verbose and applied:
            print(f"[env] {resolved}: {', '.join(applied)}")
    env = {key: os.environ.get(key, default) or default for key, default in DEFAULTS.items()}
    if not env["FOUNDRY_MODEL"]:
        env["FOUNDRY_MODEL"] = env["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    os.environ.setdefault("VIA_TODAY", env["VIA_TODAY"])
    return env


def require(env: dict[str, str], *keys: str) -> None:
    """Exit-friendly check: raise with a pointer to SETUP.md when a required variable is blank."""
    missing = [k for k in keys if not env.get(k)]
    if missing:
        raise RuntimeError(f"Missing environment variable(s): {', '.join(missing)}. "
                           f"Copy .env.example to .env in the base repo root and fill them in (see SETUP.md).")


# ---------------------------------------------------------------------------
# Azure client factories (lazy imports)
# ---------------------------------------------------------------------------
def get_credential():
    """AzureCliCredential, scoped to TENANT_ID when set. Run `az login` first."""
    from azure.identity import AzureCliCredential
    tenant = load_env().get("TENANT_ID")
    return AzureCliCredential(tenant_id=tenant) if tenant else AzureCliCredential()


def get_project_client():
    """AIProjectClient(endpoint=FOUNDRY_PROJECT_ENDPOINT, credential=AzureCliCredential(), allow_preview=True)."""
    from azure.ai.projects import AIProjectClient
    env = load_env()
    require(env, "FOUNDRY_PROJECT_ENDPOINT")
    return AIProjectClient(endpoint=env["FOUNDRY_PROJECT_ENDPOINT"], credential=get_credential(), allow_preview=True)


def get_openai_client(project_client=None):
    """OpenAI client bound to the Foundry project (Responses, Conversations, Evals APIs)."""
    return (project_client or get_project_client()).get_openai_client()


def get_foundry_chat_client(model: str | None = None):
    """agent_framework.foundry.FoundryChatClient for the hosted agents (Agent Framework)."""
    from agent_framework.foundry import FoundryChatClient
    env = load_env()
    require(env, "FOUNDRY_PROJECT_ENDPOINT")
    return FoundryChatClient(project_endpoint=env["FOUNDRY_PROJECT_ENDPOINT"],
                             model=model or env["FOUNDRY_MODEL"], credential=get_credential())


def model_name(env: dict[str, str] | None = None) -> str:
    """The chat model deployment to use (FOUNDRY_MODEL, else AZURE_AI_MODEL_DEPLOYMENT_NAME)."""
    env = env or load_env()
    return env.get("FOUNDRY_MODEL") or env.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or DEFAULTS["AZURE_AI_MODEL_DEPLOYMENT_NAME"]


# ---------------------------------------------------------------------------
# Artifacts (the chain between labs)
# ---------------------------------------------------------------------------
def artifacts_dir(option_folder: Path | str, lab: str) -> Path:
    """<folder>/artifacts/<lab>/ (for example labs/artifacts/lab2), created if needed."""
    path = Path(option_folder) / "artifacts" / lab
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_artifact(path: Path | str, obj: Any) -> Path:
    """Write JSON (dicts, lists, dataclass-like objects via default=str) or text when obj is a str."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        path.write_text(obj, encoding="utf-8")
    else:
        path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")
    return path


def load_artifact(path: Path | str) -> Any:
    """Read a JSON artifact (dict/list), a JSONL file (list of dicts) or plain text by extension.

    Raises FileNotFoundError with the catch-up hint when the previous lab has not run.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Artifact {path} not found. Run the earlier lab, or `python catch_up.py --through N` "
                                f"from the labs folder to recreate artifacts for labs 1..N.")
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    return text


if __name__ == "__main__":
    loaded = load_env(verbose=True)
    print("[env] effective values (secrets are never stored in .env for this workshop; Entra login only):")
    for name, value in loaded.items():
        shown = value if value else "(blank)"
        if name == "APPLICATIONINSIGHTS_CONNECTION_STRING" and value:
            shown = value[:20] + "..."
        print(f"  {name:40} {shown}")
    print(f"[env] model deployment: {model_name(loaded)}")
    print("[env] artifacts land in labs/artifacts/<lab>/ via artifacts_dir(LABS_DIR, 'lab1')")
