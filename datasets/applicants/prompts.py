"""The prompts and the output shape for each stage of the pipeline.

some:   draft in the person's own voice, then a light AI edit of one part.
mostly: draft in the person's own voice, then a full AI rewrite that keeps the facts.
fully:  the AI writes the whole application from the facts alone.
"""

import json

from roles import BY_KEY
from specs import Spec

SYSTEM: str = (
    "You write fictional job applications for a labelled training corpus that teaches a screening tool. "
    "Every person, employer and school you name is invented. Follow the brief exactly: never give the applicant "
    "a skill or credential the brief says they lack, and keep their years of experience as given. "
    "Answer with the JSON object only."
)

_JOB = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "employer": {"type": "string"},
        "location": {"type": "string"},
        "start": {"type": "string"},
        "end": {"type": "string"},
        "bullets": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "employer", "location", "start", "end", "bullets"],
    "additionalProperties": False,
}
_SCHOOL = {
    "type": "object",
    "properties": {"credential": {"type": "string"}, "school": {"type": "string"}, "year": {"type": "string"}},
    "required": ["credential", "school", "year"],
    "additionalProperties": False,
}
SCHEMA: dict = {
    "type": "object",
    "properties": {
        "email_subject": {"type": "string"},
        "email_body": {"type": "string"},
        "cover_letter": {"type": "string", "description": "the letter, paragraphs separated by blank lines"},
        "city": {"type": "string"},
        "headline": {"type": "string"},
        "summary": {"type": "string"},
        "experience": {"type": "array", "items": _JOB},
        "education": {"type": "array", "items": _SCHOOL},
        "skills": {"type": "array", "items": {"type": "string"}},
        "extras": {"type": "array", "items": {"type": "string"}, "description": "certifications, languages, etc."},
    },
    "required": [
        "email_subject",
        "email_body",
        "cover_letter",
        "city",
        "headline",
        "summary",
        "experience",
        "education",
        "skills",
        "extras",
    ],
    "additionalProperties": False,
}
PARTS: str = "an application email, a cover letter and a resume (headline, summary, jobs, education, skills, extras)"


def brief(s: Spec) -> str:
    role = BY_KEY[s.role]
    lacks = ", ".join(s.lacks) if s.lacks else "nothing the posting requires"
    return (
        f"The posting: {role.posting()}\n\nThe applicant: {s.name}, {s.email}, {s.phone}. "
        f"{s.years} years of work experience; background: {s.background}. "
        f"They have: {', '.join(s.has)}. They lack: {lacks}. "
        "Leave headline, summary or extras empty if this person would not write one."
    )


def draft(s: Spec) -> str:
    return (
        f"{brief(s)}\n\nWrite {PARTS} exactly as this person would write them alone, with no editor and no AI "
        f"help. Their writing: {s.voice}. Keep their quirks and slips; do not polish. Avoid the stock phrases "
        "of AI-written applications (thrilled, proven track record, leverage, passionate, em dashes)."
    )


def fully(s: Spec) -> str:
    return (
        f"{brief(s)}\n\nAs an AI assistant asked by this applicant to write the whole application for them from "
        f"the facts above, write {PARTS}. Style: {s.tells}."
    )


def edit(s: Spec, first: dict) -> str:
    return (
        f"{brief(s)}\n\nHere is the application the applicant wrote themselves, as JSON:\n{json.dumps(first)}\n\n"
        f"They asked an AI assistant for a light touch: {s.edit}. Return the whole application as JSON; every "
        "part the edit does not cover must be returned exactly as it was, slips and all."
    )


def rewrite(s: Spec, first: dict) -> str:
    return (
        f"{brief(s)}\n\nHere is the application the applicant wrote themselves, as JSON:\n{json.dumps(first)}\n\n"
        "They asked an AI assistant to rewrite all of it to make it stronger, keeping their facts, jobs, dates "
        f"and schools. Rewrite every part. Style: {s.tells}."
    )


def first_stage(s: Spec) -> str:
    return fully(s) if s.generated == "fully" else draft(s)


def second_stage(s: Spec, first: dict) -> str | None:
    if s.generated == "fully":
        return None
    return edit(s, first) if s.generated == "some" else rewrite(s, first)
