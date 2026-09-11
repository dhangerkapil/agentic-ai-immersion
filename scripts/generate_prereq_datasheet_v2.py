# -*- coding: utf-8 -*-
"""Generates a colorful v2 of the Agentic AI Immersion Workshop Pre-Requisites Datasheet,
styled after Workshop-Turing-Team-Engineering-for-Building-Agents-v3.pdf (dark hero band,
Microsoft four-color accents, two-column readiness layout)."""
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    ListFlowable, ListItem, PageBreak
)

W, H = LETTER

# ---- Palette (Microsoft four-color accents + dark navy hero) ----
NAVY_DARK = colors.HexColor("#0B2E4A")
NAVY_MID = colors.HexColor("#123E63")
MS_BLUE = colors.HexColor("#0078D4")
MS_GREEN = colors.HexColor("#7FBA00")
MS_AMBER = colors.HexColor("#FFB900")
MS_RED = colors.HexColor("#F25022")
DARK = colors.HexColor("#1B1B1B")
GRAY = colors.HexColor("#5C5C5C")
LIGHT_BG = colors.HexColor("#F3F2F1")
PALE_BLUE = colors.HexColor("#EAF3FB")
PALE_YELLOW = colors.HexColor("#FFF8E1")
WHITE = colors.white

OUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                            "Workshop-Agentic-AI-Immersion-Prerequisites-Datasheet-v2.pdf"))

styles = {
    "eyebrow": ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#9AD0F5"),
                              leading=12, spaceAfter=6, tracking=1),
    "herotitle": ParagraphStyle("herotitle", fontName="Helvetica-Bold", fontSize=25, textColor=WHITE, leading=29),
    "herosub": ParagraphStyle("herosub", fontName="Helvetica-Bold", fontSize=12.5, textColor=MS_AMBER, leading=16, spaceBefore=6, spaceAfter=6),
    "herobody": ParagraphStyle("herobody", fontName="Helvetica", fontSize=10, textColor=colors.HexColor("#DCEBF7"), leading=14),
    "infolabel": ParagraphStyle("infolabel", fontName="Helvetica-Bold", fontSize=7.6, textColor=GRAY, leading=10),
    "infoval": ParagraphStyle("infoval", fontName="Helvetica-Bold", fontSize=11.5, textColor=DARK, leading=14),
    "infosub": ParagraphStyle("infosub", fontName="Helvetica", fontSize=8, textColor=GRAY, leading=10),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11.5, textColor=MS_BLUE, spaceBefore=2, spaceAfter=6),
    "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=9.6, textColor=DARK, spaceBefore=6, spaceAfter=2),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.2, textColor=DARK, leading=12.8),
    "bodySmall": ParagraphStyle("bodySmall", fontName="Helvetica", fontSize=8.3, textColor=GRAY, leading=11),
    "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.0, textColor=DARK, leading=12.5),
    "calloutlabel": ParagraphStyle("calloutlabel", fontName="Helvetica-Bold", fontSize=9.5, textColor=WHITE, leading=12),
    "calloutbody": ParagraphStyle("calloutbody", fontName="Helvetica", fontSize=9.0, textColor=DARK, leading=12.5),
    "footer": ParagraphStyle("footer", fontName="Helvetica", fontSize=7.5, textColor=GRAY),
    "footerB": ParagraphStyle("footerB", fontName="Helvetica-Bold", fontSize=7.5, textColor=DARK),
    "tblhead": ParagraphStyle("tblhead", fontName="Helvetica-Bold", fontSize=8.4, textColor=WHITE, leading=10.5),
    "tblcell": ParagraphStyle("tblcell", fontName="Helvetica", fontSize=8.1, textColor=DARK, leading=10.6),
    "steplabel": ParagraphStyle("steplabel", fontName="Helvetica-Bold", fontSize=7.6, textColor=MS_BLUE, leading=9.5),
    "stepbody": ParagraphStyle("stepbody", fontName="Helvetica", fontSize=8.7, textColor=DARK, leading=11.5),
}

ACCENTS = [MS_BLUE, MS_GREEN, MS_AMBER, MS_RED]


def hexc(c):
    """Return '#RRGGBB' for a reportlab Color, for use in Paragraph markup."""
    r, g, b = [int(round(v * 255)) for v in (c.red, c.green, c.blue)]
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def color_strip(canvas, x, y, w, h_):
    seg = w / len(ACCENTS)
    for i, c in enumerate(ACCENTS):
        canvas.setFillColor(c)
        canvas.rect(x + i * seg, y, seg, h_, stroke=0, fill=1)


