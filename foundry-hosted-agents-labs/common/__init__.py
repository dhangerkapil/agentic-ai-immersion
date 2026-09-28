"""Shared helpers for the Foundry Hosted Agents Labs.

Every lab driver script imports these modules the same way:

    import sys; from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]      # foundry-hosted-agents-labs/
    sys.path.insert(0, str(ROOT))
    from common import benefits_data, foundry_env, guardrails

* benefits_data     pure-Python access to the synthetic systems of record in data/*.json
* foundry_env  .env loading and Azure client factories (Azure SDKs imported lazily)
* guardrails   compliance instruction block, PII redaction, recommendation heuristic
* session_store  session map (file, Redis, Cosmos) for resilient clients and hosted agents
* message_store  chat history outside the container (file, Redis) for hosted agents

Nothing in this package calls Azure at import time, so `python common/benefits_data.py`
runs on a machine with no Azure packages installed.
"""

from __future__ import annotations

__all__ = ["benefits_data", "foundry_env", "guardrails", "session_store", "message_store"]
__version__ = "1.0.0"
