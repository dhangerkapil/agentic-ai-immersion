---
name: hra-reimbursement-rules
description: How Via Benefits reviews HRA claims: eligible expense types, the two kinds of documentation every claim needs, the accepted and not-accepted proof-of-payment documents, the denial reason codes with their fixes, and how a denied claim is resubmitted. Use when a participant asks why a claim was denied, what to send, whether an expense is eligible, or when a payment will arrive.
version: 1.0.0
context: accounts
source_doc: KB-ACC-001
last_reviewed: 2026-09-01
---

# HRA reimbursement rules

Derived from the Via Benefits knowledge document KB-ACC-001 (HRA Reimbursement Rules). Cite `[KB-ACC-001]`
after any statement taken from this skill. All amounts, rules and codes below are for the workshop's synthetic
sponsors; production skills are regenerated from the governed knowledge base.

## When to use this skill

- The participant asks why a claim was denied, or what "missing proof of payment" means.
- The participant asks what documents to send with a claim or a resubmission.
- The participant asks whether an expense type is eligible under their sponsor.
- The participant asks when a claim will be paid.

Do not use it to promise that a resubmission will be paid, and never upload or submit anything on the
participant's behalf: agents explain, list the accepted documents and flag the claim for follow-up.

## Eligible expense types (sponsor chooses which apply)

- `premium`: monthly premiums for Medicare Advantage, Medigap, Part D, ACA individual plans, and dental or vision plans unless the sponsor lists those separately.
- `part_b_premium`: the Medicare Part B premium deducted from Social Security or paid directly to Medicare.
- `out_of_pocket`: deductibles, copays and coinsurance for medical, dental, vision and prescription expenses.
- `dental_vision_premium`: dental and vision premiums when the sponsor lists them separately.

Never eligible: gym memberships, cosmetic procedures, vitamins without a prescription, expenses for people who are not covered dependents, late fees. Check the sponsor's list with `list_eligible_expenses` before answering.

## Every claim needs two documents

1. **Proof of expense**, one of: an itemized statement or explanation of benefits (provider, date of service, service, amount owed); or a premium invoice or billing statement from the carrier (coverage month, premium amount).
2. **Proof of payment**, one of the accepted documents below.

Claims for a plan year are accepted until March 31 of the following year (the run-out period).

## Accepted proof of payment

- A bank or credit card statement showing the payee, the date and the amount. Other lines may be blacked out.
- A cancelled check image, front and back.
- A receipt marked paid that shows the payment method and date.
- A carrier statement showing payment received or a zero balance for the month.
- For the Part B premium: the annual Social Security benefit statement, Form SSA-1099, or a Medicare premium bill marked paid.

## Not accepted as proof of payment

Quotes or estimates; statements showing only a balance due; balance-forward statements without a payment line; handwritten notes; screenshots that do not show the payee, date and amount together.

## Denial reason codes

| Code | Meaning | Fix |
|---|---|---|
| `missing_proof_of_payment` | Proof of expense received, nothing shows the bill was paid | Resubmit with one accepted proof-of-payment document; reference the original claim id |
| `expense_not_eligible` | Category not covered by the sponsor | None for that expense |
| `duplicate_claim` | Same expense, date and amount already paid | None |
| `outside_plan_year` | Service date or coverage month outside the plan year, or run-out passed | None unless the date on the document was misread; ask the participant to check it |
| `missing_service_date` | Document shows no date of service or coverage month | Resubmit with a document that shows the date |
| `provider_not_identified` | Document shows no provider or carrier | Resubmit with a document that names the provider or carrier |
| `illegible_documentation` | Upload could not be read | Re-scan and resubmit |

## Processing and payment

Most claims are reviewed within five business days. Approved amounts are paid by direct deposit two to three business days after approval, or by check within ten business days. `pending` means the claim is in the review queue.

## Resubmitting a denied claim

A denied claim is not closed. The participant submits the missing document as a new claim that references the original claim id, or replies to the denial notice in the portal. Agents may explain the reason, list the accepted documents, and flag the claim for resubmission follow-up. Agents cannot submit a claim or upload documents for the participant.

## How to answer (pattern)

1. Look the claim up with `get_claim_status`; read `reason` and `reason_text`.
2. Say the reason in one plain sentence, cite `[KB-ACC-001]`.
3. If the code has a fix, list the accepted documents that apply and the resubmission step. If it has no fix, say so without apology language that implies the decision might change.
4. Offer to flag the claim for resubmission follow-up. Do not promise payment.
5. Repeat only the claim id, amount and date. Never read back account or card numbers.
