"""PDF reports (English and Kannada) using fpdf2 + HarfBuzz text shaping.

Kannada needs proper shaping (conjuncts, vowel signs), so text shaping is
switched on and Noto Sans Kannada is registered as a fallback font next to
Noto Sans. The report content is the same Markdown the app already builds;
this module renders that small Markdown subset (headings, bullets, tables,
**bold**) and draws South Indian charts where a [[CHARTS]] marker appears.
"""
from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

FONT_DIR = Path(__file__).resolve().parent.parent / "fonts"

# Characters the bundled fonts don't have, replaced with close equivalents.
_REPLACE = {"→": "->", "◀": "<", "⏱️": "", "⏱": "", "⚠️": "", "✅": "", "🟡": "", "❌": ""}


def _clean(text: str) -> str:
    for a, b in _REPLACE.items():
        text = text.replace(a, b)
    # single-asterisk italics are not part of fpdf2's markdown: drop them
    text = re.sub(r"(?<!\*)\*(?!\*)([^*]+)(?<!\*)\*(?!\*)", r"\1", text)
    return text


class ReportPDF(FPDF):
    def __init__(self, footer_text: str = ""):
        super().__init__(format="A4")
        self.footer_text = footer_text
        for family, stem in (("NotoSans", "NotoSans"), ("NotoKn", "NotoSansKannada")):
            self.add_font(family, "", str(FONT_DIR / f"{stem}-Regular.ttf"))
            self.add_font(family, "B", str(FONT_DIR / f"{stem}-Bold.ttf"))
        self.set_fallback_fonts(["NotoKn"], exact_match=False)
        self.set_text_shaping(True)
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, margin=18)
        self.set_font("NotoSans", size=10)

    def footer(self):
        self.set_y(-12)
        self.set_font("NotoSans", size=7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, f"{self.footer_text}   ·   {self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)

    # ------------------------------------------------------------ blocks
    def heading(self, text: str, level: int) -> None:
        size = {1: 17, 2: 13, 3: 11}[level]
        self.ln(2 if level > 1 else 0)
        self.set_font("NotoSans", "B", size)
        if level == 1:
            self.set_text_color(150, 60, 20)
        self.multi_cell(0, size * 0.55, _clean(text).replace("**", ""),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        if level <= 2:
            y = self.get_y() + 0.5
            self.set_draw_color(210, 160, 120)
            self.line(self.l_margin, y, self.w - self.r_margin, y)
            self.set_draw_color(0, 0, 0)
            self.ln(2)
        self.set_font("NotoSans", size=10)

    def paragraph(self, text: str) -> None:
        self.set_font("NotoSans", size=10)
        self.multi_cell(0, 5.2, _clean(text), markdown=True,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def bullet(self, text: str, level: int = 0) -> None:
        indent = 4 + level * 5
        self.set_font("NotoSans", size=9.5)
        self.set_x(self.l_margin + indent)
        self.cell(4, 5, "•")
        self.multi_cell(0, 5, _clean(text), markdown=True,
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def md_table(self, rows: list[str]) -> None:
        cells = [[_clean(c.strip()) for c in r.strip().strip("|").split("|")]
                 for r in rows if not re.fullmatch(r"\|?[\s:\-|]+\|?", r.strip())]
        if not cells:
            return
        n = max(len(r) for r in cells)
        cells = [r + [""] * (n - len(r)) for r in cells]
        self.set_font("NotoSans", size=8.5)
        self.ln(1)
        with self.table(text_align="LEFT", markdown=True, line_height=4.6,
                        first_row_as_headings=True, padding=1.2,
                        headings_style=_heading_style(), borders_layout="HORIZONTAL_LINES") as table:
            for r in cells:
                row = table.row()
                for c in r:
                    row.cell(c)
        self.ln(2)
        self.set_font("NotoSans", size=10)

    # ------------------------------------------------------------ charts
    def south_chart(self, x: float, y: float, size: float, contents: dict[int, list[str]],
                    lagna_sign: int, labels: list[str], title: str, subtitle: str) -> None:
        from .charts import SIGN_CELL
        c = size / 4
        self.set_line_width(0.2)
        self.set_draw_color(120, 120, 120)
        for sign, (r, col) in SIGN_CELL.items():
            cx, cy = x + col * c, y + r * c
            self.rect(cx, cy, c, c)
            if sign == lagna_sign:
                self.set_draw_color(200, 110, 30)
                self.set_line_width(0.6)
                self.line(cx, cy + 6, cx + 6, cy)
                self.set_line_width(0.2)
                self.set_draw_color(120, 120, 120)
            self.set_font("NotoSans", size=5.5)
            self.set_text_color(120, 120, 120)
            self.set_xy(cx + 0.5, cy + 0.6)
            self.cell(c - 1.2, 2.6, labels[sign], align="R")
            self.set_text_color(0, 0, 0)
            items = contents.get(sign, [])
            if items:
                self.set_font("NotoSans", "B", 8)
                self.set_xy(cx + 1, cy + 4)
                self.multi_cell(c - 2, 3.6, "  ".join(items), align="L")
        self.set_line_width(0.5)
        self.rect(x, y, size, size)
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        self.set_font("NotoSans", "B", 10)
        self.set_xy(x + c, y + size / 2 - 5)
        self.cell(2 * c, 5, title, align="C")
        self.set_font("NotoSans", size=7.5)
        self.set_xy(x + c, y + size / 2 + 0.5)
        self.cell(2 * c, 4, subtitle, align="C")
        self.set_font("NotoSans", size=10)


def _heading_style():
    from fpdf.fonts import FontFace
    return FontFace(emphasis="BOLD", fill_color=(245, 230, 215))


def render(md: str, footer_text: str, charts: list[tuple] | None = None,
           chart_labels: list[str] | None = None, chart_subtitle: str = "") -> bytes:
    """charts: [(title, contents, lagna_sign), ...] drawn at the [[CHARTS]] marker."""
    pdf = ReportPDF(footer_text)
    pdf.add_page()
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("|"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i])
                i += 1
            pdf.md_table(block)
            continue
        s = line.strip()
        if s == "[[CHARTS]]" and charts:
            size = 84
            if pdf.get_y() + size + 4 > pdf.h - pdf.b_margin:
                pdf.add_page()
            y = pdf.get_y() + 2
            for k, (title, contents, lagna) in enumerate(charts[:2]):
                pdf.south_chart(pdf.l_margin + k * (size + 12), y, size, contents,
                                lagna, chart_labels or [str(n) for n in range(12)],
                                title, chart_subtitle)
            pdf.set_xy(pdf.l_margin, y + size + 4)
        elif line.startswith("### "):
            pdf.heading(line[4:], 3)
        elif line.startswith("## "):
            pdf.heading(line[3:], 2)
        elif line.startswith("# "):
            pdf.heading(line[2:], 1)
        elif line.startswith("  - "):
            pdf.bullet(line[4:], 1)
        elif line.startswith("- "):
            pdf.bullet(line[2:], 0)
        elif s == "---":
            pdf.ln(2)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.set_draw_color(0, 0, 0)
            pdf.ln(2)
        elif not s:
            pdf.ln(1.5)
        else:
            pdf.paragraph(line)
        i += 1
    return bytes(pdf.output())
