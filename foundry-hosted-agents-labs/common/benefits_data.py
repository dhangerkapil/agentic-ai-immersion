"""Benefits Marketplace synthetic systems of record: pure-Python access to data/*.json.

Every agent (Agent Framework @tool functions in the hosted containers, Foundry Agent Service FunctionTools in
Stretch 5) calls these functions. There are no Azure calls here, so this module runs anywhere:

    python common/benefits_data.py        # self-test over the S1 / S2 / S3 scenarios

Data lives in ../data relative to this file (participants, sponsors, plans, hra_accounts, knowledge/*.md).
All records are synthetic. Functions never raise for a missing record; they return {"error": "..."} so a
tool-calling loop can hand the problem back to the model instead of crashing.

Public surface (exact signatures are part of the shared brief):
    get_participant, get_sponsor, search_plans, compare_plans, get_hra_account, get_claim_status,
    list_eligible_expenses, get_enrollment_window, list_knowledge_docs, read_knowledge_doc, redact_pii,
    TOOL_REGISTRY (name -> function), TOOL_SCHEMAS (OpenAI JSON schemas for the 8 tools)
"""

from __future__ import annotations

import calendar
import copy
import json
import os
import sys
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Callable

if __package__ in (None, ""):                       # `python common/benefits_data.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import guardrails  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]           # foundry-hosted-agents-labs/
DATA_DIR = ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
BENEFITS_TODAY_DEFAULT = "2026-10-06"

PLAN_TYPES = ["Medicare Advantage HMO", "Medicare Advantage PPO", "Medigap Plan G", "Medigap Plan N",
              "Part D", "ACA Bronze", "ACA Silver", "ACA Gold"]
COMPARISON_FIELDS = ["plan_id", "carrier", "plan_name", "plan_type", "premium_monthly", "deductible_annual",
                     "max_out_of_pocket", "star_rating", "network_type", "drug_coverage",
                     "formulary_tier_examples", "dental_vision", "highlights"]
DENIAL_REASON_TEXT = {
    "missing_proof_of_payment": "Proof of the expense was received, but nothing shows that the bill was paid. "
                                "Resubmit with an accepted proof of payment (bank or card statement, cancelled "
                                "check, receipt marked paid, or carrier statement showing payment received) and "
                                "reference the original claim id.",
    "expense_not_eligible": "The expense category is not on the sponsor's list of eligible expenses. "
                            "There is no fix for that expense under this sponsor.",
    "duplicate_claim": "A claim for the same expense, date and amount was already paid.",
    "outside_plan_year": "The service date or coverage month falls outside the account's plan year, or the "
                         "run-out period has passed.",
    "missing_service_date": "The document does not show the date of service or the coverage month.",
    "provider_not_identified": "The document does not show who provided the service or which carrier billed "
                               "the premium.",
    "illegible_documentation": "The upload could not be read. Re-scan and resubmit.",
}
SEP_QUALIFYING_EVENTS = [
    "moved out of the plan's service area (or moved into a new one)",
    "lost employer or union coverage",
    "current plan is leaving Medicare or the service area",
    "qualified for Extra Help or Medicaid (dual eligibility)",
    "moved into or out of a nursing home or long-term care facility",
    "a 5-star plan is available in the county (once per year)",
    "released from incarceration or returned from living abroad",
]
REQUIRED_KNOWLEDGE_DOC_IDS = {"KB-MKT-001", "KB-MKT-002", "KB-MKT-003", "KB-MKT-004",
                              "KB-ACC-001", "KB-ACC-002", "KB-ACC-003", "KB-UNI-001", "KB-UNI-002"}
