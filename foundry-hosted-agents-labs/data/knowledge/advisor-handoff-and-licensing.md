---
title: Advisor Handoff and Licensing Boundaries
context: universal
doc_id: KB-UNI-001
last_reviewed: 2026-09-01
audience: advisor
---

# Advisor Handoff and Licensing Boundaries

Audience: licensed benefit advisors, supervisors and the teams that configure assistant agents. Not shown to participants. It defines what an unlicensed assistant, human or software, may say about individual plans, when a conversation moves to a licensed benefit advisor, and what the handoff packet contains.

## Why the boundary exists

Recommending, selling or enrolling a person in a Medicare Advantage, Medigap, Part D or ACA individual plan is a licensed activity under state insurance law and CMS Medicare marketing rules. Only a licensed benefit advisor appointed with the carrier may do it. An assistant that steers a participant toward one plan creates compliance exposure for Benefits Marketplace and the sponsor, even when well meant. The operating model: assistants inform, advisors decide with the participant.

## What an assistant may say

- Explain plan types, enrollment periods, HRA rules and account status.
- Present neutral, factual comparisons of plans the participant asked about or that match filters the participant gave (county, plan type, premium ceiling, a named drug), side by side, without ranking.
- Report what a formulary or network lookup returns, noting that the carrier confirms it.
- Explain a claim denial reason, the accepted documents, and how resubmission works.
- Say that a licensed benefit advisor can review options and complete an enrollment, and cite the knowledge document used, for example [KB-MKT-004].

## What an assistant must not say or do

- Name a "best" plan, say a plan is "right for you", rank plans by suitability, or use phrases such as "you should enroll in", "I recommend", "pick plan".
- Start, submit or promise an enrollment, disenrollment or plan change.
- Predict total annual cost or guarantee that a doctor or drug is covered.
- Give medical advice or interpret a diagnosis.
- Discuss carrier commissions, offer incentives to enroll, or contact a participant who did not initiate the conversation.

## When to hand off

Hand off when any of these occur:

1. The participant asks for a recommendation in any wording ("which one should I pick", "what would you do").
2. The participant asks to enroll, switch, cancel or change a plan.
3. The situation needs judgment: a Special Enrollment Period claim, a late enrollment penalty, dual eligibility, employer coverage ending, a move between counties or states, or a spouse with different needs.
4. A catastrophic fund request or any sponsor exception.
5. A complaint, an appeal, or a medical emergency.
6. The participant is distressed, identity is unclear, or a third party is speaking for them without a documented authorization.

The assistant says a licensed benefit advisor will help, confirms the callback preference, and creates the packet. It does not hold the participant to "finish" a comparison first.

## The handoff packet

Every handoff produces one structured packet the advisor reviews before contact:

- participant_id, first name, county, state, sponsor_id, contact preference (never a full SSN, MBI or card number).
- line_of_business: marketplace, accounts or both.
- reason_for_handoff: one of recommendation_requested, enrollment_requested, judgment_needed, sponsor_exception, complaint_or_appeal, other.
- summary: three to five sentences on what was asked and what was explained.
- options_discussed: plan ids or account items presented, with no ranking.
- open_questions: what the advisor needs to resolve.
- compliance_flags: recommendation_language_detected, phi_redacted_in_transcript, identity_not_verified, or none.
- knowledge_refs: document ids cited.
- created_at and the creating agent name.

## Advisor review

The advisor approves, revises or declines the packet. Approval routes the case to the advisor's queue with the callback preference. Revision returns it to the assistant with feedback. Declines are logged with a reason. No enrollment starts without a licensed advisor's approval.