def page1_bg(canvas, doc):
    canvas.saveState()
    hero_h = 2.55 * inch
    # gradient-ish hero: two navy bands
    canvas.setFillColor(NAVY_DARK)
    canvas.rect(0, H - hero_h, W, hero_h, stroke=0, fill=1)
    canvas.setFillColor(NAVY_MID)
    canvas.rect(0, H - hero_h, W, 0.35 * inch, stroke=0, fill=1)
    # four color dots top-right of hero
    dot_y = H - 0.5 * inch
    dot_x = W - 1.75 * inch
    for i, c in enumerate(ACCENTS):
        canvas.setFillColor(c)
        canvas.rect(dot_x + i * 0.28 * inch, dot_y, 0.2 * inch, 0.2 * inch, stroke=0, fill=1)
    # footer
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(DARK)
    canvas.drawString(0.6 * inch, 0.38 * inch, "Agentic AI Immersion Workshop")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(1.98 * inch, 0.38 * inch, "| Pre-requisites datasheet")
    canvas.drawRightString(W - 0.6 * inch, 0.38 * inch, f"Page {doc.page} of 2")
    canvas.restoreState()


def page2_bg(canvas, doc):
    canvas.saveState()
    color_strip(canvas, 0, H - 0.16 * inch, W, 0.16 * inch)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(DARK)
    canvas.drawString(0.6 * inch, 0.38 * inch, "Agentic AI Immersion Workshop")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawString(1.98 * inch, 0.38 * inch, "| Pre-requisites datasheet | Updated September 2026")
    canvas.drawRightString(W - 0.6 * inch, 0.38 * inch,
                            f"github.com/dhangerkapil/agentic-ai-immersion  |  Page {doc.page} of 2")
    canvas.restoreState()


def bullets(items, color=MS_BLUE, style="bullet"):
    flow = []
    for it in items:
        flow.append(ListItem(Paragraph(it, styles[style]), leftIndent=4, bulletColor=color))
    return ListFlowable(flow, bulletType="bullet", start="•", leftIndent=12, bulletFontSize=7.5,
                         spaceBefore=1, spaceAfter=3)


def section_bar(title, color=MS_BLUE):
    """Uppercase section label with a colored underline bar."""
    lbl = Paragraph(f"<font color='{hexc(color)}'><b>{title.upper()}</b></font>", ParagraphStyle(
        "sectionlbl", fontName="Helvetica-Bold", fontSize=9.6, textColor=color, spaceAfter=3))
    bar = Table([[""]], colWidths=[3.5 * inch], rowHeights=[2.2])
    bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color)]))
    return [lbl, bar, Spacer(1, 4)]


def req_table(rows, col_widths, header_color=MS_BLUE):
    data = [[Paragraph(h, styles["tblhead"]) for h in rows[0]]]
    for r in rows[1:]:
        data.append([Paragraph(c, styles["tblcell"]) for c in r])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8D8D8")),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_BG))
    t.setStyle(TableStyle(style))
    return t


def left_border_box(paras, border_color=MS_GREEN, bg=LIGHT_BG):
    inner = Table([[p] for p in paras], colWidths=[3.35 * inch])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 1),
    ]))
    wrapper = Table([[inner]], colWidths=[3.45 * inch])
    wrapper.setStyle(TableStyle([
        ("LINEBEFORE", (0, 0), (0, 0), 3, border_color),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 0), (0, 0), 0),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
    ]))
    return wrapper


def step_row(num, phase, phase_color, title, desc):
    circ_style = ParagraphStyle("circ", fontName="Helvetica-Bold", fontSize=9, textColor=WHITE, alignment=1, leading=11)
    circle = Table([[Paragraph(str(num), circ_style)]], colWidths=[0.26 * inch], rowHeights=[0.26 * inch])
    circle.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), phase_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]) if hasattr(TableStyle, "roundedcorners") else ("BOX", (0,0),(-1,-1),0,colors.white),
    ]))
    text = Paragraph(f"<font color='{hexc(phase_color)}'><b>{phase}</b></font><br/><b>{title}</b> &mdash; {desc}",
                      styles["stepbody"])
    row = Table([[circle, text]], colWidths=[0.32 * inch, 3.05 * inch])
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return row


story = []