ACA_QUALIFYING_EVENTS = [
    "lost other health coverage (job loss, aging off a parent's plan, COBRA ending)",
    "moved to a new county or state",
    "got married, divorced, or had a child",
    "household income change that changes subsidy eligibility",
    "became a U.S. citizen or lawful resident",
]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
@lru_cache(maxsize=None)
def _load(name: str) -> list[dict]:
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing. The data folder ships with the workshop; check your checkout.")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def reload() -> None:
    """Drop the JSON cache (call after editing data/*.json in a running process)."""
    _load.cache_clear()
    _knowledge_index.cache_clear()


def _norm_id(value: str | None) -> str:
    return (value or "").strip().upper()


def _find(name: str, key: str, value: str) -> dict | None:
    wanted = _norm_id(value)
    for record in _load(name):
        if _norm_id(record.get(key)) == wanted:
            return copy.deepcopy(record)
    return None


def _error(message: str) -> dict:
    return {"error": message}


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def today_date(today: str | None = None) -> date:
    """Resolve the workshop 'today': explicit argument, then BENEFITS_TODAY, then the brief's default."""
    return _parse_date(today) or _parse_date(os.environ.get("BENEFITS_TODAY")) or date.fromisoformat(BENEFITS_TODAY_DEFAULT)


# ---------------------------------------------------------------------------
# Participants and sponsors
# ---------------------------------------------------------------------------
def get_participant(participant_id: str) -> dict:
    """Participant profile by id (P-1001 style). Returns {"error": ...} when the id is unknown."""
    record = _find("participants", "participant_id", participant_id)
    if record is None:
        return _error(f"participant {_norm_id(participant_id) or '(blank)'} not found. Ids look like P-1001.")
    return record


def get_sponsor(sponsor_id: str) -> dict:
    """Plan sponsor record (HRA amounts, eligibility, eligible expense types)."""
    record = _find("sponsors", "sponsor_id", sponsor_id)
    if record is None:
        return _error(f"sponsor {_norm_id(sponsor_id) or '(blank)'} not found. Ids look like SP-NORTHWIND.")
    return record


def list_eligible_expenses(sponsor_id: str) -> list[str]:
    """Expense types the sponsor reimburses (for example premium, out_of_pocket, part_b_premium)."""
    sponsor = get_sponsor(sponsor_id)
    if "error" in sponsor:
        return [f"error: {sponsor['error']}"]
    return list(sponsor.get("eligible_expense_types", []))


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------
def _premium(plan: dict) -> float:
    return float(plan.get("premium_monthly") or 0.0)


def _stars(plan: dict) -> float:
    return float(plan.get("star_rating") or 0.0)


def _drug_tier(plan: dict, drug_name: str) -> str | None:
    wanted = drug_name.strip().lower()
    for name, tier in (plan.get("formulary_tier_examples") or {}).items():
        key = name.lower()
        if key == wanted or key in wanted or wanted in key:
            return tier
    return None


def search_plans(county: str, state: str = "UT", plan_type: str | None = None,
                 max_premium: float | None = None, needs_drug_coverage: bool | None = None,
                 drug_name: str | None = None) -> list[dict]:
    """Plans sold in a county, sorted by monthly premium then star rating (descending), at most 10.

    plan_type matches case-insensitively and by substring, so "Medicare Advantage" returns HMO and PPO plans
    and "Medigap" returns Plan G and Plan N. drug_name keeps only plans whose formulary examples list that
    drug and adds "drug_tier_for_query" to each hit.
    """
    county_l = (county or "").strip().lower()
    if not county_l:
        return [_error("county is required (for example Salt Lake, Utah, Davis, Weber).")]
    state_u = (state or "UT").strip().upper()
    type_l = (plan_type or "").strip().lower()
    drug = (drug_name or "").strip()
    hits: list[dict] = []
    for plan in _load("plans"):
        if plan.get("state", "UT").upper() != state_u:
            continue
        if county_l not in [c.lower() for c in plan.get("service_area_counties", [])]:
            continue
        if type_l and type_l not in plan.get("plan_type", "").lower():
            continue
        if max_premium is not None and _premium(plan) > float(max_premium):
            continue
        if needs_drug_coverage is not None and bool(plan.get("drug_coverage")) != bool(needs_drug_coverage):
            continue
        record = copy.deepcopy(plan)
        if drug:
            tier = _drug_tier(plan, drug)
            if tier is None:
                continue
            record["drug_tier_for_query"] = tier
        hits.append(record)
    hits.sort(key=lambda p: (_premium(p), -_stars(p), p["plan_id"]))
    return hits[:10]


