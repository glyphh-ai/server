"""Past cases a gate starts from (docs/specs/bots.md, 9): a gate's `seed_from` names a seed set Glyphh ships
(library/seeds/<name>.json, generated and labelled), recorded as its first precedents when its Ada model is made, so
it decides from day one and the person's answers and corrections build on them. A set's applicants are made into
items by the same code a run uses (ops/bots/applicants.py), and each gate's case is filled from an item as its loop
fills it; an applicant is a precedent of each gate its `labels` names."""

import json
import re
from functools import cache
from pathlib import Path
from typing import Any

from glyphh.bots.runner import fill

from glyphh_server.errors import Invalid
from glyphh_server.ops.bots import applicants

SEEDS: Path = Path(__file__).with_name("library") / "seeds"
NAME: re.Pattern[str] = re.compile(r"[a-z][a-z0-9-]{0,40}")


def shipped(name: Any) -> bool:
    return isinstance(name, str) and NAME.fullmatch(name) is not None and (SEEDS / f"{name}.json").exists()


def named(spec: dict[str, Any]) -> None:
    """Each gate's `seed_from` is a set Glyphh ships, or Invalid says which is not."""
    gates = spec.get("gates") if isinstance(spec.get("gates"), dict) else {}
    asked = {n: g["seed_from"] for n, g in gates.items() if isinstance(g, dict) and "seed_from" in g}
    bad = [f"{n}: {s}" for n, s in asked.items() if not shipped(s)]
    if bad:
        raise Invalid(f"A gate's seed_from names a seed set Glyphh ships: {', '.join(bad)} is not one.", reason="spec")


@cache
def items(name: str) -> tuple[tuple[dict[str, Any], dict[str, str]], ...]:
    """The set's applicants as items, each with its labels (those the sender checks refuse are left out)."""
    out = []
    for a in json.loads((SEEDS / f"{name}.json").read_text("utf-8"))["applicants"]:
        got, _ = applicants.item(a["id"], a["from"], a["subject"], a["auth"], a["bulk"], a["body"], a["resume"],
                                 a["resume_kind"])  # fmt: skip
        if got is not None:
            out.append((got, a["labels"]))
    return tuple(out)


def cases(gate: dict[str, Any], name: str) -> list[dict[str, Any]]:
    """The gate's seed precedents: each item's case, its label for this gate (`name`) the outcome."""
    return [{"data": fill(gate["case"], {"item": item}), "outcome": labels[name]}
            for item, labels in items(gate["seed_from"]) if name in labels]  # fmt: skip


def plant(runner: Any, made: list[str]) -> dict[str, int]:
    """The seed sets of the gates whose models were just made, recorded in them: {gate: precedents}."""
    planted = {}
    for name, gate in runner.bot.gates.items():
        model = runner.bot.gate_model(name)
        if gate.get("seed_from") and model in made:
            got = cases(gate, name)
            runner.ada.model(model).record_many(got)
            planted[name] = len(got)
    return planted
