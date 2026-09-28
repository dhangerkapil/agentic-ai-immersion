"""Shared guardrails for every Benefits Marketplace agent, hosted or platform-managed.

* COMPLIANCE_INSTRUCTIONS   appended verbatim to every agent's instructions
* DISCLAIMER                one-line footer agents may add to plan comparisons
* redact_pii(text)          regex redaction of SSN, MBI, phone, email and 16-digit card numbers
* contains_recommendation   cheap heuristic that flags plan-recommendation language

Pure Python, no Azure imports. The regexes are deliberately conservative: workshop identifiers
(P-1001, CLM-9003, HRA-5001, KB-ACC-001, plan ids, ZIP codes, dollar amounts, dates) must survive
unchanged, because `guardrails.redact_pii(text) == text` is used as a "no PII" check.
"""

from __future__ import annotations

import re

COMPLIANCE_INSTRUCTIONS = """COMPLIANCE RULES (Benefits Marketplace)
1. You are not a licensed benefit advisor. Never recommend a specific plan, never tell a participant which plan
   to choose or enroll in, never rank plans as "best". Provide neutral, factual comparisons only.
2. When a participant asks for a recommendation, asks to enroll, or shares a situation that needs judgment,
   say a licensed benefit advisor will help and offer the handoff.
3. Data minimization: never ask for, repeat, or store a full Social Security Number, Medicare Beneficiary
   Identifier, or card number. Confirm identity only with participant_id and ZIP code in this workshop.
4. Use only the tools and knowledge provided. If the knowledge base does not cover a question, say so.
5. Cite the knowledge document id (for example [KB-ACC-001]) after any statement that comes from it.
6. Plain language, short sentences. No medical advice. No guarantees about coverage or cost.
"""

DISCLAIMER = (
    "This is educational information from Benefits Marketplace, not a recommendation. Plan details, premiums and "
    "networks can change; a licensed benefit advisor can confirm them and help you enroll."
)

# ---------------------------------------------------------------------------
# PII redaction
# ---------------------------------------------------------------------------
# Order matters: the longest, most specific patterns run first so a 16-digit card number is never
# partly consumed by the phone pattern, and an SSN is never mistaken for a phone number.
_MBI_ALPHA = "AC-HJKMNP-RT-Y"       # MBI letters exclude S, L, O, I, B, Z
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("CARD", re.compile(r"(?<![\w-])\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}(?![\w-])")),
    ("SSN", re.compile(r"(?<![\w-])\d{3}[- ]\d{2}[- ]\d{4}(?![\w-])")),
    ("MBI", re.compile(
        rf"(?<![A-Za-z0-9])[1-9][{_MBI_ALPHA}][{_MBI_ALPHA}0-9]\d-?[{_MBI_ALPHA}][{_MBI_ALPHA}0-9]\d-?"
        rf"[{_MBI_ALPHA}]{{2}}\d{{2}}(?![A-Za-z0-9])", re.IGNORECASE)),
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("PHONE", re.compile(
        r"(?<![\w-])(?:\+?1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]?\d{3}[ .-]?\d{4}(?![\w-])")),
]


def redact_pii(text: str) -> str:
    """Replace SSNs, MBIs, phone numbers, emails and 16-digit card numbers with [REDACTED-<type>].

    Non-string input is returned unchanged so callers can pass tool results through without type checks.
    Last-4 card digits ("card ending in 4417") are allowed by design and are not touched.
    """
    if not isinstance(text, str) or not text:
        return text
    for label, pattern in _PII_PATTERNS:
        text = pattern.sub(f"[REDACTED-{label}]", text)
    return text


def find_pii(text: str) -> dict[str, int]:
    """Count PII matches by type without changing the text. Useful in audit logs and tests."""
    counts: dict[str, int] = {}
    if not isinstance(text, str) or not text:
        return counts
    remaining = text
    for label, pattern in _PII_PATTERNS:
        hits = pattern.findall(remaining)
        if hits:
            counts[label] = len(hits)
            remaining = pattern.sub(" ", remaining)
    return counts


# ---------------------------------------------------------------------------
# Recommendation heuristic
# ---------------------------------------------------------------------------
_RECOMMENDATION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\byou should (?:enroll|enrol|sign up|switch|choose|pick|select|go with|get|take|buy)\b",
        r"\byou (?:need|ought) to (?:enroll|switch|choose|pick|select)\b",
        r"\bi(?:'d| would)? recommend\b",
        r"\bwe(?:'d| would)? recommend\b",
        r"\bmy recommendation (?:is|would be)\b",
        r"\bi(?:'d| would)? suggest (?:you )?(?:enroll|switch|choose|pick|select|go with|get)\b",
        r"\bthe best (?:plan|option|choice|fit) for you\b",
        r"\bbest plan for you\b",
        r"\b(?:is|would be) (?:the )?best (?:plan|option|choice) for you\b",
        r"\bpick plan\b",
        r"\bpick the [A-Za-z0-9 -]{0,40}\b(?:plan|hmo|ppo|medigap)\b",
        r"\byou(?:'d| would) be better off (?:with|on|in)\b",
        r"\bgo with (?:the )?[A-Za-z0-9 -]{0,40}\b(?:plan|hmo|ppo|medigap|part d)\b",
        r"\bI(?:'d| would) (?:choose|pick|go with|enroll in)\b",
    )
]
# Handoff language is not a plan recommendation: "I recommend you speak with a licensed benefit advisor".
# Neither is the general Medicare rule "you should enroll in Part B during your IEP".
_HANDOFF_EXCEPTION = re.compile(
    r"\b(?:licensed|advisor|adviser|speak|speaking|talk|talking|contact|call|schedule|review|reviewing|"
    r"part a|part b|original medicare)\b", re.IGNORECASE)


def contains_recommendation(text: str) -> bool:
    """True when the text reads like a plan recommendation.

    Heuristic only: it looks for phrases such as "you should enroll in", "I recommend",
    "the best plan for you is" and "pick plan". A match that is immediately followed by
    handoff wording (advisor, licensed, speak with) is ignored. Lab 4 measures the real
    rate with a model-graded evaluator; this function is the cheap local check.
    """
    if not isinstance(text, str) or not text:
        return False
    for pattern in _RECOMMENDATION_PATTERNS:
        for match in pattern.finditer(text):
            tail = text[match.end(): match.end() + 80]
            if _HANDOFF_EXCEPTION.search(tail):
                continue
            return True
    return False


def compliance_flags(text: str) -> list[str]:
    """Local checks shared by the labs: recommendation language and unredacted PII."""
    flags: list[str] = []
    if contains_recommendation(text):
        flags.append("recommendation_language")
    if redact_pii(text) != text:
        flags.append("pii_present")
    return flags


if __name__ == "__main__":
    sample = ("Call me at 801-555-0100 or (801) 555-0199, email evelyn.marsh@example.com, SSN 123-45-6789, "
              "MBI 1EG4-TE5-MK73, card 4111 1111 1111 1111. Participant P-1001, claim CLM-9003, ZIP 84095, "
              "balance $1,240.50, plan MA-CONTOSO-HMO-01, card ending in 4417, submitted 2026-08-03.")
    print(redact_pii(sample))
    print(find_pii(sample))
    for line in ("You should enroll in the Fabrikam PPO.",
                 "I recommend the Woodgrove plan.",
                 "The best plan for you is Contoso Advantage Choice.",
                 "I recommend you speak with a licensed benefit advisor about that choice.",
                 "Here is a neutral comparison of the two plans you asked about."):
        print(f"{contains_recommendation(line)!s:5}  {line}")