def compare_plans(plan_ids: list[str]) -> dict:
    """Side-by-side view of 2 to 4 plans: {"plans": [...], "comparison_fields": [...], "not_found": [...]}."""
    if isinstance(plan_ids, str):
        plan_ids = [p for p in plan_ids.replace(";", ",").split(",") if p.strip()]
    wanted = [_norm_id(p) for p in (plan_ids or []) if _norm_id(p)]
    if not wanted:
        return _error("plan_ids must be a list of plan ids such as [\"MA-CONTOSO-HMO-01\", \"MA-FABRIKAM-PPO-01\"].")
    by_id = {p["plan_id"].upper(): p for p in _load("plans")}
    plans = [{field: copy.deepcopy(by_id[p].get(field)) for field in COMPARISON_FIELDS} for p in wanted if p in by_id]
    not_found = [p for p in wanted if p not in by_id]
    result = {"plans": plans, "comparison_fields": list(COMPARISON_FIELDS), "not_found": not_found}
    if not plans:
        result["error"] = f"none of the plan ids were found: {not_found}"
    return result


def get_plan(plan_id: str) -> dict:
    """One plan by id (convenience for labs; not part of the 8 shared tools)."""
    record = _find("plans", "plan_id", plan_id)
    return record if record else _error(f"plan {_norm_id(plan_id) or '(blank)'} not found.")


# ---------------------------------------------------------------------------
# HRA accounts and claims
# ---------------------------------------------------------------------------
def get_hra_account(participant_id: str) -> dict:
    """HRA account for a participant: allocation, balance, auto-reimbursement, debit card (last4 only),
    every claim, and a claims_summary with paid / pending / denied counts. Accepts an HRA id as well."""
    account = _find("hra_accounts", "participant_id", participant_id) or _find("hra_accounts", "hra_account_id", participant_id)
    if account is None:
        return _error(f"no HRA account for {_norm_id(participant_id) or '(blank)'}.")
    claims = account.get("claims", [])
    account["claims_summary"] = {status: sum(1 for c in claims if c.get("status") == status)
                                 for status in ("paid", "pending", "denied")}
    account["claims_summary"]["total_paid_amount"] = round(
        sum(float(c.get("amount") or 0) for c in claims if c.get("status") == "paid"), 2)
    denied = [c["claim_id"] for c in claims if c.get("status") == "denied"]
    if denied:
        account["claims_summary"]["denied_claim_ids"] = denied
    return account


def get_claim_status(claim_id: str) -> dict:
    """Status of one claim (CLM-9003 style) with a plain-language reason for denials."""
    wanted = _norm_id(claim_id)
    for account in _load("hra_accounts"):
        for claim in account.get("claims", []):
            if _norm_id(claim.get("claim_id")) == wanted:
                result = copy.deepcopy(claim)
                result["participant_id"] = account["participant_id"]
                result["hra_account_id"] = account["hra_account_id"]
                reason = claim.get("reason")
                result["reason_text"] = DENIAL_REASON_TEXT.get(reason, reason.replace("_", " ")) if reason else None
                if claim.get("status") == "denied":
                    result["next_step"] = ("The claim can be resubmitted with the missing item; reference the "
                                           "original claim id. An agent may flag it for resubmission follow-up "
                                           "but cannot upload documents for the participant.")
                    result["knowledge_ref"] = "KB-ACC-001"
                elif claim.get("status") == "pending":
                    result["next_step"] = "In the review queue. Most claims are reviewed within five business days."
                    result["knowledge_ref"] = "KB-ACC-001"
                return result
    return _error(f"claim {wanted or '(blank)'} not found. Claim ids look like CLM-9003.")


