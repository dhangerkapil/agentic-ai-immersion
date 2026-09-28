"""Deterministic denied-claim review (Stretch 6). Pure Python: no model, no Azure.

review_claims(["CLM-9003", ...]) -> one review packet per claim, built from benefits_data.get_claim_status and the
KB-ACC-001 text (accepted proof-of-payment list, not-accepted list, denial reason fixes). The Invocations agent
in main.py exposes this as a tool and adds a plain-language participant_explanation per claim; test_local.py
and the lab driver's --offline mode call it directly.

    python claims_review.py CLM-9003 CLM-9021 CLM-9001
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
for folder in (HERE.parents[2] if len(HERE.parents) > 2 else HERE, HERE):     # repo root, then vendored copies
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
from common import guardrails, benefits_data  # noqa: E402

KB_DOC_ID = "KB-ACC-001"
FIXABLE = {"missing_proof_of_payment", "missing_service_date", "provider_not_identified", "illegible_documentation"}
_rules_cache: dict | None = None


def _bullets_after(body: str, heading_line: str) -> list[str]:
    """The '- ' bullets that follow a line starting with heading_line (blank lines before the list are skipped;
    the list ends at the first blank line after it starts)."""
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower().startswith(heading_line.lower()):
            out = []
            for item in lines[index + 1:]:
                if not item.strip():
                    if out:
                        break
                    continue
                if item.strip().startswith("- "):
                    out.append(item.strip()[2:].strip())
                elif out:
                    break
            return out
    return []


def hra_rules() -> dict:
    """Parse KB-ACC-001 once: proof-of-payment lists and the denial reason table."""
    global _rules_cache
    if _rules_cache is None:
        text = benefits_data.read_knowledge_doc(KB_DOC_ID)
        meta, body = benefits_data.split_frontmatter(text)
        not_accepted = ""
        match = re.search(r"Not accepted as proof of payment:\s*(.+)", body)
        if match:
            not_accepted = match.group(1).strip().rstrip(".")
        reasons = {}
        for bullet in _bullets_after(body, "Each denied claim carries a reason code"):
            code, _, rest = bullet.partition(":")
            reasons[code.strip().strip("`")] = rest.strip()
        _rules_cache = {
            "doc_id": meta.get("doc_id", KB_DOC_ID), "title": meta.get("title", "HRA Reimbursement Rules"),
            "last_reviewed": meta.get("last_reviewed"),
            "proof_of_expense": _bullets_after(body, "Proof of expense, one of"),
            "proof_of_payment": _bullets_after(body, "Proof of payment, one of"),
            "not_accepted": not_accepted,                          # one sentence from the KB; commas are part of the items
            "denial_reasons": reasons,
        }
    return _rules_cache


def review_claim(claim_id: str) -> dict:
    """One review packet. Denied claims get the reason, the fix and the accepted documents; others get the status."""
    status = benefits_data.get_claim_status(claim_id)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if "error" in status:
        return {"claim_id": claim_id.strip().upper(), "error": status["error"], "reviewed_at": now}
    rules = hra_rules()
    code = status.get("reason")
    packet = {
        "claim_id": status["claim_id"], "participant_id": status["participant_id"], "hra_account_id": status["hra_account_id"],
        "status": status["status"], "type": status.get("type"), "amount": status.get("amount"), "submitted": status.get("submitted"),
        "denial_reason_code": code, "denial_reason_text": status.get("reason_text"),
        "kb_rule": rules["denial_reasons"].get(code) if code else None,
        "fix_available": bool(code and code in FIXABLE),
        "accepted_proof_of_payment": rules["proof_of_payment"] if code == "missing_proof_of_payment" else [],
        "not_accepted_as_proof": rules["not_accepted"] if code == "missing_proof_of_payment" else "",
        "resubmission_steps": [],
        "advisor_action_required": False,
        "knowledge_ref": f"[{rules['doc_id']}]",
        "reviewed_at": now,
    }
    if status["status"] == "denied":
        if packet["fix_available"]:
            packet["resubmission_steps"] = [
                "Participant sends the missing document as a new claim that references the original claim id, or replies to the denial notice in the portal.",
                "Agent flags the claim for resubmission follow-up. Agents cannot upload documents for the participant.",
                "Most claims are reviewed within five business days; payment follows two to three business days after approval.",
            ]
            packet["review"] = "resubmit"
        else:
            packet["review"] = "no_fix"
            packet["advisor_action_required"] = True                 # the participant may dispute; a human explains
    elif status["status"] == "pending":
        packet["review"] = "in_review"
    else:
        packet["review"] = "not_denied"
    return packet


def review_claims(claim_ids: list[str]) -> list[dict]:
    return [review_claim(claim_id) for claim_id in claim_ids]


def redact_packet(packet: dict) -> dict:
    return json.loads(guardrails.redact_pii(json.dumps(packet, default=str)))


if __name__ == "__main__":
    ids = sys.argv[1:] or ["CLM-9003", "CLM-9021", "CLM-9001", "CLM-0000"]
    packets = review_claims(ids)
    print(json.dumps(packets, indent=2, default=str))
    assert packets[0]["review"] == "resubmit" and len(packets[0]["accepted_proof_of_payment"]) >= 4, packets[0]
    assert packets[1]["review"] == "no_fix" and packets[1]["advisor_action_required"]
    assert packets[2]["review"] == "not_denied" and "error" in packets[3]
    print(f"[claims-review] PASS ({len(packets)} packets, rules from {hra_rules()['doc_id']} reviewed {hra_rules()['last_reviewed']})")
