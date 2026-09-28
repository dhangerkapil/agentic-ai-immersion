---
title: Privacy and PHI Handling
context: universal
doc_id: KB-UNI-002
last_reviewed: 2026-09-01
---

# Privacy and PHI Handling

Benefits Marketplace handles personally identifiable information (PII) and protected health information (PHI) in every participant conversation. These rules apply to every advisor and every assistant agent: collect the minimum, verify identity the same way every time, and never let a sensitive identifier travel further than it has to.

## Data minimization

Ask only for what the current task needs. A balance question needs the participant record, not a diagnosis. A plan comparison needs county, plan type and the drug names the participant chooses to share, not a medical history. Nothing is collected "in case it is useful later".

Identifiers that are never requested, repeated back, or written into notes, summaries, packets or logs:

- The full Social Security Number.
- The Medicare Beneficiary Identifier (MBI), the 11-character number on the red, white and blue card.
- The full HRA debit card number, expiration date or security code. The last four digits identify a card.
- Bank account and routing numbers.

When a carrier form or direct deposit setup needs one of these, the participant enters it in the secure portal or the advisor uses the designated secure workflow. Assistants say so and move on.

## Identity verification in this workshop

Production verification uses knowledge-based checks and telephony signals. In the workshop data set, identity is confirmed with two facts only: the participant_id (for example P-1001) and the ZIP code on file. Both must match before any account, claim or plan detail is shared. If either does not match, share nothing, say the details do not match the record, and offer an advisor. Never hint, such as "the ZIP on file starts with 84".

A caller who is not the participant (spouse, adult child, caregiver) needs a documented authorization on the record. Without it, the assistant explains general rules and processes and takes a message.

## When a participant volunteers PHI

Participants often share more than is needed: a diagnosis, a hospital stay, a full Medicare number read from the card. When that happens:

1. Do not repeat the sensitive value back. Acknowledge briefly and continue.
2. Use only what the task needs. A drug name helps a formulary lookup; the reason it was prescribed does not.
3. Sensitive identifiers (SSN, MBI, full card numbers, phone numbers, email addresses) are redacted before any transcript, summary or packet is stored. Markers such as [REDACTED-MBI] are acceptable in stored text; the original value is not.
4. Health conditions appear in the advisor packet only when they bear on the advisor's question, in the participant's own general terms.
5. If a participant asks "what is my full Medicare number", the assistant cannot read or display it; the number is on the Medicare card and in the participant's Medicare.gov account.

## Storage and retention

Transcripts, call summaries, tool results and handoff packets are records. They live in approved systems inside the governed data boundary, with access limited to the advisors and supervisors working the case. Nothing is pasted into personal notes, email or unmanaged chat tools. Retention follows the sponsor contract and regulatory schedule; deletion requests go to the privacy office.

## Reporting a possible breach

If a sensitive value was shared with the wrong person, stored unredacted, or sent to an unmanaged system, report it the same day through the privacy incident process. An early report is always better than silence. Assistants that detect unredacted identifiers in stored output raise a compliance flag rather than cleaning up on their own.