# ---------------------------------------------------------------------------
# Enrollment windows
# ---------------------------------------------------------------------------
def _month_start(d: date) -> date:
    return d.replace(day=1)


def _add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year, month = d.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def _month_end(d: date) -> date:
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def _iep_window(dob: date) -> tuple[date, date, date]:
    """(start, end, 65th birthday): the 7-month Initial Enrollment Period around the 65th birthday month."""
    try:
        birthday65 = dob.replace(year=dob.year + 65)
    except ValueError:                                  # Feb 29 birthdays
        birthday65 = dob.replace(year=dob.year + 65, day=28)
    return _month_start(_add_months(birthday65, -3)), _month_end(_add_months(birthday65, 3)), birthday65


def _aep_window(year: int) -> tuple[date, date]:
    return date(year, 10, 15), date(year, 12, 7)


def _next_aep(today: date) -> tuple[date, date]:
    start, end = _aep_window(today.year)
    return (start, end) if today <= end else _aep_window(today.year + 1)


def _aca_window(today: date) -> tuple[date, date]:
    """ACA open enrollment that is open or next to open: Nov 1 to Jan 15."""
    if today.month == 1 and today.day <= 15:
        return date(today.year - 1, 11, 1), date(today.year, 1, 15)
    return date(today.year, 11, 1), date(today.year + 1, 1, 15)


