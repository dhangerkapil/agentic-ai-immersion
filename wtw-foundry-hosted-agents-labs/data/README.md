# data/: the Via Benefits synthetic systems of record

Everything in this folder is synthetic. The people, sponsors, carriers, plans, plan ids, claims, balances,
phone numbers, email addresses and call transcripts were invented for this workshop. Nothing here comes from
a real participant, a real carrier or a real Via Benefits system. Carrier names are the Microsoft fictional
companies: Contoso Health, Fabrikam Medicare, Woodgrove Assurance, Tailspin Health, Northwind Rx.

Every lab reads this folder through `common/via_data.py` (the 8 shared tools); hosted agents get a vendored copy
(`hosted/prepare.py`) so the container can read it. Field names are a contract: the lab
code depends on them, so add fields if you like but do not rename or remove any.

## Files

| File | Records | What it is | Read by |
|---|---|---|---|
| `participants.json` | 6 | Participant profiles P-1001 to P-1006: 4 Medicare-eligible, 2 pre-Medicare. Fields: participant_id, first_name, last_name, dob, age, zip, county, state, sponsor_id, medicare_eligible, medicare_parts, part_b_effective, current_plan_id, hra_account_id, lob_relationship (both, accounts_only, marketplace_only), preferences {doctors, prescriptions, priorities}, contact_preference, language | get_participant, get_enrollment_window |
| `sponsors.json` | 2 | Plan sponsors SP-NORTHWIND (Northwind Traders Retiree Health Program) and SP-ADATUM (Adatum Corporation Retiree Medical): HRA amounts, eligibility rule, eligible_expense_types, catastrophic_fund, notes | get_sponsor, list_eligible_expenses |
| `plans.json` | 20 | Plan year 2027 individual plans sold in Utah counties Salt Lake, Utah, Davis and Weber: 6 Medicare Advantage (3 HMO, 3 PPO), 3 Medigap (2 Plan G, 1 Plan N), 3 Part D, 8 ACA (2 Bronze, 3 Silver, 3 Gold). Fields: plan_id, carrier, plan_name, plan_type, premium_monthly, deductible_annual, max_out_of_pocket, star_rating (null for Medigap), network_type, service_area_counties, state, drug_coverage, formulary_tier_examples, dental_vision, plan_year, highlights | search_plans, compare_plans |
| `hra_accounts.json` | 6 | One HRA account per participant for plan year 2026: annual_allocation, balance, account_status, auto_reimbursement_enabled, debit_card {status, last4}, claims [{claim_id, type, amount, submitted, status, paid_date, reason}] | get_hra_account, get_claim_status |
| `knowledge/*.md` | 9 docs | The knowledge base: Via Benefits functional documentation as Markdown with frontmatter (title, context, doc_id, last_reviewed). Contexts: marketplace (KB-MKT-001..004), accounts (KB-ACC-001..003), universal (KB-UNI-001, KB-UNI-002). KB-UNI-001 carries `audience: advisor` and is the advisor-only doc used to show a security filter | list_knowledge_docs, read_knowledge_doc, every knowledge lab |
| `eval/golden_questions.jsonl` | 18 | Evaluation set, one JSON object per line: id, scenario, query, participant_id, context, expected_behavior, must_include, must_not | Lab 4 (evaluation of the hosted agent) |
| `transcripts/call-00N.txt` | 3 | Synthetic Genesys-style call transcripts, `[hh:mm:ss] Advisor:` / `[hh:mm:ss] Participant:` lines, 27 turns each. call-001 is S1, call-002 is S2, call-003 is S3 | Anyone demonstrating PII redaction (`guardrails.redact_pii`) |

## The three scenarios and where their facts live

| Scenario | Participant | Facts the data guarantees |
|---|---|---|
| S1 AEP shopper | P-1001 Evelyn Marsh, 68, Salt Lake County | On MA-CONTOSO-HMO-01 (atorvastatin Tier 2). Two MA PPOs in Salt Lake County list atorvastatin as Tier 1: MA-FABRIKAM-PPO-01 ($29, MOOP $5,900) and MA-WOODGROVE-PPO-01 ($48, MOOP $6,700). HRA-5001 balance 1,240.50, auto-reimbursement on. Enrollment window: AEP from 2026-10-15 |
| S2 Denied claim | P-1003 Harold Bing, 72, Utah County | HRA-5003, balance 2,210.00, auto-reimbursement off. CLM-9003 (out_of_pocket, 240.00, submitted 2026-09-14) denied with reason `missing_proof_of_payment`. CLM-9004 and CLM-9005 paid |
| S3 Pre-Medicare, both LOBs | P-1005 Rosa Delgado, 63, Davis County | Not Medicare eligible, dob 1962-11-20 so the Medicare IEP runs 2027-08-01 to 2028-02-29. On ACA-TAILSPIN-SILVER-01 ($548). HRA-5005 balance 1,875.25, sponsor SP-NORTHWIND funds pre-65 retirees. Davis County has 2 Bronze, 2 Silver, 2 Gold ACA plans |

Other useful records: P-1004 Margaret Okafor has a blocked debit card and a claim denied as `expense_not_eligible`
(debit card and eligibility demos); P-1002 Walter Finch is on Medigap with premium auto-reimbursement under
SP-ADATUM; P-1006 Daniel Whitaker is marketplace-only with an unfunded HRA (the "no account" path).

## Dates

The data describes plan year 2026 accounts and plan year 2027 marketplace plans, as they would look during
the fall 2026 enrollment season. Enrollment-window answers depend on "today". `common/via_data.py` reads
`VIA_TODAY` (ISO date) and defaults to `2026-10-06`, which is nine days before AEP opens. Set
`VIA_TODAY=2026-10-20` to run S1 inside AEP, `2026-11-15` to put S3 inside ACA open enrollment, or
`2027-09-01` to see Rosa's IEP. Tests pass `today=` explicitly for the same reason.

## Golden questions

`must_include` and `must_not` are substrings meant for a case-insensitive check that ignores thousands
separators (a model may write `$2,210.00` or `2210`). They are guidance for graders, not an exact-match test;
Lab 4 pairs them with model-graded evaluators (task adherence, groundedness, relevance, the
`no_plan_recommendation` label). Every line carries `"recommend a specific plan"` in `must_not` because that
is the rule the whole workshop is built around. Coverage: plan comparison (GQ-01, 02, 10), enrollment windows
(GQ-03, 09), denied claim (GQ-05, 06, 07), debit card (GQ-11, 12), premium auto-reimbursement (GQ-13),
PHI probes (GQ-14, 15), jailbreak (GQ-16), off-topic (GQ-17, 18), both-LOB (GQ-08), recommendation
pressure (GQ-04).

## PII in the transcripts

call-001 contains one phone number and call-003 one email address, so redaction has something to find and
the `phi_redacted_in_transcript` flag appears on S1 and S3 packets. call-002 is clean on purpose: a good
YOUR TURN is to add an MBI and a phone number to a copy of it and watch the redaction counts change. Workshop
identifiers (P-1001, CLM-9003, ZIP codes, last-4 card digits) are not PII for the redactor and survive.

## Editing the data

Keep JSON valid (`python -m json.tool data/plans.json`) and re-run `python common/via_data.py` after any
edit; its self-test asserts the scenario facts above. If you add a knowledge doc, give it the four
frontmatter fields and a unique doc_id; `list_knowledge_docs()` picks it up automatically.
