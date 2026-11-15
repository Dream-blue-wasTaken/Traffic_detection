"""Shared layout helpers and styles for the KIIT project report PDF."""

from __future__ import annotations

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "report_assets")

NAVY = colors.HexColor("#1F3864")
GREY = colors.HexColor("#555555")
LIGHT = colors.HexColor("#DCE6F1")
PALE = colors.HexColor("#F4F7FB")
LINE = colors.HexColor("#8C9BB0")
GOLD = colors.HexColor("#8A6D1F")

# ----------------------------------------------------------------- fonts
FONT_DIR = "C:/Windows/Fonts"
_FONTS = {
    "TNR": "times.ttf",
    "TNR-Bold": "timesbd.ttf",
    "TNR-Italic": "timesi.ttf",
    "TNR-BoldItalic": "timesbi.ttf",
}
for name, fname in _FONTS.items():
    path = os.path.join(FONT_DIR, fname)
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont(name, path))

try:
    pdfmetrics.registerFontFamily(
        "TNR", normal="TNR", bold="TNR-Bold", italic="TNR-Italic", boldItalic="TNR-BoldItalic"
    )
    BASE = "TNR"
except Exception:  # pragma: no cover - fallback on machines without the fonts
    BASE = "Times-Roman"

BOLD = f"{BASE}-Bold" if BASE == "TNR" else "Times-Bold"
ITAL = f"{BASE}-Italic" if BASE == "TNR" else "Times-Italic"

# ----------------------------------------------------------------- styles
STYLES = {
    "Body": ParagraphStyle(
        "Body", fontName=BASE, fontSize=12, leading=18, alignment=TA_JUSTIFY,
        spaceAfter=6, firstLineIndent=0,
    ),
    "BodyCenter": ParagraphStyle(
        "BodyCenter", parent=ParagraphStyle("x", fontName=BASE, fontSize=12, leading=18),
        alignment=TA_CENTER, spaceAfter=6,
    ),
    "ChapterLabel": ParagraphStyle(
        "ChapterLabel", fontName=BOLD, fontSize=13, leading=18, alignment=TA_CENTER,
        textColor=NAVY, spaceBefore=6, spaceAfter=2,
    ),
    "ChapterTitle": ParagraphStyle(
        "ChapterTitle", fontName=BOLD, fontSize=18, leading=24, alignment=TA_CENTER,
        textColor=NAVY, spaceAfter=4,
    ),
    "Section": ParagraphStyle(
        "Section", fontName=BOLD, fontSize=14, leading=19, spaceBefore=14,
        spaceAfter=6, textColor=NAVY, keepWithNext=1,
    ),
    "Subsection": ParagraphStyle(
        "Subsection", fontName=BOLD, fontSize=12, leading=17, spaceBefore=10,
        spaceAfter=4, keepWithNext=1,
    ),
    "SubSub": ParagraphStyle(
        "SubSub", fontName=f"{BASE}-Bold" if BASE == "TNR" else "Times-Bold",
        fontSize=12, leading=16, spaceBefore=8, spaceAfter=3, keepWithNext=1,
    ),
    "Caption": ParagraphStyle(
        "Caption", fontName=ITAL, fontSize=9.5, leading=12.5, alignment=TA_CENTER,
        spaceBefore=4, spaceAfter=10, textColor=colors.HexColor("#333333"),
    ),
    "TableCaption": ParagraphStyle(
        "TableCaption", fontName=ITAL, fontSize=9.5, leading=12.5, alignment=TA_CENTER,
        spaceBefore=8, spaceAfter=4,
    ),
    "Bullet": ParagraphStyle(
        "Bullet", fontName=BASE, fontSize=12, leading=17.5, alignment=TA_JUSTIFY,
        leftIndent=18, bulletIndent=6, spaceAfter=3,
    ),
    "TH": ParagraphStyle(
        "TH", fontName=BOLD, fontSize=8.6, leading=10.8, alignment=TA_CENTER,
        textColor=colors.white,
    ),
    "TD": ParagraphStyle(
        "TD", fontName=BASE, fontSize=8.6, leading=10.8, alignment=TA_LEFT,
    ),
    "TDC": ParagraphStyle(
        "TDC", fontName=BASE, fontSize=8.6, leading=10.8, alignment=TA_CENTER,
    ),
    "TOC": ParagraphStyle("TOC", fontName=BASE, fontSize=11, leading=15),
    "TOCBold": ParagraphStyle("TOCBold", fontName=BOLD, fontSize=11.5, leading=16),
    "TOCPage": ParagraphStyle(
        "TOCPage", fontName=BASE, fontSize=11, leading=15, alignment=TA_RIGHT
    ),
    "TOCPageBold": ParagraphStyle(
        "TOCPageBold", fontName=BOLD, fontSize=11.5, leading=16, alignment=TA_RIGHT
    ),
    "FrontTitle": ParagraphStyle(
        "FrontTitle", fontName=BOLD, fontSize=16, leading=22, alignment=TA_CENTER,
        textColor=NAVY, spaceBefore=4, spaceAfter=14,
    ),
    "CoverBig": ParagraphStyle(
        "CoverBig", fontName=BOLD, fontSize=20, leading=26, alignment=TA_CENTER,
        textColor=NAVY, spaceAfter=6,
    ),
    "CoverMid": ParagraphStyle(
        "CoverMid", fontName=BASE, fontSize=12.5, leading=19, alignment=TA_CENTER,
    ),
    "CoverBold": ParagraphStyle(
        "CoverBold", fontName=BOLD, fontSize=12.5, leading=19, alignment=TA_CENTER,
    ),
    "Ref": ParagraphStyle(
        "Ref", fontName=BASE, fontSize=11, leading=16, leftIndent=22,
        firstLineIndent=-22, spaceAfter=5, alignment=TA_JUSTIFY,
    ),
}