def get_enrollment_window(participant_id: str, today: str | None = None) -> dict:
    """Which enrollment window applies to the participant on `today` (ISO date, default BENEFITS_TODAY).

    window values: "IEP" (Medicare Initial Enrollment Period, 7 months around the 65th birthday month),
    "AEP" (Medicare Annual Enrollment, Oct 15 to Dec 7), "OEP" (Medicare Advantage Open Enrollment Jan 1 to
    Mar 31 for MA members, or ACA Open Enrollment Nov 1 to Jan 15 for pre-Medicare participants),
    "SEP-possible" (outside every scheduled window; a qualifying event is needed) or "none".
    starts / ends describe the active window; next_window says when the next scheduled window opens.
    """
    participant = get_participant(participant_id)
    if "error" in participant:
        return participant
    now = today_date(today)
    dob = _parse_date(participant.get("dob"))
    medicare = bool(participant.get("medicare_eligible"))
    current_type = (get_plan(participant["current_plan_id"]).get("plan_type", "")
                    if participant.get("current_plan_id") else "")
    base = {"participant_id": participant["participant_id"], "today": now.isoformat(), "medicare_eligible": medicare,
            "program": "Medicare" if medicare else "ACA"}

    iep = _iep_window(dob) if dob else None
    if iep:
        base["medicare_iep"] = {"starts": iep[0].isoformat(), "ends": iep[1].isoformat(),
                                "turns_65_on": iep[2].isoformat()}
        if iep[0] <= now <= iep[1]:
            return {**base, "window": "IEP", "program": "Medicare", "starts": iep[0].isoformat(),
                    "ends": iep[1].isoformat(),
                    "explanation": (f"Initial Enrollment Period: the 7 months around the 65th birthday month "
                                    f"({iep[2].isoformat()}). Runs {iep[0].isoformat()} to {iep[1].isoformat()}. "
                                    "Sign up for Part A and B, then choose Medicare Advantage, or Medigap plus "
                                    "Part D. Enrolling in the 3 months before the birthday month avoids a gap."),
                    "knowledge_ref": "KB-MKT-001"}

    if medicare:
        aep_start, aep_end = _aep_window(now.year)
        if aep_start <= now <= aep_end:
            return {**base, "window": "AEP", "starts": aep_start.isoformat(), "ends": aep_end.isoformat(),
                    "explanation": ("Annual Enrollment Period, October 15 to December 7. Join, switch or drop a "
                                    "Medicare Advantage or Part D plan; changes take effect January 1."),
                    "knowledge_ref": "KB-MKT-001"}
        if current_type.startswith("Medicare Advantage") and date(now.year, 1, 1) <= now <= date(now.year, 3, 31):
            return {**base, "window": "OEP", "starts": date(now.year, 1, 1).isoformat(),
                    "ends": date(now.year, 3, 31).isoformat(),
                    "explanation": ("Medicare Advantage Open Enrollment Period, January 1 to March 31. One change "
                                    "for people already on a Medicare Advantage plan: switch to another MA plan "
                                    "or return to Original Medicare with a Part D plan."),
                    "knowledge_ref": "KB-MKT-001"}
        nxt_start, nxt_end = _next_aep(now)
        days = (nxt_start - now).days
        return {**base, "window": "SEP-possible", "starts": None, "ends": None,
                "next_window": {"window": "AEP", "starts": nxt_start.isoformat(), "ends": nxt_end.isoformat(),
                                "days_until_start": days},
                "qualifying_events": list(SEP_QUALIFYING_EVENTS),
                "explanation": (f"No scheduled window is open today ({now.isoformat()}). The Annual Enrollment "
                                f"Period opens {nxt_start.isoformat()} and runs through {nxt_end.isoformat()} "
                                f"({days} days from today). Before then a change needs a Special Enrollment "
                                "Period qualifying event; a licensed benefit advisor confirms eligibility."),
                "knowledge_ref": "KB-MKT-001"}

    # Pre-Medicare: ACA open enrollment Nov 1 to Jan 15, otherwise SEP with qualifying events.
    aca_start, aca_end = _aca_window(now)
    if aca_start <= now <= aca_end:
        return {**base, "window": "OEP", "starts": aca_start.isoformat(), "ends": aca_end.isoformat(),
                "explanation": ("ACA Marketplace Open Enrollment, November 1 to January 15. Enroll by December 15 "
                                "for January 1 coverage; later enrollments start February 1."),
                "knowledge_ref": "KB-MKT-003"}
    days = (aca_start - now).days
    result = {**base, "window": "SEP-possible", "starts": None, "ends": None,
              "next_window": {"window": "OEP", "program": "ACA", "starts": aca_start.isoformat(),
                              "ends": aca_end.isoformat(), "days_until_start": days},
              "qualifying_events": list(ACA_QUALIFYING_EVENTS),
              "explanation": (f"Not Medicare eligible yet. ACA Open Enrollment opens {aca_start.isoformat()} and "
                              f"runs through {aca_end.isoformat()} ({days} days from today). Outside it, a change "
                              "needs a qualifying life event within the last 60 days."),
              "knowledge_ref": "KB-MKT-003"}
    if iep:
        result["explanation"] += (f" Medicare Initial Enrollment Period will run {iep[0].isoformat()} to "
                                  f"{iep[1].isoformat()} around the 65th birthday ({iep[2].isoformat()}).")
    return result


