"""A part of a bot template's package (ops/bots/packages.py) read and checked: its skills (skills/<name>/SKILL.md)."""

import re

IN_SKILL: re.Pattern[str] = re.compile(r"skills/([^/]+)/(.+)")
FRONT: re.Pattern[str] = re.compile(r"\A---\n(.*?)\n---(\n|\Z)", re.S)


def skills(texts: dict[str, str], problems: list[str]) -> list[str]:
    """The package's skills by name: each folder under skills/ holds a SKILL.md whose frontmatter names it."""
    names = sorted({m.group(1) for p in texts if (m := IN_SKILL.fullmatch(p))})
    for name in names:
        path = f"skills/{name}/SKILL.md"
        if path not in texts:
            problems.append(f"The skill {name} has no SKILL.md.")
            continue
        front = FRONT.match(texts[path])
        said = dict(re.findall(r"^([\w-]+):[ \t]*(\S.*)$", front.group(1) if front else "", re.M))
        if not said.get("name") or not said.get("description"):
            problems.append(f"{path} needs a name and a description in its frontmatter.")
        elif said["name"].strip() != name:
            problems.append(f"{path} names itself {said['name'].strip()}: a skill is named as its folder, {name}.")
    return names
