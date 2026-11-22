"""PDF renderings of the resume and cover letter, in the same four layouts, with reportlab's built-in fonts."""

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, ListFlowable, Paragraph, SimpleDocTemplate, Spacer, Table
from styles import PDF_BOLD, PDF_FONT

SIZE: dict[str, int] = {"classic": 11, "modern": 10, "compact": 9, "plain": 11}
ACCENT: dict[str, colors.Color] = {"modern": colors.HexColor("#1F4E79"), "compact": colors.HexColor("#404040")}


def _styles(layout: str, font: str) -> dict[str, ParagraphStyle]:
    base, bold, size = PDF_FONT[font], PDF_BOLD[PDF_FONT[font]], SIZE[layout]
    colour = ACCENT.get(layout, colors.black)
    return {
        "body": ParagraphStyle("body", fontName=base, fontSize=size, leading=size * 1.3, spaceAfter=3),
        "name": ParagraphStyle(
            "name",
            fontName=bold,
            fontSize={"classic": 18, "modern": 22, "compact": 14, "plain": 12}[layout],
            leading=26,
            alignment=1 if layout == "classic" else 0,
        ),
        "contact": ParagraphStyle("contact", fontName=base, fontSize=size, alignment=1 if layout == "classic" else 0),
        "head": ParagraphStyle(
            "head",
            fontName=base if layout == "plain" else bold,
            fontSize=size + 1,
            textColor=colour,
            spaceBefore=8,
            spaceAfter=3,
        ),
    }


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def _head(st: dict, text: str, layout: str) -> list:
    out = [_p(text.upper() if layout != "plain" else text + ":", st["head"])]
    if layout in ("classic", "modern"):
        out.append(HRFlowable(width="100%", thickness=0.6, color=ACCENT.get(layout, colors.black)))
    return out


def _top(st: dict, r: dict, name: str, contact: str) -> list:
    out = [_p(name, st["name"]), _p(contact, st["contact"])]
    if r.get("headline"):
        out.append(_p(r["headline"], st["body"]))
    return [*out, Spacer(1, 6)]


def _jobs(st: dict, jobs: list[dict], layout: str) -> list:
    out: list = []
    for j in jobs:
        out.append(_p(f"{j['title']}, {j['employer']}  {j['location']}  {j['start']} - {j['end']}", st["body"]))
        items = [_p(b, st["body"]) for b in j["bullets"]]
        if layout == "plain":
            out += [_p(f"- {b}", st["body"]) for b in j["bullets"]]
        elif items:
            out.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=12))
    return out


def _skills(st: dict, skills: list[str], layout: str) -> list:
    if layout == "compact" and skills:
        cols = 3
        rows = -(-len(skills) // cols)
        grid = [
            [_p(skills[c * rows + i], st["body"]) if c * rows + i < len(skills) else "" for c in range(cols)]
            for i in range(rows)
        ]
        return [Table(grid)]
    return [_p(", ".join(skills), st["body"])] if skills else []


def _build(path: Path, flow: list, layout: str) -> None:
    size = A4 if layout == "compact" else LETTER
    margin = 0.6 * inch if layout == "compact" else 0.9 * inch
    SimpleDocTemplate(
        str(path), pagesize=size, leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin
    ).build(flow)


def resume(r: dict, name: str, contact: str, layout: str, font: str, path: Path) -> None:
    st = _styles(layout, font)
    flow = _top(st, r, name, contact)
    if r.get("summary"):
        flow += [*_head(st, "Summary", layout), _p(r["summary"], st["body"])]
    flow += _head(st, "Experience", layout) + _jobs(st, r["experience"], layout)
    flow += _head(st, "Education", layout)
    flow += [_p(f"{e['credential']}, {e['school']} {e['year']}".strip(), st["body"]) for e in r["education"]]
    flow += _head(st, "Skills", layout) + _skills(st, r["skills"], layout)
    if r.get("extras"):
        flow += _head(st, "Additional", layout) + [_p(x, st["body"]) for x in r["extras"]]
    _build(path, flow, layout)


def letter(text: str, name: str, contact: str, layout: str, font: str, path: Path) -> None:
    st = _styles(layout, font)
    flow = _top(st, {}, name, contact) if layout != "plain" else []
    flow += [_p(p.strip(), st["body"]) for p in text.split("\n\n") if p.strip()]
    _build(path, flow, layout)
