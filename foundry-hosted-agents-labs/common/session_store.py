"""Session map for resilient clients and hosted agents (shared by Lab 1 and Lab 4).

A SessionRecord is the small piece of state a client must never lose: which Foundry conversation (Prompt
Agents) or which message-store key (Hosted Agents) belongs to a participant session. Keep it outside the
process and a restarted script, a second web node or a failover region resumes the same thread.

* SessionRecord         dataclass, JSON friendly (to_dict / from_dict)
* SessionStore          Protocol: get / put / delete / list_ids
* FileSessionStore      JSON files under <dir>/<session_id>.json (default; artifacts/labN/sessions/)
* RedisSessionStore     redis-py, key benefits:session:<id>, TTL from BENEFITS_SESSION_TTL_SECONDS (default 7 days)
* CosmosSessionStore    azure-cosmos with DefaultAzureCredential (BENEFITS_COSMOS_ENDPOINT / _DB / _CONTAINER)
* get_session_store()   picks Redis if BENEFITS_REDIS_URL is set, Cosmos if BENEFITS_COSMOS_ENDPOINT is set, else File

No Azure or redis import happens at module import time; each backend imports its SDK inside __init__ so
`python common/session_store.py` self-tests the file store on a machine with nothing installed.

Usage:
    from common import session_store
    store = session_store.get_session_store(ARTIFACTS / "lab1" / "sessions")
    rec = store.get(session_id) or session_store.SessionRecord.new(session_id, agent_name="benefits-concierge")
    rec.conversation_id = conversation.id
    store.put(rec.touch())
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, runtime_checkable

DEFAULT_TTL_SECONDS = 7 * 24 * 3600
REDIS_KEY_PREFIX = "benefits:session:"
_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_session_id(session_id: str) -> str:
    """File-system and key safe form of a session id (letters, digits, dot, underscore, dash)."""
    cleaned = _SAFE_ID.sub("_", str(session_id).strip())
    if not cleaned:
        raise ValueError("session_id must not be empty")
    return cleaned[:128]


# ---------------------------------------------------------------------------
# The record
# ---------------------------------------------------------------------------
@dataclass
class SessionRecord:
    session_id: str
    participant_id: str | None
    agent_name: str
    agent_version: str | None
    conversation_id: str | None
    last_response_id: str | None
    turn_count: int
    updated_at: str
    notes: dict = field(default_factory=dict)

    @classmethod
    def new(cls, session_id: str, agent_name: str, participant_id: str | None = None,
            agent_version: str | None = None, **notes) -> "SessionRecord":
        return cls(session_id=session_id, participant_id=participant_id, agent_name=agent_name,
                   agent_version=agent_version, conversation_id=None, last_response_id=None,
                   turn_count=0, updated_at=_now_iso(), notes=dict(notes))

    def touch(self, response_id: str | None = None, increment: int = 1) -> "SessionRecord":
        """Record one completed turn and return self (for `store.put(rec.touch())`)."""
        self.turn_count += increment
        if response_id:
            self.last_response_id = response_id
        self.updated_at = _now_iso()
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SessionRecord":
        known = {f: data.get(f) for f in cls.__dataclass_fields__}      # ignore unknown keys from older writers
        known["turn_count"] = int(known.get("turn_count") or 0)
        known["notes"] = dict(known.get("notes") or {})
        known["updated_at"] = known.get("updated_at") or _now_iso()
        return cls(**known)


# ---------------------------------------------------------------------------
# The protocol every backend satisfies
# ---------------------------------------------------------------------------
@runtime_checkable
class SessionStore(Protocol):
    def get(self, session_id: str) -> SessionRecord | None: ...
    def put(self, rec: SessionRecord) -> None: ...
    def delete(self, session_id: str) -> None: ...
    def list_ids(self) -> list[str]: ...


# ---------------------------------------------------------------------------
# File store (default): one JSON file per session
# ---------------------------------------------------------------------------
class FileSessionStore:
    """JSON files under <directory>/<session_id>.json. Good for one laptop; not shared across replicas."""

    kind = "file"

    def __init__(self, directory: Path | str):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.directory / f"{safe_session_id(session_id)}.json"

    def get(self, session_id: str) -> SessionRecord | None:
        path = self._path(session_id)
        if not path.is_file():
            return None
        return SessionRecord.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def put(self, rec: SessionRecord) -> None:
        path = self._path(rec.session_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rec.to_dict(), indent=2, default=str) + "\n", encoding="utf-8")
        tmp.replace(path)                                    # atomic on the same file system

    def delete(self, session_id: str) -> None:
        path = self._path(session_id)
        if path.is_file():
            path.unlink()

    def list_ids(self) -> list[str]:
        ids = []
        for path in sorted(self.directory.glob("*.json")):
            try:
                ids.append(json.loads(path.read_text(encoding="utf-8")).get("session_id") or path.stem)
            except (OSError, ValueError):
                ids.append(path.stem)
        return ids

    def __repr__(self) -> str:
        return f"FileSessionStore({self.directory})"


# ---------------------------------------------------------------------------
# Redis store: shared across processes and replicas, expires idle sessions
# ---------------------------------------------------------------------------
class RedisSessionStore:
    """redis-py backed store. Key benefits:session:<id>, value JSON, TTL BENEFITS_SESSION_TTL_SECONDS (default 7 days).

    Local Redis for the workshop: docker run -d -p 6379:6379 redis:latest
    then BENEFITS_REDIS_URL=redis://localhost:6379/0. Entra-authenticated Azure Managed Redis uses a
    rediss:// URL; pass a token-refreshing credential through the `client` argument in that case.
    """

    kind = "redis"

    def __init__(self, url: str | None = None, ttl_seconds: int | None = None, client=None,
                 key_prefix: str = REDIS_KEY_PREFIX):
        import redis                                         # lazy: only when this backend is chosen

        self.url = url or os.environ.get("BENEFITS_REDIS_URL", "redis://localhost:6379/0")
        self.ttl_seconds = int(ttl_seconds or os.environ.get("BENEFITS_SESSION_TTL_SECONDS") or DEFAULT_TTL_SECONDS)
        self.key_prefix = key_prefix
        self.client = client or redis.Redis.from_url(self.url, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}{safe_session_id(session_id)}"

    def get(self, session_id: str) -> SessionRecord | None:
        raw = self.client.get(self._key(session_id))
        return SessionRecord.from_dict(json.loads(raw)) if raw else None

    def put(self, rec: SessionRecord) -> None:
        self.client.set(self._key(rec.session_id), json.dumps(rec.to_dict(), default=str), ex=self.ttl_seconds)

    def delete(self, session_id: str) -> None:
        self.client.delete(self._key(session_id))

    def list_ids(self) -> list[str]:
        ids = []
        for key in self.client.scan_iter(match=f"{self.key_prefix}*", count=200):
            raw = self.client.get(key)
            if raw:
                try:
                    ids.append(json.loads(raw).get("session_id") or key[len(self.key_prefix):])
                    continue
                except ValueError:
                    pass
            ids.append(key[len(self.key_prefix):])
        return sorted(ids)

    def __repr__(self) -> str:
        return f"RedisSessionStore({self.url}, ttl={self.ttl_seconds}s)"


# ---------------------------------------------------------------------------
# Cosmos DB store: multi-region, Entra only
# ---------------------------------------------------------------------------
class CosmosSessionStore:
    """azure-cosmos backed store. Container partitioned on /session_id, item id = session_id.

    Env: BENEFITS_COSMOS_ENDPOINT (https://<account>.documents.azure.com:443/), BENEFITS_COSMOS_DB (default benefits),
    BENEFITS_COSMOS_CONTAINER (default sessions). Auth is DefaultAzureCredential (az login locally, managed identity in
    the hosted container); the identity needs the Cosmos DB Built-in Data Contributor role on the account.
    Idle sessions expire with BENEFITS_SESSION_TTL_SECONDS through the item-level `ttl` field, which only takes effect
    when the container has default TTL enabled (any value, including -1).
    """

    kind = "cosmos"

    def __init__(self, endpoint: str | None = None, database: str | None = None, container: str | None = None,
                 ttl_seconds: int | None = None, credential=None):
        # VERIFY against https://learn.microsoft.com/azure/cosmos-db/nosql/quickstart-python before delivery:
        # CosmosClient(url, credential=TokenCredential) and get_database_client / get_container_client names.
        from azure.cosmos import CosmosClient                # lazy: only when this backend is chosen
        from azure.identity import DefaultAzureCredential

        self.endpoint = endpoint or os.environ.get("BENEFITS_COSMOS_ENDPOINT", "")
        if not self.endpoint:
            raise RuntimeError("BENEFITS_COSMOS_ENDPOINT is not set")
        self.database = database or os.environ.get("BENEFITS_COSMOS_DB", "benefits")
        self.container_name = container or os.environ.get("BENEFITS_COSMOS_CONTAINER", "sessions")
        self.ttl_seconds = int(ttl_seconds or os.environ.get("BENEFITS_SESSION_TTL_SECONDS") or DEFAULT_TTL_SECONDS)
        client = CosmosClient(self.endpoint, credential=credential or DefaultAzureCredential())
        self.container = client.get_database_client(self.database).get_container_client(self.container_name)

    def get(self, session_id: str) -> SessionRecord | None:
        from azure.cosmos import exceptions

        try:
            item = self.container.read_item(item=safe_session_id(session_id), partition_key=safe_session_id(session_id))
        except exceptions.CosmosResourceNotFoundError:
            return None
        return SessionRecord.from_dict(item)

    def put(self, rec: SessionRecord) -> None:
        item = {**rec.to_dict(), "id": safe_session_id(rec.session_id), "ttl": self.ttl_seconds}
        item["session_id"] = item["id"]                       # partition key value must equal what get() uses
        self.container.upsert_item(item)

    def delete(self, session_id: str) -> None:
        from azure.cosmos import exceptions

        try:
            self.container.delete_item(item=safe_session_id(session_id), partition_key=safe_session_id(session_id))
        except exceptions.CosmosResourceNotFoundError:
            pass

    def list_ids(self) -> list[str]:
        # VERIFY: query_items(query=..., enable_cross_partition_query=True) is the azure-cosmos 4.x signature.
        rows = self.container.query_items(query="SELECT c.session_id FROM c", enable_cross_partition_query=True)
        return sorted(row["session_id"] for row in rows)

    def __repr__(self) -> str:
        return f"CosmosSessionStore({self.endpoint}, {self.database}/{self.container_name})"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def get_session_store(default_dir: Path | str) -> SessionStore:
    """Redis when BENEFITS_REDIS_URL is set, Cosmos when BENEFITS_COSMOS_ENDPOINT is set, otherwise files in default_dir.

    The lab scripts print the chosen backend so the room can see which resiliency story is in play.
    """
    if os.environ.get("BENEFITS_REDIS_URL"):
        return RedisSessionStore(os.environ["BENEFITS_REDIS_URL"])
    if os.environ.get("BENEFITS_COSMOS_ENDPOINT"):
        return CosmosSessionStore(os.environ["BENEFITS_COSMOS_ENDPOINT"])
    return FileSessionStore(default_dir)


def describe(store: SessionStore) -> str:
    """One line for lab logs: `file (artifacts/lab1/sessions)`, `redis (redis://...)`, `cosmos (...)`."""
    kind = getattr(store, "kind", type(store).__name__)
    target = getattr(store, "directory", None) or getattr(store, "url", None) or getattr(store, "endpoint", "")
    return f"{kind} ({target})"


# ---------------------------------------------------------------------------
# Self-test: file store only, no network, no packages
# ---------------------------------------------------------------------------
def _selftest() -> int:
    import shutil

    scratch = Path(__file__).resolve().parent / ".session_store_selftest"
    shutil.rmtree(scratch, ignore_errors=True)
    store = get_session_store(scratch)
    failures = []

    def check(name: str, ok: bool) -> None:
        print(f"[session_store] {'ok  ' if ok else 'FAIL'} {name}")
        if not ok:
            failures.append(name)

    check("factory picks file store when no BENEFITS_REDIS_URL / BENEFITS_COSMOS_ENDPOINT", isinstance(store, FileSessionStore))
    check("FileSessionStore satisfies the SessionStore protocol", isinstance(store, SessionStore))
    check("empty store lists nothing", store.list_ids() == [])
    check("get of unknown id is None", store.get("nope") is None)

    rec = SessionRecord.new("S1-evelyn", agent_name="benefits-concierge", participant_id="P-1001", agent_version="3", scenario="S1")
    rec.conversation_id = "conv_local_test"
    store.put(rec.touch(response_id="resp_1"))
    store.put(rec.touch(response_id="resp_2"))
    loaded = store.get("S1-evelyn")
    check("round trip keeps every field", loaded is not None and loaded.to_dict() == rec.to_dict())
    check("turn_count counted two turns", loaded is not None and loaded.turn_count == 2)
    check("last_response_id is the latest", loaded is not None and loaded.last_response_id == "resp_2")
    check("notes survive", loaded is not None and loaded.notes == {"scenario": "S1"})
    check("list_ids shows the session", store.list_ids() == ["S1-evelyn"])

    weird = SessionRecord.new("call/2026-10-06 12:00", agent_name="benefits-concierge")
    store.put(weird)
    check("unsafe ids are sanitised for the file name", (scratch / "call_2026-10-06_12_00.json").is_file())
    check("from_dict ignores unknown keys", SessionRecord.from_dict({**rec.to_dict(), "extra": 1}).session_id == "S1-evelyn")

    store.delete("S1-evelyn")
    store.delete("call/2026-10-06 12:00")
    check("delete removes the files", store.list_ids() == [] and store.get("S1-evelyn") is None)

    shutil.rmtree(scratch, ignore_errors=True)
    print(f"[session_store] backend for this run: {describe(store)}")
    print(f"[session_store] {'PASS' if not failures else 'FAIL: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