# ============================ PAGE 1 ============================
story.append(Spacer(1, 0.14 * inch))
story.append(Paragraph("CUSTOMER WORKSHOP  |  MICROSOFT FOUNDRY &amp; AGENT FRAMEWORK", styles["eyebrow"]))
story.append(Paragraph("Agentic AI Immersion Workshop", styles["herotitle"]))
story.append(Paragraph("Pre-Requisites Checklist &mdash; Complete Before Day 1", styles["herosub"]))
story.append(Paragraph(
    "Every lab authenticates against a live Microsoft Foundry project with your own Azure identity &mdash; "
    "no shared tenants, no API keys. Work through this checklist before Day 1 so class time is spent building "
    "agents, not troubleshooting environments.", styles["herobody"]))
story.append(Spacer(1, 0.24 * inch))

info_row = [[
    Paragraph("SETUP TIME", styles["infolabel"]),
    Paragraph("DELIVERY", styles["infolabel"]),
    Paragraph("DEADLINE", styles["infolabel"]),
], [
    Paragraph("45&ndash;60 minutes", styles["infoval"]),
    Paragraph("Dev Container or local install", styles["infoval"]),
    Paragraph("1 business day before class", styles["infoval"]),
], [
    Paragraph("Plus 5&ndash;15 min role propagation", styles["infosub"]),
    Paragraph("VS Code required either way", styles["infosub"]),
    Paragraph("RBAC roles need time to propagate", styles["infosub"]),
]]
info_tbl = Table(info_row, colWidths=[2.33 * inch, 2.33 * inch, 2.34 * inch])
info_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
    ("LINEAFTER", (0, 0), (0, -1), 1, colors.HexColor("#D8D8D8")),
    ("LINEAFTER", (1, 0), (1, -1), 1, colors.HexColor("#D8D8D8")),
    ("TOPPADDING", (0, 0), (-1, 0), 7),
    ("BOTTOMPADDING", (0, -1), (-1, -1), 7),
    ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ("TOPPADDING", (0, 1), (-1, 1), 1),
    ("BOTTOMPADDING", (0, 1), (-1, 1), 1),
]))
story.append(info_tbl)
story.append(Spacer(1, 10))

story.extend(section_bar("Why This Matters", MS_BLUE))
story.append(Paragraph(
    "This workshop is hands-on from the first notebook &mdash; there's no lecture-only warm-up period. If your "
    "Azure identity, Foundry project, or local tools aren't ready, the first lab (and the RBAC propagation delay "
    "behind it) can eat 20&ndash;30 minutes of class time you won't get back.", styles["body"]))
story.append(Spacer(1, 8))

story.extend(section_bar("Choose Your Setup Path", MS_GREEN))
path_tbl = Table([
    [Paragraph("<font color='#7FBA00'><b>OPTION A &mdash; RECOMMENDED</b></font><br/><b>Dev Container</b>", styles["h3"]),
     Paragraph("<font color='#0078D4'><b>OPTION B</b></font><br/><b>Local Setup</b>", styles["h3"])],
    [Paragraph("Install Docker Desktop + VS Code with the Dev Containers extension, clone the repo, then "
               "<b>F1 → Dev Containers: Reopen in Container</b>. Python, pinned packages, Azure CLI, azd, and "
               "Jupyter are pre-installed for you.", styles["body"]),
     Paragraph("Install the tools in the checklist below yourself, then run "
               "<font face='Courier'>pip install -r requirements.txt</font> inside a virtual environment.",
               styles["body"])],
], colWidths=[3.4 * inch, 3.4 * inch])
path_tbl.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BOX", (0, 0), (0, -1), 0.75, MS_GREEN),
    ("BOX", (1, 0), (1, -1), 0.75, MS_BLUE),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(path_tbl)
story.append(Spacer(1, 8))

story.extend(section_bar("Required Tools &amp; Accounts", MS_BLUE))
tool_rows = [
    ["Requirement", "Details"],
    ["Visual Studio Code", "Latest version, with the Python, Jupyter, and GitHub Copilot extensions installed."],
    ["Git &amp; GitHub account", "Git installed and signed in (git config / credential manager). Needed to clone the "
     "repo and use GitHub Copilot &mdash; test with a <font face='Courier'>git clone</font> before Day 1."],
    ["Python 3.12+ (3.14 recommended)", "Matches the pinned dependency lock used by the Dev Container. Confirm with "
     "<font face='Courier'>python --version</font>."],
    ["Azure CLI", "Installed and signed in via <font face='Courier'>az login</font>. Confirm the subscription with "
     "<font face='Courier'>az account show</font>."],
    ["Azure subscription access", "Access to create/use a Microsoft Foundry resource. Contributor is easiest; "
     "otherwise request the RBAC roles on page 2 from your Azure admin in advance."],
    ["Docker Desktop", "Needed for the Dev Container path, and for a local Redis container used by one Agent "
     "Framework lab (<font face='Courier'>threads/2</font>)."],
]
story.append(req_table(tool_rows, [1.9 * inch, 4.9 * inch], header_color=MS_BLUE))

