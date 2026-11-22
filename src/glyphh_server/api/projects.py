"""The org's projects (docs/specs/bots.md, 10): a crew of its bots, in no order, on one GitHub repo and a set of
instructions, on Glyphh cloud or one of its rrotors, each turn a pull request; the org's GitHub token the turns use.
Projects were swarms: every route also answers at its old path (/v1/swarms, /v1/swarm-runs), out of the spec. And
the bots' tool callback: a bot running on a rrotor calls its tools here, with its run's tool token."""

import uuid
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import ValidationError

from glyphh_server.api.auth import Bearer, Caller, Cfg, Conn
from glyphh_server.api.templates import Person
from glyphh_server.errors import Invalid, Unauthorized
from glyphh_server.ops.bots import remote_in, tool_calls
from glyphh_server.ops.projects import github, runs, store
from glyphh_server.ops.projects.views import (
    GitHubKeyIn,
    GitHubKeyView,
    ProjectIn,
    ProjectPatch,
    ProjectRuns,
    ProjectRunView,
    Projects,
    ProjectView,
    ReviewIn,
    TaskIn,
)

router = APIRouter(tags=["projects"])
OLD: dict[str, Any] = {"include_in_schema": False}  # a route at its old path, a swarm's


def _projects(request: Request) -> Any:
    return request.app.state.bots.projects


def _was(body: dict[str, Any], shape: type[Any]) -> Any:
    """A body as a swarm's client sends it: `rounds` (there are none now) left out, review `auto` read as `end`."""
    given = {k: v for k, v in body.items() if k != "rounds"}
    if given.get("review") == "auto":
        given["review"] = "end"
    try:
        return shape.model_validate(given)
    except ValidationError as err:
        problems = [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in err.errors()]
        raise Invalid("; ".join(problems), reason="body", problems=problems) from err


@router.get("/v1/projects", operation_id="listProjects")
async def list_projects(caller: Caller, conn: Conn) -> Projects:
    return Projects(projects=await store.listing(conn))


@router.get("/v1/swarms", **OLD)
async def list_swarms(caller: Caller, conn: Conn) -> dict[str, Any]:
    found = [p.model_dump(mode="json") for p in await store.listing(conn)]
    return {"projects": found, "swarms": found}


@router.post("/v1/projects", operation_id="createProject", status_code=201)
async def create_project(body: ProjectIn, caller: Caller, conn: Conn) -> ProjectView:
    """A project: its crew (the org's bots, in no order), repo, base branch, instructions, how turns are taken, its
    review, its safety caps, and where it runs (Glyphh cloud, or one of the org's rrotors)."""
    return await store.create(conn, caller, body)


@router.post("/v1/swarms", status_code=201, **OLD)
async def create_swarm(body: dict[str, Any], caller: Caller, conn: Conn) -> ProjectView:
    return await store.create(conn, caller, _was(body, ProjectIn))


@router.get("/v1/swarms/{slug}", **OLD)
@router.get("/v1/projects/{slug}", operation_id="getProject")
async def get_project(slug: str, caller: Caller, conn: Conn) -> ProjectView:
    return await store.one(conn, slug)


@router.patch("/v1/projects/{slug}", operation_id="updateProject")
async def update_project(slug: str, body: ProjectPatch, caller: Caller, conn: Conn) -> ProjectView:
    """What is given, changed; `runs_on` null puts it on Glyphh cloud, `orchestrator` null makes Claude its
    orchestrator, `max_spend_cents` null lifts the spend cap."""
    return await store.patch(conn, slug, body)


@router.patch("/v1/swarms/{slug}", **OLD)
async def update_swarm(slug: str, body: dict[str, Any], caller: Caller, conn: Conn) -> ProjectView:
    return await store.patch(conn, slug, _was(body, ProjectPatch))


