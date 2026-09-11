# -*- coding: utf-8 -*-
"""Generates the Agentic AI Immersion Workshop - Pre-Requisites Datasheet PDF."""
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    ListFlowable, ListItem, HRFlowable, NextPageTemplate, PageBreak
)
from reportlab.lib.enums import TA_LEFT

MS_BLUE = colors.HexColor("#0078D4")
DARK = colors.HexColor("#1B1B1B")
GRAY = colors.HexColor("#5C5C5C")
LIGHT_BG = colors.HexColor("#F3F2F1")
GREEN = colors.HexColor("#107C10")
AMBER = colors.HexColor("#CA5010")

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "Workshop-Agentic-AI-Immersion-Prerequisites-Datasheet.pdf")
OUT_PATH = os.path.abspath(OUT_PATH)

styles = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, textColor=DARK, leading=26, spaceAfter=4),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=12, textColor=MS_BLUE, leading=16, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13.5, textColor=MS_BLUE, spaceBefore=14, spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10.5, textColor=DARK, spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.3, textColor=DARK, leading=13),
    "bodySmall": ParagraphStyle("bodySmall", fontName="Helvetica", fontSize=8.5, textColor=GRAY, leading=11.5),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.3, textColor=DARK, leading=13),
    "callout": ParagraphStyle("callout", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.white, leading=13),
    "footer": ParagraphStyle("footer", fontName="Helvetica", fontSize=7.5, textColor=GRAY),
    "tblhead": ParagraphStyle("tblhead", fontName="Helvetica-Bold", fontSize=8.6, textColor=colors.white, leading=11),
    "tblcell": ParagraphStyle("tblcell", fontName="Helvetica", fontSize=8.3, textColor=DARK, leading=11),
    "tblcellB": ParagraphStyle("tblcellB", fontName="Helvetica-Bold", fontSize=8.3, textColor=DARK, leading=11),
}


def header_footer(canvas, doc):
    canvas.saveState()
    # top bar
    canvas.setFillColor(MS_BLUE)
    canvas.rect(0, LETTER[1] - 0.12 * inch, LETTER[0], 0.12 * inch, stroke=0, fill=1)
    # footer
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(0.6 * inch, 0.4 * inch, "Agentic AI Immersion Workshop  |  Pre-Requisites Datasheet")
    canvas.drawRightString(LETTER[0] - 0.6 * inch, 0.4 * inch, f"Page {doc.page}")
    canvas.restoreState()


def bullets(items, style="bullet", bullet_color=MS_BLUE):
    flow = []
    for it in items:
        flow.append(ListItem(Paragraph(it, styles[style]), leftIndent=6, bulletColor=bullet_color))
    return ListFlowable(flow, bulletType="bullet", start="•", leftIndent=14, bulletFontSize=8, spaceBefore=2, spaceAfter=6)


