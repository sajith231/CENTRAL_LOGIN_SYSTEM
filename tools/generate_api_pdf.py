from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Preformatted, HRFlowable,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


OUT = "output/pdf/license-create-api-documentation.pdf"
PAGE_W, PAGE_H = A4
NAVY = colors.HexColor("#12243A")
BLUE = colors.HexColor("#1D5D8F")
TEAL = colors.HexColor("#0E7C7B")
LIGHT = colors.HexColor("#F2F6FA")
MID = colors.HexColor("#D7E2EC")
TEXT = colors.HexColor("#263746")
MUTED = colors.HexColor("#607487")
RED = colors.HexColor("#A63D40")
GREEN = colors.HexColor("#237A57")


def setup_fonts():
    regular = r"C:\Windows\Fonts\segoeui.ttf"
    semibold = r"C:\Windows\Fonts\seguisb.ttf"
    mono = r"C:\Windows\Fonts\consola.ttf"
    try:
        pdfmetrics.registerFont(TTFont("Segoe", regular))
        pdfmetrics.registerFont(TTFont("Segoe-Semi", semibold))
        pdfmetrics.registerFont(TTFont("Consolas", mono))
        return "Segoe", "Segoe-Semi", "Consolas"
    except Exception:
        return "Helvetica", "Helvetica-Bold", "Courier"


REG, SEMI, MONO = setup_fonts()
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="DocTitle", fontName=SEMI, fontSize=25, leading=30, textColor=colors.white, alignment=TA_LEFT, spaceAfter=7))
styles.add(ParagraphStyle(name="Subtitle", fontName=REG, fontSize=10.5, leading=15, textColor=colors.HexColor("#D9E7F2")))
styles.add(ParagraphStyle(name="H1x", fontName=SEMI, fontSize=17, leading=22, textColor=NAVY, spaceBefore=5, spaceAfter=9))
styles.add(ParagraphStyle(name="H2x", fontName=SEMI, fontSize=11.5, leading=15, textColor=BLUE, spaceBefore=9, spaceAfter=5))
styles.add(ParagraphStyle(name="Bodyx", fontName=REG, fontSize=9.1, leading=13.3, textColor=TEXT, spaceAfter=6))
styles.add(ParagraphStyle(name="Smallx", fontName=REG, fontSize=7.8, leading=10.3, textColor=MUTED))
styles.add(ParagraphStyle(name="Tablex", fontName=REG, fontSize=8.1, leading=10.5, textColor=TEXT))
styles.add(ParagraphStyle(name="TableHead", fontName=SEMI, fontSize=8.1, leading=10.5, textColor=colors.white))
styles.add(ParagraphStyle(name="Codex", fontName=MONO, fontSize=7.1, leading=9.3, textColor=colors.HexColor("#E8F2F8")))
styles.add(ParagraphStyle(name="Callout", fontName=REG, fontSize=8.8, leading=12.5, textColor=TEXT, leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=4))


def P(text, style="Bodyx"):
    return Paragraph(text, styles[style])


def code(text):
    return Preformatted(text.strip("\n"), styles["Codex"])


def box(content, bg=LIGHT, border=MID, pad=8):
    t = Table([[content]], colWidths=[174*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.7, border),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]))
    return t


def code_box(text):
    return box(code(text), bg=NAVY, border=NAVY, pad=10)


