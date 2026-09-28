"""Shared helpers for the Foundry Agents lab sequence (Hosted Agents first, Prompt Agents in Stretch 5).

Every lab driver script (the notebook side) imports this module after the standard `common` import block.
Hosted `main.py` files do not import it: they ship in a container with only `common/` and `data/` vendored.
It holds the pieces that are identical across the labs so the lab files
stay focused on what they teach:

* `agent_reference(name)`      the extra_body payload that routes a Responses call to a server-side agent
* `function_tools(names)`      FunctionTool objects built from benefits_data.TOOL_SCHEMAS (filtered by name)
* `run_turn(...)`              one participant turn against a platform prompt agent, including the client-side
                               function-call loop (Stretch 5 uses it; Lab 4 uses it for the deployed hosted agent)
* `artifact_path(...)`         labs/artifacts/labN/<name>
* `require_artifact(...)`      load a previous lab's artifact or exit with the catch_up.py hint
* `load_lab_module(...)`       import a lab file from a hyphenated folder (used by catch_up.py and Lab 4)
* `get_session_store(dir)`     common.session_store when present (Redis, Cosmos or file), else a local
                               file store with the same get/put/delete/list_ids surface (Lab 2 client side)

No endpoints, ids or keys live here. Everything comes from `.env` through common.foundry_env.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

LABS_DIR = Path(__file__).resolve().parent              # labs/
ROOT = LABS_DIR.parent                                   # foundry-hosted-agents-labs/ (where common/ and data/ live)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common import benefits_data, foundry_env, guardrails  # noqa: E402

DEFAULT_MODEL = "gpt-5.4-mini"
CITATION_RE = re.compile(r"\[KB-[A-Z]{3}-\d{3}\]")


# ----------------------------------------------------------------------------
# Environment and naming
# ----------------------------------------------------------------------------
def pick_model(env: dict) -> str:
    """Model deployment name from .env (base repo names first, then the Foundry alias)."""
    return env.get("AZURE_AI_MODEL_DEPLOYMENT_NAME") or env.get("FOUNDRY_MODEL") or DEFAULT_MODEL


def agent_reference(agent_name: str) -> dict:
    """The verified extra_body shape that binds a Responses call to a Foundry agent."""
    return {"agent_reference": {"name": agent_name, "type": "agent_reference"}}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def identity_line(participant_id: str) -> str:
    """Workshop identity check: participant_id plus ZIP, nothing else (compliance rule 3)."""
    participant = benefits_data.get_participant(participant_id)
    return f"Hi, this is participant {participant_id}, ZIP {participant.get('zip', '')}."


def count_citations(text: str) -> int:
    return len(CITATION_RE.findall(text or ""))


# ----------------------------------------------------------------------------
# Artifacts
# ----------------------------------------------------------------------------
def artifact_path(lab: str, *parts: str) -> Path:
    """labs/artifacts/<lab>/<parts...>; the lab folder is created on first use."""
    return foundry_env.artifacts_dir(LABS_DIR, lab).joinpath(*parts)


def require_artifact(lab: str, name: str, through: int, caller: str) -> dict:
    """Load a JSON artifact from an earlier lab or stop with the one command that fixes it."""
    path = artifact_path(lab, name)
    if not path.exists():
        raise SystemExit(
            f"[{caller}] Missing artifact {path.relative_to(LABS_DIR)}.\n"
            f"[{caller}] Earlier labs create it. Fix with:\n"
            f"[{caller}]     cd {LABS_DIR.name} && python catch_up.py --through {through}"
        )
    return foundry_env.load_artifact(path)


def load_lab_module(relative_file: str):
    """Import a lab script by path (folders like lab2-hosted-knowledge-sessions are not importable by name)."""
    path = LABS_DIR / relative_file
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


# ----------------------------------------------------------------------------
# Session store (Lab 2 persists the session -> conversation map on the client side; the hosted main.py has its own)
# ----------------------------------------------------------------------------
@dataclass
class _FallbackSessionRecord:
    """Same fields as common.session_store.SessionRecord; used only when that module is unavailable."""
    session_id: str
    participant_id: str | None = None
    agent_name: str = ""
    agent_version: str | None = None
    conversation_id: str | None = None
    last_response_id: str | None = None
    turn_count: int = 0
    updated_at: str = ""
    notes: dict = field(default_factory=dict)


class _FallbackFileSessionStore:
    """JSON file per session under <dir>/<session_id>.json. No Redis, no Cosmos, no dependencies."""

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
        return self.directory / f"{safe}.json"

    def get(self, session_id: str):
        path = self._path(session_id)
        if not path.exists():
            return None
        return _FallbackSessionRecord(**json.loads(path.read_text(encoding="utf-8")))

    def put(self, rec) -> None:
        data = asdict(rec) if hasattr(rec, "__dataclass_fields__") else dict(rec)
        self._path(data["session_id"]).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def delete(self, session_id: str) -> None:
        path = self._path(session_id)
        if path.exists():
            path.unlink()

    def list_ids(self) -> list[str]:
        return sorted(p.stem for p in self.directory.glob("*.json"))


SessionRecord = _FallbackSessionRecord
try:                                                     # common.session_store ships in common/ (Agent 2)
    from common import session_store as _session_store   # noqa: E402
    SessionRecord = _session_store.SessionRecord         # type: ignore[misc]
except ImportError:                                      # module missing: the file store below still works
    _session_store = None


def get_session_store(default_dir: Path, log_prefix: str = "[session]"):
    """Pick the configured store (BENEFITS_REDIS_URL -> Redis, BENEFITS_COSMOS_ENDPOINT -> Cosmos, else file).

    Falls back to the local file store when common.session_store is missing or when the configured
    backend cannot be reached (redis package not installed, Redis not running). The labs must keep
    running on a laptop with nothing but Python and az login.
    """
    if _session_store is not None:
        try:
            store = _session_store.get_session_store(Path(default_dir))
            print(f"{log_prefix} session store: {type(store).__name__}")
            return store
        except Exception as exc:                             # noqa: BLE001
            print(f"{log_prefix} session store {type(exc).__name__}: {exc}; using the local file store")
    else:
        print(f"{log_prefix} common.session_store not found; using the local file store")
    return _FallbackFileSessionStore(Path(default_dir))


# ----------------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------------
def tool_schema(name: str) -> dict:
    """Flat {name, description, parameters} schema for one benefits_data tool."""
    for schema in benefits_data.TOOL_SCHEMAS:
        flat = schema.get("function", schema)   # accept flat or {"type": "function", "function": {...}}
        if flat.get("name") == name:
            return flat
    known = sorted((s.get("function", s)).get("name", "?") for s in benefits_data.TOOL_SCHEMAS)
    raise KeyError(f"No schema named {name!r} in benefits_data.TOOL_SCHEMAS. Known: {known}")


def function_tools(names: list[str]) -> list:
    """FunctionTool objects for the named benefits_data tools.

    Strict mode is only switched on when every property is required, because the
    Responses API rejects strict schemas with optional properties.
    """
    from azure.ai.projects.models import FunctionTool

    tools = []
    for name in names:
        flat = tool_schema(name)
        params = json.loads(json.dumps(flat.get("parameters") or {}))
        params.setdefault("type", "object")
        params.setdefault("properties", {})
        params["additionalProperties"] = False
        strict = set(params["properties"]) == set(params.get("required", []))
        tools.append(FunctionTool(name=name, description=flat.get("description", name),
                                  parameters=params, strict=strict))
    return tools


def dispatch_tool(name: str, arguments: str | dict) -> dict | list:
    """Run one benefits_data tool by name; never raises so the loop can report errors to the model."""
    args = json.loads(arguments or "{}") if isinstance(arguments, str) else dict(arguments or {})
    fn = benefits_data.TOOL_REGISTRY.get(name)
    if fn is None:
        return {"error": f"unknown tool {name}"}
    try:
        return fn(**args)
    except TypeError as exc:
        return {"error": f"bad arguments for {name}: {exc}"}


# ----------------------------------------------------------------------------
# The conversation turn against a platform agent (Stretch 5 teaches the loop; Lab 4 uses it for deployed targets)
# ----------------------------------------------------------------------------
def run_turn(openai_client, agent_name: str, conversation_id: str, user_text: str,
             max_rounds: int = 6, log_prefix: str = "[agent]") -> tuple[str, list[dict]]:
    """Send one participant message and satisfy every function_call the agent emits.

    Returns (final_text, tool_calls). Server-side tool calls (MCP) are logged but need no
    client work; client-side function calls are executed through benefits_data.TOOL_REGISTRY.
    """
    from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam

    ref = agent_reference(agent_name)
    response = openai_client.responses.create(input=user_text, conversation=conversation_id, extra_body=ref)
    tool_calls: list[dict] = []
    for _ in range(max_rounds):
        outputs: ResponseInputParam = []
        for item in response.output:
            if item.type == "function_call":
                args = json.loads(item.arguments or "{}")
                result = dispatch_tool(item.name, args)
                tool_calls.append({"tool": item.name, "arguments": args, "server_side": False})
                print(f"{log_prefix}   tool {item.name}({_fmt_args(args)})")
                outputs.append(FunctionCallOutput(type="function_call_output", call_id=item.call_id,
                                                  output=json.dumps(result, default=str)))
            elif item.type == "mcp_call":
                name = getattr(item, "name", "?")
                label = getattr(item, "server_label", "mcp")
                tool_calls.append({"tool": name, "server": label, "server_side": True})
                print(f"{log_prefix}   server-side tool {label}.{name}")
        if not outputs:
            break
        response = openai_client.responses.create(input=outputs, conversation=conversation_id, extra_body=ref)
    return response.output_text, tool_calls


def _fmt_args(args: dict) -> str:
    return ", ".join(f"{k}={v!r}" for k, v in args.items())


def guardrail_report(text: str) -> dict:
    """Cheap local checks used after every turn: recommendation heuristic and PII regex."""
    return {
        "no_recommendation": not guardrails.contains_recommendation(text),
        "no_pii": guardrails.redact_pii(text) == text,
        "citations": count_citations(text),
    }


def fmt_checks(report: dict) -> str:
    return ", ".join(f"{k}={'OK' if v is True else 'FAIL' if v is False else v}" for k, v in report.items())