def callout(text, bg=MS_BLUE):
    t = Table([[Paragraph(text, styles["callout"])]], colWidths=[7.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def req_table(rows, col_widths):
    header = [Paragraph(h, styles["tblhead"]) for h in rows[0]]
    data = [header]
    for r in rows[1:]:
        data.append([Paragraph(c, styles["tblcell"]) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), MS_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D0D0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_BG))
    t.setStyle(TableStyle(style))
    return t


story = []

# ---------------- PAGE 1 ----------------
story.append(Paragraph("Agentic AI Immersion Workshop", styles["title"]))
story.append(Paragraph("Pre-Requisites Datasheet &nbsp;&bull;&nbsp; Complete before Day 1", styles["subtitle"]))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E1E1E1"), spaceAfter=10))

story.append(Paragraph(
    "This workshop is hands-on from the first notebook. Every lab authenticates against a live Microsoft Foundry "
    "project using your own Azure identity &mdash; there are no shared demo tenants and no API keys. Complete every "
    "item below <b>before Day 1</b> so class time is spent building agents, not troubleshooting environments.",
    styles["body"]))
story.append(Spacer(1, 8))

story.append(callout("⏱ Azure role assignments can take 5&ndash;15 minutes to propagate. Finish setup at least "
                      "one day before the workshop, not the morning of."))
story.append(Spacer(1, 12))

story.append(Paragraph("1. Choose Your Setup Path", styles["h2"]))
story.append(Paragraph(
    "<b>Recommended &mdash; Dev Container:</b> Install Docker Desktop and Visual Studio Code with the "
    "<i>Dev Containers</i> extension, clone the repository, then <b>F1 → Dev Containers: Reopen in Container</b>. "
    "Python, pinned packages, Azure CLI, Azure Developer CLI (azd), and Jupyter support are pre-installed.",
    styles["body"]))
story.append(Spacer(1, 4))
story.append(Paragraph(
    "<b>Alternative &mdash; Local Setup:</b> Install the tools listed in Section 2 yourself and run "
    "<font face='Courier'>pip install -r requirements.txt</font> in a virtual environment.",
    styles["body"]))

story.append(Paragraph("2. Required Tools &amp; Accounts", styles["h2"]))
tool_rows = [
    ["Requirement", "Details"],
    ["Visual Studio Code", "Latest version, with the Python, Jupyter, and GitHub Copilot extensions installed."],
    ["Git &amp; GitHub account", "Git installed locally and signed in (git config / credential manager). A GitHub "
     "account is required to clone the repo and use GitHub Copilot; run a test <font face='Courier'>git clone</font> "
     "before Day 1 to confirm access."],
    ["Python 3.12+ (3.14 recommended)", "Matches the pinned dependency lock used by the Dev Container. Confirm with "
     "<font face='Courier'>python --version</font>."],
    ["Azure CLI", "Installed and signed in via <font face='Courier'>az login</font>. Confirm the correct "
     "subscription with <font face='Courier'>az account show</font>."],
    ["Azure subscription access", "An Azure subscription (or resource group) where you can create/access a Microsoft "
     "Foundry resource. Contributor-level access is easiest; otherwise request the RBAC roles in Section 4 from "
     "your Azure admin in advance."],
    ["Docker Desktop", "Required for the Dev Container path, and to run a local Redis container used by one "
     "Agent Framework lab (<font face='Courier'>threads/2</font>)."],
]
story.append(req_table(tool_rows, [1.9 * inch, 5.1 * inch]))

story.append(Paragraph("3. Microsoft Foundry Project &amp; Model Deployments", styles["h2"]))
story.append(Paragraph(
    "Every notebook authenticates with <font face='Courier'>DefaultAzureCredential</font> against a Foundry project "
    "endpoint &mdash; <b>no API keys are used</b>. Before Day 1:", styles["body"]))
story.append(bullets([
    "Create a Foundry resource at <font face='Courier'>ai.azure.com</font> → <b>Create project</b> (this creates the "
    "account, a project, and default storage). A region such as East&nbsp;US&nbsp;2 is recommended for model availability.",
    "Deploy the following models under <b>Models + endpoints</b>: <font face='Courier'>gpt-5.4</font>, "
    "<font face='Courier'>gpt-5.4-mini</font>, <font face='Courier'>gpt-5.4-nano</font>, and "
    "<font face='Courier'>text-embedding-3-large</font>. Wait for each to reach status <i>Succeeded</i>.",
    "Add <b>Azure AI Search</b> and <b>Application Insights</b> connections under the project's <b>Connections</b> "
    "tab (used by the search and observability labs).",
    "Copy <font face='Courier'>.env.example</font> to <font face='Courier'>.env</font> at the repo root and fill in "
    "your project endpoint, model names, and search endpoint.",
]))

# push remaining content but keep on page 1 if it fits; force page break to page 2
story.append(PageBreak())

# ---------------- PAGE 2 ----------------
story.append(Paragraph("4. Required Azure Permissions (RBAC)", styles["h2"]))
story.append(Paragraph(
    "Ask your Azure administrator to assign the following <b>data-plane roles</b> before Day 1 (roles can take "
    "5&ndash;15 minutes to propagate after assignment). The repo includes "
    "<font face='Courier'>scripts/setup-permissions.ps1</font>, an idempotent script that assigns all of these "
    "automatically if you have sufficient rights.", styles["body"]))
story.append(Spacer(1, 4))
perm_rows = [
    ["Role", "Assignee", "Scope"],
    ["Foundry User", "Your user account", "Foundry account"],
    ["Cognitive Services OpenAI User", "Your user account", "Foundry account"],
    ["Storage Blob Data Contributor", "Your user account", "Project storage account"],
    ["Search Index Data Contributor", "Your user account", "Azure AI Search resource"],
    ["Search Index Data Reader", "Your user account", "Azure AI Search resource"],
    ["Search Service Contributor", "Your user account", "Azure AI Search resource"],
]
story.append(req_table(perm_rows, [2.3 * inch, 2.1 * inch, 2.6 * inch]))
story.append(Spacer(1, 4))
story.append(Paragraph(
    "<b>Note:</b> The Foundry project's own managed identity and the AI Search managed identity also need "
    "matching roles for evaluation and Foundry IQ labs to work; the setup script assigns these automatically. "
    "If you don't have permission to assign roles yourself, share this section with your Azure admin ahead of time.",
    styles["bodySmall"]))

story.append(Paragraph("5. Verify Your Setup", styles["h2"]))
story.append(Paragraph("Run the following before Day 1 to confirm everything is connected:", styles["body"]))
story.append(bullets([
    "<font face='Courier'>pip install -r requirements.txt</font> completes without errors.",
    "<font face='Courier'>az account show</font> returns the subscription containing your Foundry project.",
    "The verification snippet in the README (loads <font face='Courier'>AIProjectClient</font> against your "
    "<font face='Courier'>FOUNDRY_PROJECT_ENDPOINT</font>) prints <b>“Connected to Foundry.”</b>",
    "Open <font face='Courier'>azure-ai-agents/1-basics.ipynb</font> in VS Code and run the first cell &mdash; a "
    "clean run means you're ready. A 401/403 means roles are still propagating; wait and retry.",
]))

story.append(Paragraph("6. Optional &mdash; Additional Modules", styles["h2"]))
story.append(Paragraph(
    "The items below are <b>not required for Day 1</b> but unlock specific advanced modules later in the "
    "workshop. Set these up only if your agenda includes these sessions.", styles["bodySmall"]))
story.append(Spacer(1, 4))
opt_rows = [
    ["Module", "Additional Requirement"],
    ["Hosted Agents (notebook 10, hosted-agents/, AgentOps/)", "Azure Developer CLI (azd) installed; permission to "
     "create/deploy Foundry hosted-agent container resources in your subscription."],
    ["Observability &amp; Evaluations (observability-and-evaluations/)", "Application Insights connection added to "
     "the Foundry project; public network access enabled on project storage (or private endpoints reachable by "
     "Foundry) so evaluation traces and content-safety calls succeed."],
    ["Agent Framework threads lab (threads/2)", "A local Redis instance: "
     "<font face='Courier'>docker run -d --name redis-workshop -p 6379:6379 redis:7-alpine</font>."],
    ["Model Router lab (13-model-router.ipynb)", "The gpt-5.4-mini and gpt-5.4-nano deployments from Section 3; "
     "the lab skips any tier that isn't deployed."],
    ["AgentOps (GitOps CI/CD demo)", "A GitHub repository with Actions enabled, plus permissions to configure "
     "Azure federated credentials for CI/CD deployment."],
]
story.append(req_table(opt_rows, [2.6 * inch, 4.4 * inch]))

story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#E1E1E1"), spaceAfter=6))
story.append(Paragraph(
    "Repository: github.com/dhangerkapil/agentic-ai-immersion &nbsp;&bull;&nbsp; Questions before Day 1? "
    "Open a GitHub issue on the repository. &nbsp;&bull;&nbsp; Updated September 2026.",
    styles["footer"]))

doc = BaseDocTemplate(OUT_PATH, pagesize=LETTER,
                       leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                       topMargin=0.55 * inch, bottomMargin=0.6 * inch,
                       title="Agentic AI Immersion Workshop - Pre-Requisites Datasheet")
frame = Frame(0.6 * inch, 0.6 * inch, LETTER[0] - 1.2 * inch, LETTER[1] - 1.15 * inch, id="normal")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=header_footer)])
doc.build(story)
print("Saved:", OUT_PATH)
