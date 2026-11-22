"""The applicant specs: who each fictional applicant is, how well they fit, and how their application was made.

Every label comes from here, before any model writes a word: fit from the facts we hand the writer, generated
from the pipeline the applicant goes through. Seeded, so the same run makes the same specs.
"""

import random
from dataclasses import asdict, dataclass

from roles import ROLES, Role
from styles import EDITS, FIRST, LAST, LAYOUTS, TELLS, VOICES

FITS: tuple[str, ...] = ("strong", "borderline", "poor")
GENERATED: tuple[str, ...] = ("some", "mostly", "fully")
TEST_SHARE: float = 0.2
SECOND_MODEL_SHARE: float = 0.3  # the share written by the larger model, drawn independently of every label


@dataclass
class Spec:
    id: str
    role: str
    fit: str
    generated: str
    split: str
    name: str
    email: str
    phone: str
    years: int
    has: list[str]
    lacks: list[str]
    background: str
    voice: str  # how the person writes on their own (the draft for some/mostly)
    tells: str  # how strongly the AI-written text shows it (mostly/fully)
    edit: str  # what the light AI edit touched (some)
    layout: str
    font: str
    model: str

    def row(self) -> dict:
        return asdict(self)


def _facts(role: Role, fit: str, rng: random.Random) -> tuple[int, list[str], list[str], str]:
    lo, hi = role.years
    if fit == "strong":
        has = list(role.must) + rng.sample(list(role.nice), 2)
        return rng.randint(lo, hi), has, [], f"{role.title} or the same job under another title"
    if fit == "borderline":
        keep = rng.randint(2, 3)
        has = rng.sample(list(role.must), keep) + rng.sample(list(role.nice), 1)
        lacks = [m for m in role.must if m not in has]
        return max(0, lo - rng.randint(1, 2)), has, lacks, role.adjacent
    other = rng.choice([r for r in ROLES if r.key != role.key])
    has = rng.sample(list(other.must), 3) + rng.sample(list(role.must), rng.randint(0, 1))
    lacks = [m for m in role.must if m not in has]
    return rng.randint(1, 8), has, lacks, f"{other.title}, a different field, now applying out of field"


def _person(rng: random.Random) -> tuple[str, str, str]:
    first, last = rng.choice(FIRST), rng.choice(LAST)
    handle = rng.choice([f"{first}.{last}", f"{first[0]}{last}", f"{first}{last}{rng.randint(1, 99)}"]).lower()
    domain = rng.choice(["gmail.com", "outlook.com", "yahoo.com", "icloud.com", "proton.me"])
    phone = f"({rng.randint(201, 989)}) {rng.randint(200, 999)}-{rng.randint(1000, 9999)}"
    return f"{first} {last}", f"{handle}@{domain}", phone


def _spec(n: int, role: Role, fit: str, generated: str, split: str, rng: random.Random, models: list[str]) -> Spec:
    years, has, lacks, background = _facts(role, fit, rng)
    name, email, phone = _person(rng)
    layout, font = rng.choice(LAYOUTS)
    return Spec(
        id=f"a{n:05d}",
        role=role.key,
        fit=fit,
        generated=generated,
        split=split,
        name=name,
        email=email,
        phone=phone,
        years=years,
        has=has,
        lacks=lacks,
        background=background,
        voice=rng.choice(VOICES),
        tells=rng.choice(TELLS) if generated != "some" else "",
        edit=rng.choice(EDITS) if generated == "some" else "",
        layout=layout,
        font=font,
        model=models[1] if rng.random() < SECOND_MODEL_SHARE else models[0],
    )


def build(per_cell: int, models: list[str], seed: int = 7) -> list[Spec]:
    """per_cell applicants for every (role, fit, generated) cell; the test split is stratified by cell."""
    rng = random.Random(seed)
    specs: list[Spec] = []
    n_test = max(1, round(per_cell * TEST_SHARE))
    for role in ROLES:
        for fit in FITS:
            for generated in GENERATED:
                test = set(rng.sample(range(per_cell), n_test))
                for i in range(per_cell):
                    split = "test" if i in test else "train"
                    specs.append(_spec(len(specs), role, fit, generated, split, rng, models))
    return specs


def pilot(specs: list[Spec], k: int = 20, seed: int = 11) -> list[Spec]:
    """A small spread over every role, fit and generated class for costing the run."""
    rng = random.Random(seed)
    firsts: dict[tuple[str, str, str], Spec] = {}
    for s in specs:
        firsts.setdefault((s.role, s.fit, s.generated), s)
    by_class = {g: [s for s in firsts.values() if s.generated == g] for g in GENERATED}
    for group in by_class.values():
        rng.shuffle(group)
    return [by_class[GENERATED[i % 3]][i // 3] for i in range(k)]  # the classes in turn