story.append(PageBreak())

# ============================ PAGE 2 ============================
story.append(Spacer(1, 0.07 * inch))
story.append(Paragraph("<font color='#0078D4'><b>DELIVERY READINESS</b></font>", ParagraphStyle(
    "eyebrow2", fontName="Helvetica-Bold", fontSize=9.5, textColor=MS_BLUE, spaceAfter=2)))
story.append(Paragraph("Readiness, Permissions &amp; Optional Modules", ParagraphStyle(
    "h1b", fontName="Helvetica-Bold", fontSize=15, textColor=DARK, spaceAfter=8)))

story.extend(section_bar("Foundry Project &amp; Model Deployments", MS_AMBER))
story.append(Paragraph(
    "Every notebook authenticates with <font face='Courier'>DefaultAzureCredential</font> &mdash; "
    "<b>no API keys</b>. Before Day 1:", styles["body"]))
story.append(bullets([
    "Create a Foundry resource at <font face='Courier'>ai.azure.com</font> → <b>Create project</b> (region "
    "such as East&nbsp;US&nbsp;2 recommended for model availability).",
    "Deploy <font face='Courier'>gpt-5.4</font>, <font face='Courier'>gpt-5.4-mini</font>, "
    "<font face='Courier'>gpt-5.4-nano</font>, and <font face='Courier'>text-embedding-3-large</font> under "
    "<b>Models + endpoints</b>; wait for status <i>Succeeded</i>.",
    "Add <b>Azure AI Search</b> and <b>Application Insights</b> connections under <b>Connections</b>.",
    "Copy <font face='Courier'>.env.example</font> to <font face='Courier'>.env</font> and fill in your endpoint, "
    "model names, and search endpoint.",
], color=MS_AMBER))
story.append(Spacer(1, 4))

left_col = []
left_col.extend(section_bar("Required Azure Permissions (RBAC)", MS_BLUE))
left_col.append(Paragraph(
    "Ask your Azure admin to assign these <b>data-plane roles</b> before Day 1 (allow 5&ndash;15 minutes to "
    "propagate). <font face='Courier'>scripts/setup-permissions.ps1</font> assigns all of them automatically "
    "if you have sufficient rights.", styles["body"]))
left_col.append(Spacer(1, 3))
perm_rows = [
    ["Role", "Scope"],
    ["Foundry User", "Foundry account"],
    ["Cognitive Services OpenAI User", "Foundry account"],
    ["Storage Blob Data Contributor", "Project storage account"],
    ["Search Index Data Contributor", "Azure AI Search resource"],
    ["Search Index Data Reader", "Azure AI Search resource"],
    ["Search Service Contributor", "Azure AI Search resource"],
]
left_col.append(req_table(perm_rows, [2.15 * inch, 2.15 * inch], header_color=MS_BLUE))
left_col.append(Spacer(1, 3))
left_col.append(Paragraph(
    "<b>Note:</b> the Foundry project's managed identity and the AI Search managed identity also need matching "
    "roles for evaluation and Foundry IQ labs &mdash; the setup script covers this automatically.",
    styles["bodySmall"]))
left_col.append(Spacer(1, 6))

left_col.extend(section_bar("Verify Your Setup", MS_GREEN))
left_col.append(bullets([
    "<font face='Courier'>pip install -r requirements.txt</font> completes without errors.",
    "<font face='Courier'>az account show</font> returns the subscription with your Foundry project.",
    "The README's <font face='Courier'>AIProjectClient</font> verification snippet prints "
    "<b>“Connected to Foundry.”</b>",
    "<font face='Courier'>azure-ai-agents/1-basics.ipynb</font> runs cleanly in VS Code. A 401/403 means roles "
    "are still propagating &mdash; wait and retry.",
], color=MS_GREEN))

right_col = []
right_col.extend(section_bar("Optional — Additional Modules", MS_RED))
right_col.append(Paragraph(
    "Not required for Day 1 &mdash; set up only if your agenda includes these sessions.", styles["bodySmall"]))
