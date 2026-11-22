"""The protocol's integrity checks and baselines over a rendered corpus.

uv run datasets/applicants/build.py ... render, then:
uv run --with python-docx --with pypdf python datasets/applicants/check.py --out datasets/applicants/out
"""

import argparse
import email
import json
import random
from collections import Counter
from pathlib import Path

import baseline
from assemble import docx_text, pdf_text
from docx import Document
from pypdf import PdfReader

FILES: tuple[str, ...] = ("cover_letter_docx", "cover_letter_pdf", "resume_docx", "resume_pdf", "email")


def opens(root: Path, rows: list[dict]) -> Counter:
    failed: Counter = Counter()
    for r in rows:
        for key in FILES:
            path = root / r["paths"][key]
            try:
                if key.endswith("docx"):
                    Document(path)
                elif key.endswith("pdf"):
                    assert len(PdfReader(path).pages) >= 1
                else:
                    msg = email.message_from_bytes(path.read_bytes())
                    assert msg["From"] and len(list(msg.iter_attachments())) == 2
            except Exception:  # noqa: BLE001 - any failure to open is the finding
                failed[key] += 1
    return failed


def spot(root: Path, rows: list[dict], apps: dict[str, dict], k: int = 20) -> list[str]:
    """Parse k applicants back from Word and PDF; the name and first job title must survive in each."""
    bad = []
    for r in random.Random(5).sample(rows, k):
        app = apps[r["id"]]
        name = app["_name"]
        title = app["experience"][0]["title"] if app["experience"] else ""
        for key in ("resume_docx", "resume_pdf"):
            path = root / r["paths"][key]
            text = docx_text(path) if key.endswith("docx") else pdf_text(path)
            flat = " ".join(text.split())
            if name not in flat or " ".join(title.split()) not in flat:
                bad.append(f"{r['id']}:{key}")
    return bad


def report(out: Path) -> dict:
    import build
    import specs

    root = out / "corpus"
    rows = [json.loads(line) for line in (root / "manifest.jsonl").read_text().splitlines()]
    cache: dict = {}
    every = {s.id: s for s in specs.build(build.PER_CELL, build.MODELS)}
    apps = {r["id"]: {**build.final(every[r["id"]], out, cache), "_name": every[r["id"]].name} for r in rows}
    train, test = [r for r in rows if r["split"] == "train"], [r for r in rows if r["split"] == "test"]
    return {
        "applicants": len(rows),
        "counts": Counter(f"{r['split']}/{r['fit']}/{r['generated']}" for r in rows),
        "by_generated": Counter(f"{r['split']}/{r['generated']}" for r in rows),
        "by_fit": Counter(f"{r['split']}/{r['fit']}" for r in rows),
        "failed_to_open": opens(root, rows),
        "spot_check_failures": spot(root, rows, apps),
        "baseline_generated": baseline.single_feature(train, test, "generated", ("some", "mostly", "fully")),
        "baseline_fit": baseline.single_feature(train, test, "fit", ("strong", "borderline", "poor")),
        "probe_lexical": baseline.probe(train, test),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("datasets/applicants/out"))
    args = ap.parse_args()
    result = report(args.out)
    (args.out / "corpus" / "checks.json").write_text(json.dumps(result, indent=2, default=dict))
    print(json.dumps(result, indent=2, default=dict))


if __name__ == "__main__":
    main()
