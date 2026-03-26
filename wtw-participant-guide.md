# AI Capability Guide - Participant Reference
### Willis Towers Watson | Agentic AI Immersion | April 2025

---

## Before the Workshop

Great meeting with you all this week - as promised, here is the pre-read for the April session.

What we need from you this coming week is to pick the 5 use cases you want to work through hands-on and 5 wishlist use cases that we would cover if time allows. Browse the 7 technology areas below - each one has a short description and a list of specific use cases underneath it - and let us know which you want to dig into.

Your picks shape the whole day. We use them to make sure the session reflects what actually matters to your team rather than a generic agenda.

**Please send your 5 choices to me <ptaylor@aimconsulting.com> by EOD Wednesday April 1.** Instructions for responding are at the end of this document.

The full workshop materials are at: [github.com/aim-technology-consulting/agentic-ai-immersion](https://github.com/aim-technology-consulting/agentic-ai-immersion)

---

## How to Choose

No wrong answers here. Three questions that usually help:

**1. Where's the friction?**
Think about a task or process that takes more time or expertise than it should. Which use case, if it worked reliably, would change that?

**2. What would your users notice?**
Some of these change how your team works internally. Others change what a client experiences. Both are fair game - just worth being deliberate about which you're going after.

**3. What are you just curious about?**
This is a hands-on workshop, not a procurement review. If something sounds interesting even if you can't immediately place it in a workflow, pick it anyway. That's exactly what the day is for.

A few practical notes:
- You probably want to include at least one use case from **Conversational AI Agents** - it's the foundation everything else builds on.
- Use cases marked *Preview* are real and working, but the underlying APIs are still evolving. They're where the platform is heading, not necessarily where you'd ship today.
- You can pick multiple use cases from the same area or spread across five different ones - totally up to you.
- If you're torn between more than 5, ask yourself: which 5 would I most regret not having tried by the end of the day?

---

## The 7 Technology Areas

---

### 1. Conversational AI Agents
*The foundation everything else is built on*

An AI agent is a system that holds a conversation, remembers what was said earlier, and takes actions - not just answers questions. You give it a role, a set of rules, and access to tools or data, and it handles the rest. Every other area in this workshop is an extension of this one.

**Use cases:**
- [Financial Services Advisor](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-financial-services-advisor)
- [Financial Advisor Basics](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-financial-advisor-basics)
- [Investment Portfolio Management](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-investment-portfolio-management)
- [Persistent Financial Advisor](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-persistent-financial-advisor)
- [Banking Operations Center](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-banking-operations-center)
- [Loan Application Discussion](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-loan-application-discussion)

**Workshop track:** [Track 1 - Azure AI Agents SDK](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2 - Microsoft Agent Framework](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework)

---

### 2. Knowledge & Information Access
*Getting the right information to the agent at the right moment*

An agent is only as useful as the information it can reach. This area covers the four ways agents access knowledge: querying large structured datasets by meaning rather than keywords, reading and reasoning over uploaded documents, pulling live data from the web, and running calculations on demand. In practice these are often combined - a single agent might search a product catalog, pull a policy document, check today's rate, and compute a recommendation in one turn.

**Use cases:**
- [Banking Products Catalog](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-banking-products-catalog)
- [Loan Underwriting & Risk Assessment](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-loan-underwriting-risk-assessment)
- [Banking Document Search](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-banking-document-search)
- [Loan Policy Document Search](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-loan-policy-document-search)
- [Financial Market Research](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-financial-market-research)
- [Financial Market Research Portal](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-financial-market-research-portal)
- [Loan & Portfolio Calculator](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-loan-portfolio-calculator)
- [Financial Analytics Dashboard](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-financial-analytics-dashboard)

**Workshop track:** [Track 1 - Azure AI Agents SDK](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2 - Microsoft Agent Framework](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework)

---

### 3. Live System Integration
*Agents that reach into your own platforms during a conversation*

Rather than working only with pre-loaded data, an agent can discover and call external tools and APIs at the moment it needs them - your own systems or third-party services. The agent decides which tool to call, calls it, and incorporates the result, all within a single conversation turn. This is what makes an agent genuinely useful in an existing technology landscape rather than a standalone demo. *(Preview)*

**Use cases:**
- [Platform Operations Assistant](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-platform-operations-assistant)
- [Documentation Research Assistant](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-documentation-research-assistant)

**Workshop track:** [Track 1 - Azure AI Agents SDK](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2 - Microsoft Agent Framework](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework)

---

### 4. Memory & Session Continuity
*Agents that remember - across turns, across sessions, across instances*

This area covers two related problems. The first is cross-session memory: after a conversation ends, the agent stores what matters and recalls it the next time, so the experience becomes more personalised over time without the user having to repeat themselves. The second is distributed state: when an agent is deployed across many concurrent users or multiple servers, conversation history needs to survive restarts and route correctly to any instance. Both are prerequisites for agents that feel like a real product rather than a prototype. *(Preview)*

**Use cases:**
- [Personalized Banking Assistant](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-personalized-banking-assistant)
- [Distributed Customer Session Management](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-distributed-customer-session-management)

**Workshop track:** [Track 1 - Azure AI Agents SDK](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2 - Microsoft Agent Framework](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework)

---

### 5. Multi-Agent Workflows
*Coordinating teams of specialist agents on complex tasks*

Some problems are too large or too multifaceted for a single agent. This area covers three patterns for multi-agent work: sequential pipelines where each agent hands its output to the next; parallel research teams where a coordinator dispatches specialist agents simultaneously and synthesises their findings; and deep multi-source queries where an agent autonomously plans and executes sub-queries across multiple knowledge bases before assembling a single answer. Human review and approval steps can be inserted at any point. *(Preview)*

**Use cases:**
- [Insurance Claims Processing](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-insurance-claims-processing)
- [Multi-Source Fraud Investigation](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-multi-source-fraud-investigation)
- [Loan Underwriting & Risk Assessment](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-loan-underwriting-risk-assessment)
- [Investment Research with Compliance](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-investment-research-with-compliance)
- [Investment Research Report Generation](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-investment-research-report-generation)

**Workshop track:** [Track 1 - Azure AI Agents SDK](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2 - Microsoft Agent Framework](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework)

---

### 6. Enterprise Controls & Compliance
*AI that fits inside your governance framework*

Production AI in a regulated environment needs more than a good model - it needs controls. This area covers the framework layer that adds what professional services environments require: a middleware pipeline that intercepts every request and response without touching agent logic, complete audit logging of every interaction, human approval gates that pause a workflow pending sign-off, and programmatic enforcement of business rules. The result is an agent deployment that satisfies compliance, legal, and operations - not just engineering. *(Preview)*

**Use cases:**
- [Transaction Compliance Monitoring](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-transaction-compliance-monitoring)
- [Trade Execution Logging](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-trade-execution-logging)
- [Credit Limit Assessment](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-credit-limit-assessment)
- [Portfolio Rebalancing](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-portfolio-rebalancing)
- [Customer Service Message Filtering](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-customer-service-message-filtering)
- [Market Data Service Recovery](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-market-data-service-recovery)
- [Transaction Compliance Screening](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-transaction-compliance-screening)
- [Market Data Enrichment](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-market-data-enrichment)
- [Transaction Audit Trail](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-transaction-audit-trail)
- [Compliance-Ready Conversation Audit](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-compliance-ready-conversation-audit)
- [Insurance Claim Processing Continuity](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-insurance-claim-processing-continuity)
- [Credit Limit Review with Approval](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-credit-limit-review-with-approval)
- [Large Transaction Authorization](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-large-transaction-authorization)
- [Loan Advisory with Compliance](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-loan-advisory-with-compliance)
- [Customer Communication Quality](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-customer-communication-quality)

**Workshop track:** [Track 2 - Microsoft Agent Framework](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework)

---

### 7. Quality, Observability & Security
*Knowing your agents are working correctly - and proving it*

Deploying an agent is not the finish line. This area covers the three practices that make a deployment trustworthy over time: observability (every request, response, and tool call logged with timing and cost signals, flowing into dashboards you can alert on); systematic quality evaluation (running your agent against a defined test set and scoring responses across accuracy, relevance, and safety - tracked over time so regressions surface early); and adversarial security testing (systematically probing your agent with known attack techniques to find vulnerabilities before users do).

**Use cases:**
- [Wealth Management Advisory Monitoring](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-wealth-management-advisory-monitoring)
- [Trade Execution Monitoring](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-trade-execution-monitoring)
- [Customer Service Monitoring](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-customer-service-monitoring)
- [Loan Processing Pipeline Monitoring](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-loan-processing-pipeline-monitoring)
- [Loan Advisory Quality Testing](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-loan-advisory-quality-testing)
- [Banking Assistant Evaluation](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-banking-assistant-evaluation)
- [Banking Operations Tool Validation](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-banking-operations-tool-validation)
- [Banking AI Security Assessment](https://github.com/aim-technology-consulting/agentic-ai-immersion#uc-banking-ai-security-assessment)

**Workshop track:** [Track 3 - Observability & Evaluations](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-3--observability--evaluations-observability-and-evaluations)

---

## How to Respond

Just reply to [facilitator contact] by [date]. No form, no special format - a short email is fine.

**Subject:** WTW AI Workshop - [Your Name] selections

In the body:

1. **Your 5 use case names** - e.g. "Multi-Source Fraud Investigation, Personalized Banking Assistant, Transaction Compliance Monitoring, Insurance Claims Processing, Loan Advisory Quality Testing"
2. **One sentence on each** explaining why it caught your eye - helps us tailor the day to your context
3. **Anything you're unsure about or want us to address** - if there's a scenario specific to your team, flag it here

---

## Quick Reference

| # | Technology Area | Maturity | Track |
|---|----------------|----------|-------|
| 1 | Conversational AI Agents | Production ready | [Track 1](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework) |
| 2 | Knowledge & Information Access | Production ready | [Track 1](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework) |
| 3 | Live System Integration | Preview | [Track 1](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework) |
| 4 | Memory & Session Continuity | Preview | [Track 1](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework) |
| 5 | Multi-Agent Workflows | Preview | [Track 1](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-1--azure-ai-agents-sdk-azure-ai-agents) · [Track 2](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework) |
| 6 | Enterprise Controls & Compliance | Preview | [Track 2](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-2--microsoft-agent-framework-agent-framework) |
| 7 | Quality, Observability & Security | Production ready | [Track 3](https://github.com/aim-technology-consulting/agentic-ai-immersion#track-3--observability--evaluations-observability-and-evaluations) |
