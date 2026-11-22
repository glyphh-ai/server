# /// script
# requires-python = ">=3.12"
# dependencies = ["anthropic>=0.75", "python-dotenv", "python-docx", "reportlab", "pypdf", "boto3"]
# ///
"""Build the applicant corpus: specs, the two batch stages, the renderings and the manifest.

    uv run datasets/applicants/build.py pilot --env ../server/.env   # 20 applicants, prices the run
    uv run datasets/applicants/build.py run --env ../server/.env     # the rest, under the cap
    uv run datasets/applicants/build.py render                        # files + manifest.jsonl in --out

Stage outputs are kept in --out by applicant id, so every step resumes and the pilot's applicants are reused.
"""

import argparse
import json
from pathlib import Path

import assemble
import llm
import prompts
import specs

MODELS: list[str] = ["claude-haiku-5-5", "claude-sonnet-5-5"]
PER_CELL: int = 27  # 10 roles x 3 fits x 3 generated x 27 = 2,430 applicants


def _load(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    return {r["id"]: r["app"] for r in map(json.loads, path.read_text().splitlines())}


def _save(path: Path, rows: dict[str, dict]) -> None:
    with path.open("a") as f:
        for k, v in rows.items():
            f.write(json.dumps({"id": k, "app": v}) + "\n")


def _stage(api, todo: list[specs.Spec], n: int, out: Path, label: str, prompt) -> None:
    """Run one stage for the specs it still lacks; prompt(spec) gives the text, or None to skip the spec."""
    path = out / f"stage{n}.jsonl"
    done = _load(path)
    reqs, models = [], {}
    for s in todo:
        text = prompt(s)
        if s.id not in done and text is not None:
            reqs.append(llm.request(s.id, s.model, text))
            models[s.id] = s.model
    if not reqs:
        return
    batch = llm.run(api, reqs, out / "batches" / f"{label}-stage{n}", f"{label} stage {n}")
    _save(path, llm.collect(api, batch, models, out / "spend.jsonl", f"{label}-stage{n}"))


def generate(api, todo: list[specs.Spec], out: Path, label: str) -> None:
    _stage(api, todo, 1, out, label, prompts.first_stage)
    first = _load(out / "stage1.jsonl")
    _stage(api, todo, 2, out, label, lambda s: prompts.second_stage(s, first[s.id]) if s.id in first else None)


def final(s: specs.Spec, out: Path, cache: dict) -> dict | None:
    if not cache:
        cache.update({1: _load(out / "stage1.jsonl"), 2: _load(out / "stage2.jsonl")})
    return cache[1].get(s.id) if s.generated == "fully" else cache[2].get(s.id)


def cmd_pilot(args, every: list[specs.Spec]) -> None:
    todo = specs.pilot(every)
    generate(llm.client(args.env), todo, args.out, "pilot")
    per = llm.spent(args.out / "spend.jsonl") / len(todo)
    print(
        f"pilot: {len(todo)} applicants, ${per * len(todo):.3f}, ${per:.4f} each; "
        f"projected for {len(every)}: ${per * len(every):.2f} (cap ${llm.CAP_DOLLARS:.0f})"
    )
    (args.out / "pilot.json").write_text(json.dumps({"ids": [s.id for s in todo], "per_applicant": per}))


def cmd_run(args, every: list[specs.Spec]) -> None:
    per = json.loads((args.out / "pilot.json").read_text())["per_applicant"]
    have = _load(args.out / "stage1.jsonl")
    todo = [s for s in every if s.id not in have or final(s, args.out, {}) is None]
    llm.guard(args.out / "spend.jsonl", per * len(todo) * 1.25)  # a quarter of headroom over the pilot's rate
    generate(llm.client(args.env), todo, args.out, args.label)
    print(f"spent ${llm.spent(args.out / 'spend.jsonl'):.2f} in all")


def cmd_render(args, every: list[specs.Spec]) -> None:
    cache: dict = {}
    rows, missing = [], 0
    for s in every:
        app = final(s, args.out, cache)
        if app is None:
            missing += 1
            continue
        rows.append(assemble.write(s, app, args.out / "corpus"))
    with (args.out / "corpus" / "manifest.jsonl").open("w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    print(f"rendered {len(rows)} applicants, {missing} without a finished application")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["pilot", "run", "render"])
    ap.add_argument("--env", type=Path, default=Path(".env"), help="the server's .env, read for the API key")
    ap.add_argument("--out", type=Path, default=Path("datasets/applicants/out"))
    ap.add_argument("--label", default="run", help="names the run's batches, so a retry starts new ones")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    every = specs.build(PER_CELL, MODELS)
    {"pilot": cmd_pilot, "run": cmd_run, "render": cmd_render}[args.command](args, every)


if __name__ == "__main__":
    main()