@router.delete("/v1/swarms/{slug}", status_code=204, **OLD)
@router.delete("/v1/projects/{slug}", operation_id="deleteProject", status_code=204)
async def delete_project(slug: str, caller: Caller, conn: Conn) -> Response:
    """The project deleted, with its runs (their pull requests stay on GitHub)."""
    await store.remove(conn, slug)
    return Response(status_code=204)


@router.post("/v1/swarms/{slug}/runs", status_code=202, **OLD)
@router.post("/v1/projects/{slug}/runs", operation_id="runProject", status_code=202)
async def run_project(slug: str, body: TaskIn, request: Request, who: Person) -> ProjectRunView:
    """A run of the project, on a task or on its instructions alone: its first step sent where it runs (409 while one
    is live or its rrotor is offline; 404 github_key without the org's GitHub token; 503 anthropic_off on Glyphh
    cloud with no Anthropic key)."""
    return await _projects(request).start(who, slug, body.task)  # type: ignore[no-any-return]


@router.get("/v1/swarms/{slug}/runs", **OLD)
@router.get("/v1/projects/{slug}/runs", operation_id="listProjectRuns")
async def list_project_runs(slug: str, caller: Caller, conn: Conn) -> ProjectRuns:
    """Its runs with their turns, the newest first (the last 50)."""
    return ProjectRuns(runs=await runs.listing(conn, await store.row(conn, slug)))


@router.get("/v1/swarm-runs/{run_id}", **OLD)
@router.get("/v1/project-runs/{run_id}", operation_id="getProjectRun")
async def get_project_run(run_id: uuid.UUID, caller: Caller, conn: Conn) -> ProjectRunView:
    return await runs.get(conn, run_id)


@router.post("/v1/swarm-runs/{run_id}/answer", status_code=202, **OLD)
@router.post("/v1/project-runs/{run_id}/answer", operation_id="answerProjectRun", status_code=202)
async def answer_project_run(run_id: uuid.UUID, body: ReviewIn, request: Request, who: Person) -> ProjectRunView:
    """The pull request that waits, merged or rejected: a turn's (then the next turn), or the whole run's."""
    return await _projects(request).answer(who, run_id, body.answer)  # type: ignore[no-any-return]


@router.post("/v1/swarm-runs/{run_id}/cancel", **OLD)
@router.post("/v1/project-runs/{run_id}/cancel", operation_id="cancelProjectRun")
async def cancel_project_run(run_id: uuid.UUID, request: Request, who: Person) -> ProjectRunView:
    """The run ended; its step out stopped (an open pull request stays open)."""
    return await _projects(request).cancel(who, run_id)  # type: ignore[no-any-return]


@router.get("/v1/github-key", operation_id="getGitHubKey")
async def get_github_key(caller: Caller, conn: Conn) -> GitHubKeyView:
    return github.view(await github.get(conn))


@router.put("/v1/github-key", operation_id="setGitHubKey")
async def set_github_key(body: GitHubKeyIn, request: Request, who: Caller, conn: Conn, settings: Cfg) -> GitHubKeyView:
    """The org's GitHub token, tried with GitHub, then kept sealed: its projects commit and open pull requests with
    it."""
    return await github.put(conn, who, settings.secret_key, body.token, _projects(request).check_github)


@router.delete("/v1/github-key", operation_id="removeGitHubKey")
async def remove_github_key(caller: Caller, conn: Conn) -> GitHubKeyView:
    return await github.remove(conn, caller.org_id)


@router.post("/v1/bots/runs/{run_id}/tool", operation_id="callBotTool")
async def call_bot_tool(run_id: uuid.UUID, body: tool_calls.ToolIn, request: Request, creds: Bearer) -> dict[str, Any]:
    """A bot running on a rrotor calls one of its tools (fetch, or a connection's): bearer its run's tool token;
    answered {"result": ...} or {"error": "..."}."""
    if creds is None:
        raise Unauthorized(remote_in.BAD_TOKEN)
    return await tool_calls.call(request.app.state.bots, creds.credentials, run_id, body)
