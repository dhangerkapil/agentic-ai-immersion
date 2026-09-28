"""Chat message store for Agent Framework sessions (Lab 2 imports it; Lab 3 and S6 reuse the helpers).

Hosted agents are stateless containers by design. If the conversation history lives inside the process, a
restart, a version roll or a second replica loses the participant mid-call. This module keeps the history
OUTSIDE the container, keyed by session id, with two interchangeable backends:

* RedisMessageStore   redis-py, key via:messages:<session_id> (a Redis list, one JSON message per entry),
                      TTL VIA_SESSION_TTL_SECONDS (default 7 days). Shared by every replica.
* FileMessageStore    <dir>/<session_id>.messages.json. One laptop, the "kill it and restart" demo.

Plus the glue Agent Framework needs:

* serialize_messages / deserialize_messages   Message objects <-> JSON friendly dicts
* get_message_store(default_dir)              Redis when VIA_REDIS_URL is set, otherwise files
* as_history_provider(store)                  wraps a store as an Agent Framework history (context) provider
* build_history_provider(default_dir)         RedisHistoryProvider when VIA_REDIS_URL is set (the base repo
                                              threads/2 pattern), otherwise the file store wrapped by
                                              as_history_provider

Pattern source: base repo notebook agent-framework/threads/2-redis-chat-message-store-thread.ipynb, which
confirms `from agent_framework.redis import RedisHistoryProvider`, `RedisHistoryProvider(redis_url=...,
key_prefix=...)`, `Agent(..., context_providers=[provider])`, `agent.create_session(session_id=...)`,
`await provider.get_messages(session_id)`, `await provider.clear(session_id)`, `await provider.aclose()`.

No agent_framework or redis import happens at module import time. `python common/message_store.py` runs the
file-backend self-test on a machine with nothing installed.

Usage (hosted main.py):
    from common import message_store
    provider = message_store.build_history_provider(HERE / "message_store")
    agent = Agent(client=client, instructions=..., tools=..., context_providers=[provider],
                  default_options={"store": False})
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable

DEFAULT_TTL_SECONDS = 7 * 24 * 3600
DEFAULT_MAX_MESSAGES = 200
REDIS_KEY_PREFIX = "via:messages"
FILE_SUFFIX = ".messages.json"


def _safe_id(session_id: str) -> str:
    from common.session_store import safe_session_id   # same sanitiser as the session map

    return safe_session_id(session_id)


# ---------------------------------------------------------------------------
# Serialization: Message objects <-> dicts
# ---------------------------------------------------------------------------
def message_to_dict(message: Any) -> dict:
    """One message as a JSON friendly dict. Accepts Agent Framework Message objects or plain dicts."""
    if isinstance(message, dict):
        return dict(message)
    for attr in ("to_dict", "model_dump"):
        method = getattr(message, attr, None)
        if callable(method):
            try:
                data = method()
                if isinstance(data, dict):
                    return data
            except TypeError:
                continue
    return {"role": str(getattr(message, "role", "user")), "text": getattr(message, "text", str(message))}


def message_from_dict(data: dict) -> Any:
    """Rebuild a Message when agent_framework is installed, otherwise return the dict unchanged."""
    try:
        from agent_framework import Message
    except ImportError:
        return dict(data)
    # VERIFY against https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.message
    # before delivery: Message.from_dict is the SerializationMixin name in agent-framework 1.x; the fallback
    # below rebuilds a text-only message from role + text (or the text parts of `contents`).
    if hasattr(Message, "from_dict"):
        try:
            return Message.from_dict(data)
        except Exception:  # noqa: BLE001
            pass
    role = data.get("role", "user")
    text = data.get("text") or " ".join(
        part.get("text", "") for part in data.get("contents", []) if isinstance(part, dict) and part.get("text"))
    return Message(role, text=text)


def serialize_messages(messages: Iterable[Any]) -> list[dict]:
    return [message_to_dict(message) for message in messages]


def deserialize_messages(rows: Iterable[dict]) -> list[Any]:
    return [message_from_dict(row) for row in rows]


def message_text(message: Any) -> str:
    """Plain text of a message or dict, for transcripts and tests."""
    if isinstance(message, dict):
        return message.get("text") or " ".join(
            part.get("text", "") for part in message.get("contents", []) if isinstance(part, dict)) or ""
    return getattr(message, "text", "") or ""


def message_role(message: Any) -> str:
    role = message.get("role") if isinstance(message, dict) else getattr(message, "role", "user")
    value = getattr(role, "value", role)
    return str(value)


# ---------------------------------------------------------------------------
# The store contract (synchronous, plain Python)
# ---------------------------------------------------------------------------
@runtime_checkable
class MessageStore(Protocol):
    def get_messages(self, session_id: str) -> list[dict]: ...
    def add_messages(self, session_id: str, messages: Iterable[Any]) -> None: ...
    def clear(self, session_id: str) -> None: ...
    def list_session_ids(self) -> list[str]: ...


class FileMessageStore:
    """<directory>/<session_id>.messages.json holding a JSON list of messages. Not shared across replicas."""

    kind = "file"

    def __init__(self, directory: Path | str, max_messages: int = DEFAULT_MAX_MESSAGES):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.max_messages = max_messages

    def _path(self, session_id: str) -> Path:
        return self.directory / f"{_safe_id(session_id)}{FILE_SUFFIX}"

    def get_messages(self, session_id: str) -> list[dict]:
        path = self._path(session_id)
        if not path.is_file():
            return []
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return []
        return list(rows)[-self.max_messages:] if isinstance(rows, list) else []

    def add_messages(self, session_id: str, messages: Iterable[Any]) -> None:
        rows = self.get_messages(session_id) + serialize_messages(messages)
        rows = rows[-self.max_messages:]
        path = self._path(session_id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(rows, indent=2, default=str) + "\n", encoding="utf-8")
        tmp.replace(path)                                    # atomic on the same file system

    def clear(self, session_id: str) -> None:
        path = self._path(session_id)
        if path.is_file():
            path.unlink()

    def list_session_ids(self) -> list[str]:
        return sorted(path.name[: -len(FILE_SUFFIX)] for path in self.directory.glob(f"*{FILE_SUFFIX}"))

    def __repr__(self) -> str:
        return f"FileMessageStore({self.directory})"


class RedisMessageStore:
    """redis-py backed store. Key via:messages:<session_id> is a list; every write refreshes the TTL.

    Local Redis for the workshop: docker run -d --name redis-workshop -p 6379:6379 redis:7-alpine and
    VIA_REDIS_URL=redis://localhost:6379/0. Azure Managed Redis with Entra: a rediss:// URL and a
    token-refreshing client passed through `client`.
    """

    kind = "redis"

    def __init__(self, url: str | None = None, ttl_seconds: int | None = None, client=None,
                 key_prefix: str = REDIS_KEY_PREFIX, max_messages: int = DEFAULT_MAX_MESSAGES):
        import redis                                         # lazy: only when this backend is chosen

        self.url = url or os.environ.get("VIA_REDIS_URL", "redis://localhost:6379/0")
        self.ttl_seconds = int(ttl_seconds or os.environ.get("VIA_SESSION_TTL_SECONDS") or DEFAULT_TTL_SECONDS)
        self.key_prefix = key_prefix.rstrip(":")
        self.max_messages = max_messages
        self.client = client or redis.Redis.from_url(self.url, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}:{_safe_id(session_id)}"

    def get_messages(self, session_id: str) -> list[dict]:
        rows = self.client.lrange(self._key(session_id), -self.max_messages, -1)
        out = []
        for raw in rows:
            try:
                out.append(json.loads(raw))
            except ValueError:
                continue
        return out

    def add_messages(self, session_id: str, messages: Iterable[Any]) -> None:
        rows = [json.dumps(row, default=str) for row in serialize_messages(messages)]
        if not rows:
            return
        key = self._key(session_id)
        pipe = self.client.pipeline()
        pipe.rpush(key, *rows)
        pipe.ltrim(key, -self.max_messages, -1)
        pipe.expire(key, self.ttl_seconds)
        pipe.execute()

    def clear(self, session_id: str) -> None:
        self.client.delete(self._key(session_id))

    def list_session_ids(self) -> list[str]:
        prefix = f"{self.key_prefix}:"
        return sorted(key[len(prefix):] for key in self.client.scan_iter(match=f"{prefix}*", count=200))

    def __repr__(self) -> str:
        return f"RedisMessageStore({self.url}, ttl={self.ttl_seconds}s)"


def get_message_store(default_dir: Path | str) -> MessageStore:
    """Redis when VIA_REDIS_URL is set, otherwise JSON files in default_dir."""
    if os.environ.get("VIA_REDIS_URL"):
        return RedisMessageStore(os.environ["VIA_REDIS_URL"])
    return FileMessageStore(default_dir)


def describe(store: Any) -> str:
    kind = getattr(store, "kind", type(store).__name__)
    target = getattr(store, "directory", None) or getattr(store, "url", None) or getattr(store, "redis_url", "")
    return f"{kind} ({target})"


# ---------------------------------------------------------------------------
# Agent Framework glue: a store becomes a history provider the Agent reads before and writes after a run
# ---------------------------------------------------------------------------
def as_history_provider(store: MessageStore, **kwargs):
    """Wrap a MessageStore as an Agent Framework history provider (same contract RedisHistoryProvider has).

    Imported lazily so this module stays importable without agent_framework.
    """
    try:
        # VERIFY against https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/conversation-storage
        # before delivery: BaseHistoryProvider is the abstract base RedisHistoryProvider implements
        # (async get_messages / add_messages / clear keyed by session_id). If the installed build names it
        # differently, subclass that instead.
        from agent_framework import BaseHistoryProvider as _Base
    except ImportError:
        from agent_framework import BaseContextProvider as _Base  # type: ignore  # VERIFY: older builds

    class StoreHistoryProvider(_Base):
        """Adapter: the synchronous store behind the async provider interface."""

        def __init__(self, inner: MessageStore, **kw):
            super().__init__(**kw)
            self.store = inner

        async def get_messages(self, session_id: str, **kw) -> list:
            return deserialize_messages(self.store.get_messages(session_id))

        async def add_messages(self, session_id: str, messages, **kw) -> None:
            self.store.add_messages(session_id, messages)

        async def clear(self, session_id: str, **kw) -> None:
            self.store.clear(session_id)

        async def aclose(self) -> None:
            return None

        def __repr__(self) -> str:
            return f"StoreHistoryProvider({self.store!r})"

    return StoreHistoryProvider(store, **kwargs)


def build_history_provider(default_dir: Path | str, key_prefix: str = REDIS_KEY_PREFIX):
    """The provider a hosted main.py passes as context_providers=[...].

    Redis: the framework's own RedisHistoryProvider (verified in the base repo notebook threads/2).
    Otherwise: the file store wrapped by as_history_provider. Both are keyed by the session id, so a
    restarted container or another replica continues the same conversation.
    """
    redis_url = os.environ.get("VIA_REDIS_URL")
    if redis_url:
        from agent_framework.redis import RedisHistoryProvider

        # VERIFY: key_prefix produces keys "<key_prefix>:<session_id>"; max_messages is shown in the base repo
        # notebook for the older RedisChatMessageStore and may not exist on RedisHistoryProvider.
        return RedisHistoryProvider(redis_url=redis_url, key_prefix=key_prefix)
    return as_history_provider(FileMessageStore(default_dir))


# ---------------------------------------------------------------------------
# Self-test: file store only, plain dict messages, no packages
# ---------------------------------------------------------------------------
def _selftest() -> int:
    import shutil

    scratch = Path(__file__).resolve().parent / ".message_store_selftest"
    shutil.rmtree(scratch, ignore_errors=True)
    os.environ.pop("VIA_REDIS_URL", None)
    store = get_message_store(scratch)
    failures = []

    def check(name: str, ok: bool) -> None:
        print(f"[message_store] {'ok  ' if ok else 'FAIL'} {name}")
        if not ok:
            failures.append(name)

    check("factory picks the file store when VIA_REDIS_URL is unset", isinstance(store, FileMessageStore))
    check("FileMessageStore satisfies the MessageStore protocol", isinstance(store, MessageStore))
    check("unknown session has no messages", store.get_messages("nope") == [])

    turn1 = [{"role": "user", "text": "Hi, this is P-1001, ZIP 84095."},
             {"role": "assistant", "text": "Thanks Evelyn. How can I help today?"}]
    turn2 = [{"role": "user", "text": "When can I change my plan?"},
             {"role": "assistant", "text": "Your window is AEP, Oct 15 to Dec 7 [KB-MKT-001]."}]
    store.add_messages("S1-evelyn", turn1)
    store.add_messages("S1-evelyn", turn2)
    rows = store.get_messages("S1-evelyn")
    check("two turns append to four messages", len(rows) == 4)
    check("order is preserved", [message_role(r) for r in rows] == ["user", "assistant", "user", "assistant"])
    check("text survives the round trip", message_text(rows[-1]).startswith("Your window is AEP"))
    check("file name uses the .messages.json suffix", (scratch / "S1-evelyn.messages.json").is_file())
    check("list_session_ids shows the session", store.list_session_ids() == ["S1-evelyn"])

    round_trip = deserialize_messages(serialize_messages(rows))
    check("serialize/deserialize keep the count", len(round_trip) == 4)
    check("serialize/deserialize keep the text", message_text(round_trip[0]) == turn1[0]["text"])

    small = FileMessageStore(scratch / "trim", max_messages=3)
    small.add_messages("s", turn1 + turn2)
    check("max_messages trims the oldest", [message_text(r) for r in small.get_messages("s")] == [message_text(r) for r in (turn1 + turn2)[-3:]])

    store.add_messages("call/2026-10-06 12:00", turn1)
    check("unsafe ids are sanitised for the file name", (scratch / "call_2026-10-06_12_00.messages.json").is_file())

    store.clear("S1-evelyn")
    store.clear("call/2026-10-06 12:00")
    check("clear removes the files", store.get_messages("S1-evelyn") == [] and store.list_session_ids() == [])

    shutil.rmtree(scratch, ignore_errors=True)
    print(f"[message_store] backend for this run: {describe(store)}")
    print(f"[message_store] {'PASS' if not failures else 'FAIL: ' + ', '.join(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))    # so `from common.session_store` works when run directly
    raise SystemExit(_selftest())