def table(rows, widths, header=True):
    converted = []
    for r, row in enumerate(rows):
        converted.append([P(str(cell), "TableHead" if header and r == 0 else "Tablex") for cell in row])
    t = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.45, MID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), BLUE))
        cmds.append(("TEXTCOLOR", (0, 0), (-1, 0), colors.white))
    for i in range(1 if header else 0, len(rows)):
        if i % 2 == (1 if header else 0):
            cmds.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F8FBFD")))
    t.setStyle(TableStyle(cmds))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page == 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, PAGE_H - 55*mm, PAGE_W, 55*mm, fill=1, stroke=0)
        canvas.setFillColor(TEAL)
        canvas.rect(0, PAGE_H - 57*mm, PAGE_W, 2*mm, fill=1, stroke=0)
    else:
        canvas.setStrokeColor(MID)
        canvas.setLineWidth(0.5)
        canvas.line(18*mm, PAGE_H - 15*mm, PAGE_W - 18*mm, PAGE_H - 15*mm)
        canvas.setFont(SEMI, 7.5)
        canvas.setFillColor(NAVY)
        canvas.drawString(18*mm, PAGE_H - 11*mm, "IMC | License Create API")
    canvas.setStrokeColor(MID)
    canvas.line(18*mm, 14*mm, PAGE_W - 18*mm, 14*mm)
    canvas.setFont(REG, 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(18*mm, 9*mm, "Implementation reference: auto_licence/views.py")
    canvas.drawRightString(PAGE_W - 18*mm, 9*mm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    frame = Frame(18*mm, 19*mm, PAGE_W - 36*mm, PAGE_H - 40*mm, id="normal", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=21*mm, bottomMargin=19*mm, title="IMC License Create API Documentation", author="IMC")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=header_footer)])
    story = []

    story += [Spacer(1, 9*mm), P("License Create API", "DocTitle"), P("Production integration reference for creating mobile application licences", "Subtitle"), Spacer(1, 26*mm)]
    story += [P("Endpoint at a glance", "H1x")]
    story += [table([
        ["Property", "Value"],
        ["Method", "POST"],
        ["Primary URL", "https://activate.imcbs.com/t-erp/mobileapp/api/license/create/"],
        ["Content type", "application/json"],
        ["Success codes", "201 Created when at least one licence is created; 200 OK when all requested licences are skipped"],
        ["Error code", "400 Bad Request for invalid JSON, missing fields, invalid project/package pairs, or T-ERP restrictions"],
    ], [37*mm, 137*mm])]
    story += [Spacer(1, 5*mm), box(P("Scope note: This document reflects the current Django implementation and route configuration. The view is CSRF-exempt and does not declare an authentication decorator; secure the endpoint at the gateway or add authentication before exposing it beyond a trusted integration boundary.", "Callout"), bg=colors.HexColor("#FFF7E6"), border=colors.HexColor("#E4B34B")), Spacer(1, 8*mm)]
    story += [P("Behavior summary", "H2x"), P("The API accepts one company payload and a non-empty list of project/package selections. It validates every selection before creating any records. A company is matched by exact email: an existing company is reused, and a licence already present for that company and project is returned as skipped_existing. New licences are created with a generated license_key, an automatic billing-history record, licence type new, and an active status.", "Bodyx")]
    story += [P("Route behavior", "H2x"), table([
        ["Route", "T-ERP rule", "Validity"],
        ["/t-erp/mobileapp/api/license/create/", "Each selected project must have t_erp enabled", "14 days"],
    ], [62*mm, 70*mm, 42*mm])]
    story += [PageBreak()]

    story += [P("1. Request", "H1x"), P("Send a JSON object with corporate details, company details, and at least one project/package pair. Project and package values are exact matches: spelling, spaces, and capitalization are significant.", "Bodyx"), P("Minimal valid request", "H2x")]
    story += [code_box('''{
  "corporate": {
    "name": "Corporate Name",
    "place": "Optional place"
  },
  "company": {
    "name": "Company Name",
    "place": "Optional place",
    "email": "company@domain.com",
    "contact_no": "+91 9000000000",
    "country": "India",
    "is_active": true
  },
  "projects": [
    { "project": "Exact Project Name", "package": "Exact Package Name" }
  ]
}'''), Spacer(1, 7*mm)]
    story += [P("Request fields", "H2x"), table([
        ["Field", "Type", "Required", "Description"],
        ["corporate.name", "string", "Yes", "Corporate/store name. Required only when the company email is new."],
        ["corporate.place", "string", "No", "Corporate/store place. Defaults to empty string."],
        ["company.name", "string", "Yes", "Company/shop name. If email already exists, the stored name wins."],
        ["company.place", "string", "No", "Company/shop place. Defaults to empty string."],
        ["company.email", "string", "Yes", "Used as client_id and company reuse key. Maximum 50 characters."],
        ["company.contact_no", "string", "No", "Company contact number."],
        ["company.country", "string", "No", "Defaults to India. Currency is derived server-side."],
        ["company.is_active", "boolean", "No", "Defaults to true."],
        ["projects", "array", "Yes", "Non-empty array. Each project may appear once only."],
        ["projects[].project", "string", "Yes", "Exact project name."],
        ["projects[].package", "string", "Yes", "Exact package name belonging to that project."],
    ], [39*mm, 20*mm, 19*mm, 96*mm])]
    story += [Spacer(1, 5*mm), P("cURL example", "H2x"), code_box('''curl -X POST \\
  "https://activate.imcbs.com/t-erp/mobileapp/api/license/create/" \\
  -H "Content-Type: application/json" \\
  -d @request.json''')]
    story += [PageBreak()]

    story += [P("2. Processing rules", "H1x"), P("The operation is transactional. The request is fully validated before creation, and licence creation runs inside a single database transaction.", "Bodyx")]
    story += [table([
        ["Rule", "Implementation behavior"],
        ["Project matching", "Exact project_name match. Missing projects return 400. Duplicate names in the same request return 400."],
        ["Package matching", "The package must exist under the selected project and match exactly. A package from another project is rejected."],
        ["T-ERP eligibility", "Every selected project must have t_erp enabled, otherwise the entire request is rejected."],
        ["Company reuse", "Shop is found by company.email. Existing store/shop details and client_id are reused as-is."],
        ["Duplicate licence", "If the company already has a licence for a selected project, that item is skipped with status skipped_existing."],
        ["Users / login limit", "Uses package.users_count. If zero, null, or otherwise unlimited, falls back to 50."],
        ["Validity", "T-ERP route: 14 days. Regular route, if enabled later: 30 days."],
        ["Billing", "Creates a billing-history record with bill_status true and payment_status Not Paid."],
        ["Currency", "Derived from country using the server-side country mapping; no currency_code request field is accepted."],
    ], [43*mm, 131*mm])]
    story += [Spacer(1, 7*mm), P("Bulk request example", "H2x"), code_box('''{
  "corporate": { "name": "IMC Developments", "place": "India" },
  "company": {
    "name": "Acme Retail",
    "email": "ops@acme.example",
    "country": "India"
  },
  "projects": [
    { "project": "Trellisco Alpha", "package": "Prime" },
    { "project": "Trellisco Beta", "package": "Prime" }
  ]
}'''), Spacer(1, 5*mm), box(P("Important: If one project/package entry is invalid, no new company, licence, or billing record is created for the request.", "Callout"), bg=colors.HexColor("#FDECEC"), border=colors.HexColor("#E4A5A7"))]
    story += [PageBreak()]

    story += [P("3. Success response", "H1x"), P("A successful response returns the company identity and one result item per requested project. HTTP 201 indicates that at least one licence was created. HTTP 200 indicates all requested project licences already existed and were skipped.", "Bodyx")]
    story += [code_box('''{
  "success": true,
  "message": "2 licence(s) created, 0 skipped (a licence already exists for this company under the project).",
  "reused_existing_company": false,
  "created_count": 2,
  "skipped_count": 0,
  "corporate": {
    "name": "IMC Developments",
    "place": "India",
    "store_id": 123
  },
  "company": {
    "name": "Acme Retail",
    "place": "",
    "email": "ops@acme.example",
    "contact_no": "",
    "country": "India",
    "currency_code": "INR",
    "client_id": "ops@acme.example"
  },
  "results": [
    {
      "project": "Trellisco Alpha",
      "package": "Prime",
      "status": "created",
      "license_key": "generated-key",
      "users_count": 10,
      "login_limit": 10,
      "expiry_date": "2026-12-01T10:30:00+00:00"
    }
  ]
}'''), Spacer(1, 7*mm)]
    story += [P("Response fields", "H2x"), table([
        ["Field", "Meaning"],
        ["success", "Always true for a successful operation."],
        ["reused_existing_company", "true when the email matched an existing shop."],
        ["created_count / skipped_count", "Counts of created and skipped result items."],
        ["corporate", "Resolved corporate/store identity, including store_id."],
        ["company", "Resolved company/shop identity. client_id equals the email used for matching."],
        ["results[].status", "created or skipped_existing."],
        ["results[].license_key", "Returned only for created licences."],
        ["results[].expiry_date", "ISO 8601 timestamp for the created licence."],
    ], [56*mm, 118*mm])]
    story += [Spacer(1, 5*mm), P("Mixed create and skip", "H2x"), P("When an existing email has a licence for one selected project but not another, the response can contain both statuses. The existing company is reused once, the already-licensed project is skipped, and the remaining project is created.", "Bodyx")]
    story += [PageBreak()]

    story += [P("4. Error responses", "H1x"), P("Errors use the same compact shape and do not create partial records.", "Bodyx"), code_box('''{
  "success": false,
  "error": "company.email is required (client_id is set from it)"
}'''), Spacer(1, 7*mm)]
    story += [table([
        ["HTTP", "Example condition", "Example error"],
        ["400", "Malformed JSON", "Invalid JSON body"],
        ["400", "Missing corporate name", "corporate.name is required"],
        ["400", "Missing company email", "company.email is required (client_id is set from it)"],
        ["400", "Email over 50 characters", "company.email is too long to be used as client_id (max 50 chars)"],
        ["400", "Missing projects", "projects is required and must be a non-empty list..."],
        ["400", "Unknown project", "Project '...' not found. Project name must match exactly..."],
        ["400", "Unknown package", "Package '...' not found for project '...'..."],
        ["400", "Duplicate project", "Project '...' is listed more than once..."],
        ["400", "T-ERP disabled", "Project '...' is not enabled for the T-ERP licence create API..."],
        ["400", "No branch configured", "No branch configured for project '...' and default branch..."],
    ], [17*mm, 51*mm, 106*mm])]
    story += [Spacer(1, 8*mm), P("Integration checklist", "H2x")]
    checklist = [
        "Use the trailing slash exactly as shown in the URL.",
        "Send Content-Type: application/json.",
        "Use the exact project and package names configured in IMC.",
        "Treat 201 and 200 as successful HTTP responses.",
        "Inspect each results[] item; a successful request may include skipped_existing items.",
        "Persist license_key and expiry_date for created items.",
        "Do not send currency_code; the server derives it from country.",
        "Protect the endpoint with gateway authentication or add an application authentication layer before production exposure.",
    ]
    story += [table([["Check", "Action"]] + [["OK", x] for x in checklist], [13*mm, 161*mm])]
    story += [Spacer(1, 8*mm), P("Implementation reference", "H2x"), P("Generated from the current route and view implementation in auto_licence/urls.py and auto_licence/views.py. The API contract should be updated if the server-side validation, authentication, or response schema changes.", "Smallx")]

    doc.build(story)


if __name__ == "__main__":
    build()