def P(text: str, style: str = "Body") -> Paragraph:
    return Paragraph(text, STYLES[style])


def bullets(items: list[str]) -> list[Paragraph]:
    return [Paragraph(f"•&nbsp;&nbsp;{t}", STYLES["Bullet"]) for t in items]


def caption(kind: str, num: str, text: str) -> Paragraph:
    full = f"{kind} {num}: {text}"
    p = Paragraph(full, STYLES["Caption"] if kind == "Figure" else STYLES["TableCaption"])
    p.caption_text = full
    p.caption_kind = "fig" if kind == "Figure" else "tab"
    return p


def heading_toc(paragraph: Paragraph, text: str, level: int) -> Paragraph:
    paragraph.toc_text = text
    paragraph.toc_level = level
    return paragraph


def chapter(num: int, title: str) -> list:
    """Return a page break plus the KIIT-style chapter opening."""
    p = heading_toc(P(title, "ChapterTitle"), f"{num}    {title}", 0)
    return [
        PageBreak(),
        Spacer(1, 0.3 * cm),
        P(f"Chapter {num}", "ChapterLabel"),
        p,
        Spacer(1, 0.15 * cm),
        Table([[""]], colWidths=[16 * cm], rowHeights=[0.05 * cm],
              style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY)])),
        Spacer(1, 0.55 * cm),
    ]


def section(num: str, title: str) -> Paragraph:
    return heading_toc(P(f"{num}  {title}", "Section"), f"{num}    {title}", 1)


def subsection(num: str, title: str) -> Paragraph:
    return heading_toc(P(f"{num}  {title}", "Subsection"), f"{num}    {title}", 2)


def figure(path: str, num: str, text: str, width_cm: float = 15.4) -> KeepTogether:
    img = Image(os.path.join(ASSETS, path))
    w = width_cm * cm
    h = w * img.imageHeight / img.imageWidth
    if h > 18.2 * cm:
        h = 18.2 * cm
        w = h * img.imageWidth / img.imageHeight
    img.drawWidth = w
    img.drawHeight = h
    return KeepTogether([Spacer(1, 0.15 * cm), img, caption("Figure", num, text)])


def data_table(
    num: str,
    text: str,
    header: list[str],
    rows: list[list[str]],
    widths: list[float],
    align: str = "left",
    font_size: float | None = None,
) -> list:
    th = STYLES["TH"]
    td = STYLES["TD"] if align == "left" else STYLES["TDC"]
    data = [[Paragraph(h, th) for h in header]]
    for row in rows:
        data.append([Paragraph(str(c), td) for c in row])
    table = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), PALE))
    table.setStyle(TableStyle(style))
    return [caption("Table", num, text), table, Spacer(1, 0.35 * cm)]


class ReportDoc(BaseDocTemplate):
    """Document template that records heading/caption pages and draws the footer."""

    def __init__(self, filename: str, records: dict, **kwargs):
        super().__init__(filename, pagesize=A4,
                         leftMargin=2.5 * cm, rightMargin=2.5 * cm,
                         topMargin=2.4 * cm, bottomMargin=2.4 * cm, **kwargs)
        self.records = records
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="main")
        self.addPageTemplates([
            PageTemplate(id="main", frames=[frame], onPage=self._decorate),
        ])

    def afterFlowable(self, flowable):
        toc = getattr(flowable, "toc_text", None)
        if toc is not None:
            self.records["toc"].append((getattr(flowable, "toc_level", 0), toc, self.page))
        cap = getattr(flowable, "caption_text", None)
        if cap is not None:
            self.records[getattr(flowable, "caption_kind", "fig")].append((cap, self.page))

    def _decorate(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.setFont(ITAL, 8.5)
        canvas.setFillColor(GREY)
        canvas.drawString(2.5 * cm, A4[1] - 1.55 * cm, "Video-Based Vehicle Counting System")
        canvas.drawRightString(A4[0] - 2.5 * cm, A4[1] - 1.55 * cm, "Project Report")
        canvas.line(2.5 * cm, A4[1] - 1.75 * cm, A4[0] - 2.5 * cm, A4[1] - 1.75 * cm)
        canvas.line(2.5 * cm, 1.85 * cm, A4[0] - 2.5 * cm, 1.85 * cm)
        canvas.drawString(
            2.5 * cm, 1.35 * cm,
            "School of Computer Science and Engineering, KIIT, BBSR",
        )
        canvas.setFont(BASE, 9)
        canvas.drawRightString(A4[0] - 2.5 * cm, 1.35 * cm, str(doc.page))
        canvas.restoreState()