# ---------------------------------------------------------------------------
# Knowledge documents
# ---------------------------------------------------------------------------
def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split a Markdown doc into (frontmatter dict, body). Frontmatter is the leading `---` block."""
    meta: dict = {}
    if not text.startswith("---"):
        return meta, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return meta, text
    for line in parts[1].splitlines():
        if ":" in line and not line.strip().startswith("#"):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.split("#", 1)[0].strip().strip('"').strip("'")
    return meta, parts[2].lstrip("\n")


@lru_cache(maxsize=None)
def _knowledge_index() -> tuple[dict, ...]:
    docs = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        meta, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        docs.append({"doc_id": meta.get("doc_id", path.stem), "title": meta.get("title", path.stem),
                     "context": meta.get("context", "universal"),
                     "last_reviewed": meta.get("last_reviewed"), "path": str(path)})
    docs.sort(key=lambda d: d["doc_id"])
    return tuple(docs)


def list_knowledge_docs(context: str | None = None) -> list[dict]:
    """[{doc_id, title, context, last_reviewed, path}] for data/knowledge, optionally filtered by context
    (marketplace | accounts | universal)."""
    wanted = (context or "").strip().lower()
    return [dict(d) for d in _knowledge_index() if not wanted or d["context"].lower() == wanted]


def read_knowledge_doc(doc_id: str) -> str:
    """Full Markdown text (frontmatter included) of one knowledge doc, by doc_id such as KB-ACC-001."""
    wanted = _norm_id(doc_id)
    for doc in _knowledge_index():
        if doc["doc_id"].upper() == wanted:
            return Path(doc["path"]).read_text(encoding="utf-8")
    known = [d["doc_id"] for d in _knowledge_index()]
    raise FileNotFoundError(f"knowledge doc {doc_id!r} not found. Known ids: {known}")


def redact_pii(text: str) -> str:
    """Thin wrapper over guardrails.redact_pii so tool code has one import."""
    return guardrails.redact_pii(text)


# ---------------------------------------------------------------------------
# Tool registry and schemas (the 8 shared tools)
# ---------------------------------------------------------------------------
TOOL_REGISTRY: dict[str, Callable] = {
    "get_participant": get_participant,
    "get_sponsor": get_sponsor,
    "search_plans": search_plans,
    "compare_plans": compare_plans,
    "get_hra_account": get_hra_account,
    "get_claim_status": get_claim_status,
    "list_eligible_expenses": list_eligible_expenses,
    "get_enrollment_window": get_enrollment_window,
}


def _schema(name: str, description: str, properties: dict) -> dict:
    # Every property is listed in "required" and optional ones are nullable, which is what OpenAI strict
    # mode (strict=True) needs. Non-strict callers can still omit the nullable ones.
    return {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties,
                           "required": list(properties), "additionalProperties": False}}


_PID = {"type": "string", "description": "Participant id such as P-1001."}
TOOL_SCHEMAS: list[dict] = [
    _schema("get_participant",
            "Look up a Benefits Marketplace participant profile by participant_id: name, county, state, sponsor, "
            "Medicare eligibility, current plan, HRA account id and stated preferences.",
            {"participant_id": _PID}),
    _schema("get_sponsor",
            "Plan sponsor record: HRA annual amounts, eligibility rule, eligible expense types, rollover notes.",
            {"sponsor_id": {"type": "string", "description": "Sponsor id such as SP-NORTHWIND or SP-ADATUM."}}),
    _schema("search_plans",
            "Search individual plans sold in a county. Returns at most 10 plans sorted by monthly premium then "
            "star rating. Educational comparison data only; never use it to recommend a plan.",
            {"county": {"type": "string", "description": "County name, for example Salt Lake, Utah, Davis, Weber."},
             "state": {"type": ["string", "null"], "description": "Two-letter state code. Null means UT."},
             "plan_type": {"type": ["string", "null"],
                           "description": "Filter by plan type (substring match): Medicare Advantage HMO, "
                                          "Medicare Advantage PPO, Medigap Plan G, Medigap Plan N, Part D, "
                                          "ACA Bronze, ACA Silver, ACA Gold. Null for all types."},
             "max_premium": {"type": ["number", "null"], "description": "Maximum monthly premium in USD, or null."},
             "needs_drug_coverage": {"type": ["boolean", "null"],
                                     "description": "True to keep only plans with drug coverage, or null."},
             "drug_name": {"type": ["string", "null"],
                           "description": "Generic drug name such as atorvastatin; keeps only plans whose "
                                          "formulary examples list it and adds drug_tier_for_query. Or null."}}),
    _schema("compare_plans",
            "Side-by-side comparison of 2 to 4 plans by plan_id: premium, deductible, max out of pocket, star "
            "rating, network, drug coverage, formulary tier examples, dental and vision, highlights.",
            {"plan_ids": {"type": "array", "items": {"type": "string"},
                          "description": "Plan ids such as MA-CONTOSO-HMO-01 and MA-FABRIKAM-PPO-01."}}),
    _schema("get_hra_account",
            "HRA reimbursement account for a participant: annual allocation, balance, auto-reimbursement flag, "
            "debit card status (last 4 digits only), claims and a claims_summary.",
            {"participant_id": _PID}),
    _schema("get_claim_status",
            "Status of one HRA claim with a plain-language reason text when the claim was denied.",
            {"claim_id": {"type": "string", "description": "Claim id such as CLM-9003."}}),
    _schema("list_eligible_expenses",
            "Expense types a sponsor reimburses, for example premium, out_of_pocket, part_b_premium.",
            {"sponsor_id": {"type": "string", "description": "Sponsor id such as SP-NORTHWIND."}}),
    _schema("get_enrollment_window",
            "Which enrollment window applies to a participant today: IEP, AEP, OEP, SEP-possible or none, with "
            "start and end dates, the next scheduled window and a plain-language explanation.",
            {"participant_id": _PID,
             "today": {"type": ["string", "null"],
                       "description": "ISO date override such as 2026-10-20. Null uses the workshop date "
                                      "(BENEFITS_TODAY, default 2026-10-06)."}}),
]


def tool_schema(name: str) -> dict:
    """One schema by tool name (KeyError if unknown)."""
    for schema in TOOL_SCHEMAS:
        if schema["name"] == name:
            return copy.deepcopy(schema)
    raise KeyError(f"unknown tool {name!r}; known: {sorted(TOOL_REGISTRY)}")


def call_tool(name: str, arguments: dict | str | None = None) -> dict | list:
    """Dispatch by name with JSON or dict arguments; never raises for bad input."""
    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return _error(f"unknown tool {name}")
    args = json.loads(arguments or "{}") if isinstance(arguments, str) else dict(arguments or {})
    try:
        return fn(**args)
    except TypeError as exc:
        return _error(f"bad arguments for {name}: {exc}")


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def _selftest() -> int:
    failures: list[str] = []

    def check(condition: bool, label: str) -> None:
        print(f"[benefits_data] {'ok  ' if condition else 'FAIL'} {label}")
        if not condition:
            failures.append(label)

    print(f"[benefits_data] data dir: {DATA_DIR}")
    print(f"[benefits_data] participants={len(_load('participants'))} sponsors={len(_load('sponsors'))} "
          f"plans={len(_load('plans'))} hra_accounts={len(_load('hra_accounts'))} "
          f"knowledge_docs={len(list_knowledge_docs())}")
    for schema in TOOL_SCHEMAS:
        params = schema["parameters"]
        check(set(params["properties"]) == set(params["required"]) and params["additionalProperties"] is False,
              f"schema {schema['name']} is strict-compatible")
    check(set(TOOL_REGISTRY) == {s["name"] for s in TOOL_SCHEMAS}, "TOOL_REGISTRY and TOOL_SCHEMAS agree")

    print("\n[benefits_data] S1 AEP shopper (P-1001 Evelyn Marsh)")
    evelyn = get_participant("P-1001")
    check(evelyn.get("county") == "Salt Lake" and evelyn.get("current_plan_id") == "MA-CONTOSO-HMO-01", "profile")
    window_default = get_enrollment_window("P-1001")
    print(f"           window on {window_default['today']}: {window_default['window']} "
          f"(next: {window_default.get('next_window', {}).get('starts', 'n/a')})")
    check(get_enrollment_window("P-1001", today="2026-10-20")["window"] == "AEP", "AEP on 2026-10-20")
    check(get_enrollment_window("P-1001", today="2027-02-10")["window"] == "OEP", "MA OEP on 2027-02-10")
    ppo = search_plans("Salt Lake", plan_type="Medicare Advantage PPO", drug_name="atorvastatin")
    tier1 = [p["plan_id"] for p in ppo if p.get("drug_tier_for_query") == "Tier 1"]
    print(f"           MA PPO in Salt Lake with atorvastatin: {[(p['plan_id'], p['drug_tier_for_query']) for p in ppo]}")
    check(bool(tier1), "at least one MA PPO in Salt Lake County lists atorvastatin as Tier 1")
    comparison = compare_plans(["MA-CONTOSO-HMO-01", tier1[0] if tier1 else "MA-FABRIKAM-PPO-01"])
    check(len(comparison["plans"]) == 2 and not comparison["not_found"], "compare_plans returns both plans")
    check(len(search_plans("Salt Lake")) == 10, "search_plans caps at 10")
    check(search_plans("Nowhere") == [], "unknown county returns []")

    print("\n[benefits_data] S2 denied claim (P-1003 Harold Bing)")
    claim = get_claim_status("CLM-9003")
    print(f"           CLM-9003: {claim.get('status')} / {claim.get('reason')}")
    check(claim.get("status") == "denied" and claim.get("reason") == "missing_proof_of_payment", "CLM-9003 denied")
    check("proof" in (claim.get("reason_text") or "").lower(), "reason_text mentions proof")
    account = get_hra_account("P-1003")
    check(account.get("hra_account_id") == "HRA-5003" and account["claims_summary"]["denied"] == 1, "HRA-5003 summary")
    check("error" in get_claim_status("CLM-0000"), "unknown claim -> error dict")
    check("error" in get_participant("P-9999"), "unknown participant -> error dict")

    print("\n[benefits_data] S3 pre-Medicare, both LOBs (P-1005 Rosa Delgado)")
    rosa = get_participant("P-1005")
    check(rosa.get("medicare_eligible") is False and rosa.get("sponsor_id") == "SP-NORTHWIND", "profile")
    rosa_window = get_enrollment_window("P-1005", today="2026-10-20")
    print(f"           window on 2026-10-20: {rosa_window['window']}; IEP {rosa_window.get('medicare_iep')}")
    check(rosa_window["window"] != "AEP", "pre-Medicare participant is not in AEP")
    check(get_enrollment_window("P-1005", today="2026-11-15")["window"] == "OEP", "ACA open enrollment on 2026-11-15")
    check(get_enrollment_window("P-1005", today="2027-09-01")["window"] == "IEP", "IEP in Sept 2027 (turns 65 Nov 2027)")
    aca = search_plans("Davis", plan_type="ACA")
    check(bool(aca) and all(p["plan_type"].startswith("ACA") for p in aca), "ACA plans in Davis County")
    check(list_eligible_expenses("SP-NORTHWIND") == ["premium", "out_of_pocket", "part_b_premium"], "eligible expenses")
    check(get_hra_account("P-1005").get("balance") == 1875.25, "HRA-5005 balance")

    print("\n[benefits_data] knowledge")
    docs = list_knowledge_docs()
    print("           " + ", ".join(f"{d['doc_id']}({d['context']})" for d in docs))
    check({d["doc_id"] for d in docs} >= REQUIRED_KNOWLEDGE_DOC_IDS, "all required knowledge docs present")
    check(all(d.get("title") and d.get("context") and d.get("last_reviewed") for d in docs), "frontmatter complete")
    check({d["context"] for d in docs} == {"marketplace", "accounts", "universal"}, "three bounded contexts")
    check(read_knowledge_doc("KB-ACC-001").startswith("---"), "read_knowledge_doc returns raw Markdown")
    check(redact_pii("SSN 123-45-6789") == "SSN [REDACTED-SSN]", "redact_pii wrapper")

    print(f"\n[benefits_data] {'ALL CHECKS PASSED' if not failures else f'{len(failures)} FAILURE(S): {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(_selftest())