right_col.append(Spacer(1, 4))
opt_items = [
    ("Hosted Agents", "notebook 10, hosted-agents/, AgentOps/",
     "Azure Developer CLI (azd) installed; permission to deploy Foundry hosted-agent containers."),
    ("Observability &amp; Evaluations", "observability-and-evaluations/",
     "Application Insights connection on the project; public network access (or reachable private endpoints) "
     "on project storage."),
    ("Agent Framework threads lab", "threads/2",
     "Local Redis: <font face='Courier'>docker run -d --name redis-workshop -p 6379:6379 redis:7-alpine</font>."),
    ("Model Router lab", "13-model-router.ipynb",
     "The gpt-5.4-mini and gpt-5.4-nano deployments; the lab skips any tier that isn't deployed."),
    ("AgentOps (GitOps CI/CD demo)", "AgentOps/",
     "A GitHub repo with Actions enabled, plus rights to configure Azure federated credentials for CI/CD."),
]
for title, ref, desc in opt_items:
    right_col.append(left_border_box([
        Paragraph(f"<b>{title}</b> <font color='#5C5C5C' size=7.5>({ref})</font>", styles["h3"]),
        Paragraph(desc, styles["body"]),
    ], border_color=MS_RED, bg=colors.HexColor("#FDEEEA")))
    right_col.append(Spacer(1, 4))

two_col = Table([[left_col, right_col]], colWidths=[3.55 * inch, 3.55 * inch])
two_col.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (0, 0), 0),
    ("RIGHTPADDING", (0, 0), (0, 0), 14),
    ("LEFTPADDING", (1, 0), (1, 0), 14),
    ("RIGHTPADDING", (1, 0), (1, 0), 0),
]))
story.append(two_col)
story.append(Spacer(1, 4))

# Governance-style callout (yellow), full width
gov_box = Table([[
    Paragraph("<b>NEED HELP</b><br/>BEFORE DAY 1", ParagraphStyle(
        "govlbl", fontName="Helvetica-Bold", fontSize=9.5, textColor=DARK, leading=12)),
    Paragraph(
        "If you can't assign yourself the RBAC roles above, or your subscription/tenant is locked down, share "
        "page 2 of this datasheet with your Azure administrator now &mdash; role propagation alone can take up "
        "to 15 minutes, so don't wait until the morning of the workshop. Questions about scope or access: open a "
        "GitHub issue on the repository.", styles["calloutbody"]),
]], colWidths=[1.5 * inch, 5.6 * inch])
gov_box.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), PALE_YELLOW),
    ("BOX", (0, 0), (-1, -1), 1, MS_AMBER),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
]))
story.append(gov_box)
story.append(Spacer(1, 5))

story.extend(section_bar("Included vs. Out of Scope for Setup", MS_BLUE))
scope_tbl = Table([
    [Paragraph("<font color='#7FBA00'><b>YOU HANDLE</b></font>", styles["h3"]),
     Paragraph("<font color='#F25022'><b>NOT NEEDED FOR DAY 1</b></font>", styles["h3"])],
    [bullets([
        "VS Code, Git, Python, Azure CLI installed",
        "Foundry project created + models deployed",
        "RBAC roles assigned (self-service or via admin)",
        ".env file populated from .env.example",
     ], color=MS_GREEN),
     bullets([
        "Azure Developer CLI (azd) &mdash; hosted agents only",
        "Application Insights wiring &mdash; observability only",
        "Local Redis &mdash; one Agent Framework lab only",
        "GitHub Actions / federated creds &mdash; AgentOps demo only",
     ], color=MS_RED)],
], colWidths=[3.55 * inch, 3.55 * inch])
scope_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story.append(scope_tbl)

doc = BaseDocTemplate(OUT_PATH, pagesize=LETTER,
                       leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                       topMargin=0.5 * inch, bottomMargin=0.55 * inch,
                       title="Agentic AI Immersion Workshop - Pre-Requisites Datasheet v2")

frame_hero = Frame(0.6 * inch, 0.42 * inch, W - 1.2 * inch, H - 0.92 * inch, id="hero",
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
frame_p2 = Frame(0.6 * inch, 0.42 * inch, W - 1.2 * inch, H - 0.92 * inch, id="p2")

doc.addPageTemplates([
    PageTemplate(id="page1", frames=[frame_hero], onPage=page1_bg),
    PageTemplate(id="page2", frames=[frame_p2], onPage=page2_bg),
])

# force template switch after page 1
from reportlab.platypus import NextPageTemplate
story.insert(0, NextPageTemplate("page1"))
# find PageBreak index to insert NextPageTemplate for page2 right before it
for idx, item in enumerate(story):
    if isinstance(item, PageBreak):
        story.insert(idx, NextPageTemplate("page2"))
        break

doc.build(story)
print("Saved:", OUT_PATH)
