"""Word renderings of the resume and cover letter, in four layouts and the spec's font."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

ACCENT: dict[str, RGBColor] = {"modern": RGBColor(0x1F, 0x4E, 0x79), "compact": RGBColor(0x40, 0x40, 0x40)}
SIZE: dict[str, int] = {"classic": 11, "modern": 10, "compact": 9, "plain": 11}


def _doc(font: str, layout: str) -> Document:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = font
    style.font.size = Pt(SIZE[layout])
    return doc


def _heading(doc: Document, text: str, layout: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text.upper() if layout != "plain" else text + ":")
    run.bold = layout != "plain"
    run.font.size = Pt(SIZE[layout] + (2 if layout == "modern" else 1))
    if layout in ACCENT:
        run.font.color.rgb = ACCENT[layout]


def _top(doc: Document, r: dict, name: str, contact: str, layout: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(name)
    run.bold = True
    run.font.size = Pt({"classic": 18, "modern": 22, "compact": 14, "plain": 12}[layout])
    if layout == "classic":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = doc.add_paragraph(contact)
    if layout == "classic":
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if r.get("headline"):
        doc.add_paragraph(r["headline"]).runs[0].italic = layout != "plain"


def _jobs(doc: Document, jobs: list[dict], layout: str) -> None:
    for j in jobs:
        p = doc.add_paragraph()
        p.add_run(f"{j['title']}, {j['employer']}").bold = layout != "plain"
        p.add_run(f"  {j['location']}  {j['start']} - {j['end']}")
        for b in j["bullets"]:
            if layout == "plain":
                doc.add_paragraph(f"- {b}")
            else:
                doc.add_paragraph(b, style="List Bullet")


def _skills(doc: Document, r: dict, layout: str) -> None:
    if layout == "compact" and r["skills"]:
        cols = 3
        rows = -(-len(r["skills"]) // cols)
        table = doc.add_table(rows=rows, cols=cols)
        for i, s in enumerate(r["skills"]):
            table.cell(i % rows, i // rows).text = s
    elif r["skills"]:
        doc.add_paragraph(", ".join(r["skills"]))


def resume(r: dict, name: str, contact: str, layout: str, font: str, path: Path) -> None:
    doc = _doc(font, layout)
    _top(doc, r, name, contact, layout)
    if r.get("summary"):
        _heading(doc, "Summary", layout)
        doc.add_paragraph(r["summary"])
    _heading(doc, "Experience", layout)
    _jobs(doc, r["experience"], layout)
    _heading(doc, "Education", layout)
    for e in r["education"]:
        doc.add_paragraph(f"{e['credential']}, {e['school']} {e['year']}".strip())
    _heading(doc, "Skills", layout)
    _skills(doc, r, layout)
    if r.get("extras"):
        _heading(doc, "Additional", layout)
        for x in r["extras"]:
            doc.add_paragraph(x)
    doc.save(path)


def letter(text: str, name: str, contact: str, layout: str, font: str, path: Path) -> None:
    doc = _doc(font, layout)
    if layout != "plain":
        _top(doc, {}, name, contact, layout)
    for para in [p.strip() for p in text.split("\n\n") if p.strip()]:
        doc.add_paragraph(para)
    doc.save(path)
