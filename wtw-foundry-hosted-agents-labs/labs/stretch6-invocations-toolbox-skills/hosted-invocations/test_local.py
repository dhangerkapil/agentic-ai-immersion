"""Smoke test for via-claims-review-invocations (Stretch 6).

    python test_local.py                    POST one batch to the local InvocationsHostServer (http://localhost:8088)
    python test_local.py --base http://host:8088
    python test_local.py --offline          no server, no model: run claims_review directly and check the packets
Exit code 0 when every claim in the batch came back, the denied claim has a fix and accepted documents, and no
PII or recommendation language leaked; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for folder in (HERE.parents[2] if len(HERE.parents) > 2 else HERE, HERE):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
from common import guardrails  # noqa: E402

from claims_review import review_claims  # noqa: E402

CLAIM_IDS = ["CLM-9003", "CLM-9021", "CLM-9001"]
# VERIFY against https://learn.microsoft.com/azure/ai-foundry/agents/concepts/hosted-agents before delivery: the
# path InvocationsHostServer serves. The base repo README only confirms the JSON body {"message": "..."}.
PATH_CANDIDATES = [os.environ.get("VIA_INVOCATIONS_PATH", "/invocations"), "/invoke", "/"]


def extract_reviews(payload) -> list[dict]:
    """The response envelope is not verified: accept a dict with reviews, a dict with output/text, or a string."""
    if isinstance(payload, str):
        text = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("reviews"), list):
            return payload["reviews"]
        text = payload.get("output_text") or payload.get("text") or payload.get("output") or payload.get("message") or json.dumps(payload)
        if isinstance(text, list):
            text = json.dumps(text)
    else:
        text = json.dumps(payload)
    text = str(text).strip()
    for candidate in (text, text[text.find("{"): text.rfind("}") + 1]):
        try:
            data = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(data, dict) and isinstance(data.get("reviews"), list):
            return data["reviews"]
    return []


def call_local(base: str, claim_ids: list[str]) -> list[dict]:
    import httpx

    body = {"message": json.dumps({"claim_ids": claim_ids})}
    last_error = None
    for path in PATH_CANDIDATES:
        response = httpx.post(f"{base.rstrip('/')}{path}", json=body, timeout=180.0)
        if response.status_code == 404:
            last_error = f"404 at {path}"
            continue
        response.raise_for_status()
        print(f"[invocations-test] served at {path}")
        try:
            return extract_reviews(response.json())
        except ValueError:
            return extract_reviews(response.text)
    raise SystemExit(f"[invocations-test] no invocations path answered ({last_error}); set VIA_INVOCATIONS_PATH")


def check(reviews: list[dict], claim_ids: list[str]) -> bool:
    by_id = {review.get("claim_id"): review for review in reviews}
    ok = all(claim_id in by_id for claim_id in claim_ids)
    denied = by_id.get("CLM-9003", {})
    ok = ok and denied.get("review") == "resubmit" and len(denied.get("accepted_proof_of_payment") or []) >= 4
    text = json.dumps(reviews)
    leaks = guardrails.redact_pii(text) != text
    recommends = guardrails.contains_recommendation(text)
    print(f"[invocations-test] claims back: {sorted(by_id)}  denied fix: {denied.get('review')}  pii leak: {leaks}  recommendation: {recommends}")
    for review in reviews:
        if review.get("participant_explanation"):
            print(f"[invocations-test] {review['claim_id']}> {review['participant_explanation']}")
    return ok and not leaks and not recommends


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="http://localhost:8088")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    reviews = review_claims(CLAIM_IDS) if args.offline else call_local(args.base, CLAIM_IDS)
    ok = check(reviews, CLAIM_IDS)
    print(f"[invocations-test] {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
