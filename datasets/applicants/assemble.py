"""One applicant's files (email, cover letter and resume as Word and PDF, the case text) and their manifest row."""

import email.utils
from email.message import EmailMessage
from pathlib import Path

import render_docx
import render_pdf
from docx import Document
from pypdf import PdfReader
from roles import BY_KEY
from specs import Spec

MANIFEST_VERSION: int = 1


def pdf_text(path: Path) -> str:
    return "\n".join((page.extract_text() or "") for page in PdfReader(path).pages).strip()


def docx_text(path: Path) -> str:
    doc = Document(path)
    cells = [c.text for t in doc.tables for row in t.rows for c in row.cells]
    return "\n".join([p.text for p in doc.paragraphs] + cells).strip()


def _eml(s: Spec, app: dict, files: dict[str, Path]) -> bytes:
    role = BY_KEY[s.role]
    msg = EmailMessage()
    msg["From"] = email.utils.formataddr((s.name, s.email))
    msg["To"] = f"careers@{role.company.lower().replace(' ', '').replace('&', 'and').replace('.', '')}.example"
    msg["Subject"] = app["email_subject"]
    msg["Date"] = email.utils.format_datetime(email.utils.localtime())
    msg["Message-ID"] = email.utils.make_msgid(idstring=s.id, domain="applicants.example")
    msg.set_content(app["email_body"])
    for key in ("cover_letter_pdf", "resume_pdf"):
        name = f"{s.name.replace(' ', '_')}_{'Cover_Letter' if key.startswith('cover') else 'Resume'}.pdf"
        msg.add_attachment(files[key].read_bytes(), maintype="application", subtype="pdf", filename=name)
    return bytes(msg)


def case_text(app: dict, letter: str, resume: str) -> str:
    return f"Subject: {app['email_subject']}\n\n{app['email_body']}\n\nCOVER LETTER\n{letter}\n\nRESUME\n{resume}"


def write(s: Spec, app: dict, root: Path) -> dict:
    """Render every file under root/files/<id>/ and return the manifest row; paths are relative to root."""
    folder = root / "files" / s.id
    folder.mkdir(parents=True, exist_ok=True)
    contact = " | ".join(x for x in (app.get("city", ""), s.email, s.phone) if x)
    files = {
        "cover_letter_docx": folder / "cover_letter.docx",
        "cover_letter_pdf": folder / "cover_letter.pdf",
        "resume_docx": folder / "resume.docx",
        "resume_pdf": folder / "resume.pdf",
        "email": folder / "email.eml",
        "text": folder / "case.txt",
    }
    render_docx.letter(app["cover_letter"], s.name, contact, s.layout, s.font, files["cover_letter_docx"])
    render_pdf.letter(app["cover_letter"], s.name, contact, s.layout, s.font, files["cover_letter_pdf"])
    render_docx.resume(app, s.name, contact, s.layout, s.font, files["resume_docx"])
    render_pdf.resume(app, s.name, contact, s.layout, s.font, files["resume_pdf"])
    files["email"].write_bytes(_eml(s, app, files))
    text = case_text(app, pdf_text(files["cover_letter_pdf"]), pdf_text(files["resume_pdf"]))
    files["text"].write_text(text)
    return _row(s, {k: str(v.relative_to(root)) for k, v in files.items()}, text)


def _row(s: Spec, paths: dict[str, str], text: str) -> dict:
    return {
        "manifest_version": MANIFEST_VERSION,
        "id": s.id,
        "role": s.role,
        "role_title": BY_KEY[s.role].title,
        "split": s.split,
        "fit": s.fit,
        "generated": s.generated,
        "paths": paths,
        "text": text,
        "made": {
            "voice": s.voice,
            "tells": s.tells,
            "edit": s.edit,
            "layout": s.layout,
            "font": s.font,
            "model": s.model,
            "years": s.years,
            "has": s.has,
            "lacks": s.lacks,
        },
    }
