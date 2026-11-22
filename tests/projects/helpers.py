"""Projects under test: a crew of two bots and the org's GitHub token saved; GitHub's API for one repo faked in memory
(FakeRepo, in place of ops/projects/repo.py's Repo), and Claude with tools faked by a script of replies (FakeClaude,
in place of ops/projects/claude.py's Claude)."""

import uuid
from types import SimpleNamespace
from typing import Any

import httpx
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncEngine

from glyphh_server.errors import Invalid, Unavailable
from glyphh_server.models import Bot
from tests.bots.conftest import Served, made_bot
from tests.bots.remote import OnRrotor, online
from tests.db.helpers import Person, person
from tests.link import Rt

FINE: dict[str, Any] = {"loop": [{"id": "a", "agent": "Hi"}]}
REPO: str = "https://github.com/acme/site"
TOKEN: str = "github_pat_" + "x" * 30


class FakeRepo:
    """One repo on GitHub: its branches' files, its pull requests, and what was asked of it. `fail` names a call
    GitHub refuses."""

    def __init__(self) -> None:
        self.files: dict[str, dict[str, str]] = {"main": {"README.md": "# Site\n", "docs/a.md": "one\ntwo\n"}}
        self.pulls: dict[int, dict[str, Any]] = {}
        self.asked: list[tuple[Any, ...]] = []
        self.mergeable, self.fail, self.first = True, "", 0  # `first`: that many of the call go through before

    def _did(self, call: str, *args: Any) -> None:
        self.asked.append((call, *args))
        if self.fail == call:
            self.first -= 1
        if self.fail == call and self.first < 0:
            raise Unavailable(f"GitHub did not {call} (500)", reason="github")

    async def head(self, branch: str) -> str:
        self._did("head", branch)
        return f"at:{branch}"

    async def tree(self, sha: str) -> list[str]:
        return sorted(self.files[sha[3:]])

    async def read(self, path: str, ref: str) -> str | None:
        return self.files[ref[3:]].get(path)

    async def branch(self, name: str, sha: str) -> None:
        self._did("branch", name)
        self.files[name] = dict(self.files[sha[3:]])

    async def commit(self, branch: str, parent: str, changes: dict[str, str | None], message: str, by: str) -> str:
        self._did("commit", branch, message, by)
        for path, text in changes.items():
            if text is None:
                del self.files[branch][path]
            else:
                self.files[branch][path] = text
        return f"c-{branch}"

    async def open(self, head: str, base: str, title: str, body: str) -> dict[str, Any]:
        self._did("open", head, base, title)
        n = len(self.pulls) + 1
        self.pulls[n] = {"head": head, "base": base, "title": title, "body": body, "state": "open"}
        return {"url": f"{REPO}/pull/{n}", "number": n}

    async def merge(self, number: int, title: str) -> tuple[bool, str]:
        self._did("merge", number)
        if not self.mergeable:
            return False, "Pull Request is not mergeable"
        pull = self.pulls[number]
        pull["state"] = "merged"
        self.files[pull["base"]] = dict(self.files[pull["head"]])
        return True, "m" * 40

    async def close(self, number: int) -> None:
        self._did("close", number)
        self.pulls[number]["state"] = "closed"

    async def drop(self, branch: str) -> None:
        self._did("drop", branch)
        self.files.pop(branch, None)


def use(name: str, **given: Any) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=f"tu_{uuid.uuid4().hex[:6]}", name=name, input=given)


