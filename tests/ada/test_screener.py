"""The Resume Screener's gates on real Ada (the kernel, through Ada Cloud's API and its worker): each gate's model made
from the template's spec, four fifths of its seed set recorded, the other fifth decided as new applicants, and a
verdict corrected and learned. Its bars are the template's promise that the seed set teaches its gates something:
they are what Ada scores from these precedents alone, before any person's answer."""

from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine

from glyphh_ada.process import Worker
from glyphh_server.ops.bots import seeds, templates
from tests.ada.conftest import an_org

BARS: dict[str, float] = {"source": 0.9, "fit": 0.75, "made": 0.7}


def _split(name: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    gate = templates.one("resume-screener").spec["gates"][name]
    cases = seeds.cases(gate, name)
    return gate, [c for i, c in enumerate(cases) if i % 5], [c for i, c in enumerate(cases) if not i % 5]


async def _decide(ada: httpx.AsyncClient, key: dict[str, str], name: str, case: dict[str, Any]) -> dict[str, Any]:
    got = await ada.post(f"/v1/models/{name}/decide", json={"data": case["data"]}, headers=key)
    assert got.status_code == 200, got.text
    return dict(got.json())


async def _scored(ada: httpx.AsyncClient, key: dict[str, str], name: str) -> tuple[float, list[Any]]:
    gate, known, new = _split(name)
    made = await ada.post("/v1/models", json={"name": name, "spec": gate["spec"]}, headers=key)
    assert made.status_code == 201, made.text
    done = await ada.post(f"/v1/models/{name}/record_many", json={"cases": known}, headers=key)
    assert done.status_code == 200 and done.json()["added"] == len(known), done.text
    calls = [(c, await _decide(ada, key, name, c)) for c in new]
    right = sum(1 for c, d in calls if d["outcome"] == c["outcome"])
    return right / len(new), [(c, d) for c, d in calls if d["outcome"] != c["outcome"]]


async def test_the_seed_set_teaches_each_gate_and_a_correction_is_learned(
    engine: AsyncEngine, ada: httpx.AsyncClient, worker: Worker
) -> None:
    _, key = await an_org(engine, ada)
    scores, misses = {}, {}
    for name in BARS:
        scores[name], misses[name] = await _scored(ada, key, name)
    assert all(scores[n] >= bar for n, bar in BARS.items()), scores
    case, said = misses["fit"][0]  # an applicant Ada called wrong, corrected as the person would
    assert said["outcome"] != case["outcome"]
    fixed = await ada.post("/v1/models/fit/record", json=case, headers=key)
    assert fixed.status_code == 200, fixed.text
    assert (await _decide(ada, key, "fit", case))["outcome"] == case["outcome"]