def say(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


class FakeClaude:
    """Claude with tools: each request answered by the next of `script` (a list of blocks, or an error to raise);
    every request is remembered."""

    def __init__(self) -> None:
        self.script: list[Any] = []
        self.asked: list[dict[str, Any]] = []
        self.keys: list[tuple[str, str]] = []

    def then(self, *replies: Any) -> None:
        self.script += [r if isinstance(r, list | Exception) else [r] for r in replies]

    async def create(self, system: str, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        self.asked.append({"system": system, "messages": list(messages), "tools": [t["name"] for t in tools]})
        reply = self.script.pop(0)
        if isinstance(reply, Exception):
            raise reply
        usage = SimpleNamespace(input_tokens=1000, output_tokens=200)
        return SimpleNamespace(content=[SimpleNamespace(type="thinking"), *reply], usage=usage)

    def results(self) -> list[str]:
        """What the tools answered Claude, in order, in the last request's conversation."""
        turns = [
            m["content"] for m in self.asked[-1]["messages"] if m["role"] == "user" and isinstance(m["content"], list)
        ]
        return [r["content"] for answers in turns for r in answers]


def faked(s: Served) -> tuple[FakeRepo, FakeClaude]:
    """The projects service's GitHub and Claude, faked; and a token tried by a fake GitHub."""
    projects = s.app.state.bots.projects
    repo, claude = FakeRepo(), FakeClaude()

    async def check(token: str) -> str:
        if token.endswith("bad"):
            raise Invalid("GitHub does not take that token.", reason="token")
        return "acme-bot"

    def claude_for(key: str, model: str) -> FakeClaude:
        claude.keys.append((key, model))
        return claude

    projects.check_github, projects.repo_for, projects.claude_for = check, lambda token, name: repo, claude_for
    return repo, claude


async def crew(s: Served, engine: AsyncEngine, key: bool = True) -> tuple[Person, list[dict[str, Any]]]:
    ada = await person(engine)
    bots = [await made_bot(s, ada, name=n, spec=FINE, summary=f"{n} work") for n in ("Ada Cat", "Bo Cat")]
    async with engine.begin() as conn:
        await conn.execute(update(Bot).where(Bot.slug == "ada-cat").values(look={"head": "Round", "eye": "Wide"}))
    if key:
        res = await s.http.put("/v1/github-key", json={"token": TOKEN}, headers=ada.headers)
        assert res.status_code == 200 and res.json()["login"] == "acme-bot" and res.json()["hint"] == "xxxx"
    return ada, bots


async def crew_on_rrotor(r: OnRrotor, engine: AsyncEngine, key: bool = True) -> tuple[Person, Rt, list[dict[str, Any]]]:
    """A crew whose project runs on a rrotor of the org's, linked now."""
    faked(r.s)
    ada, bots = await crew(r.s, engine, key)
    return ada, await online(engine, ada), bots


def body(bots: list[dict[str, Any]], **over: Any) -> dict[str, Any]:
    return {"name": "Site crew", "repo_url": REPO, "members": [b["id"] for b in bots], **over}


async def project(s: Served, who: Person, bots: list[dict[str, Any]], **over: Any) -> dict[str, Any]:
    res = await s.http.post("/v1/projects", json=body(bots, **over), headers=who.headers)
    assert res.status_code == 201, res.text
    return dict(res.json())


async def start(s: Served, who: Person, task: str = "Make the home page") -> httpx.Response:
    return await s.http.post("/v1/projects/site-crew/runs", json={"task": task}, headers=who.headers)


async def run_of(s: Served, who: Person, run_id: Any) -> dict[str, Any]:
    await s.app.state.bots.projects.wait()
    return dict((await s.http.get(f"/v1/project-runs/{run_id}", headers=who.headers)).json())


async def answer(s: Served, who: Person, run_id: Any, said: str) -> httpx.Response:
    return await s.http.post(f"/v1/project-runs/{run_id}/answer", json={"answer": said}, headers=who.headers)


def turned(status: str = "open", said: str = "Wrote the page.", n: int = 7, **over: Any) -> dict[str, Any]:
    """glyphh_swarm's `turn` result."""
    data = {"status": status, "said": said, "title": f"turn {n}", "files": [{"path": "a.html", "added": 3}]}
    data |= {"usage": {"input_tokens": 1000, "output_tokens": 100}, **over}
    if status == "open":
        data |= {"pr_url": f"{REPO}/pull/{n}", "number": n, "head_sha": "abc"}
    return {"status": "done", "data": data, "step": None, "prompt": None}


def picked(answer: str) -> dict[str, Any]:
    """glyphh_swarm's `pick` result."""
    data = {"status": "picked", "answer": answer, "usage": {"input_tokens": 500, "output_tokens": 50}}
    return {"status": "done", "data": data}
