"""Message Batches calls with a spend ledger: every batch is costed from its usage, and the cap is checked first."""

import json
import time
from pathlib import Path

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from dotenv import dotenv_values
from prompts import SCHEMA, SYSTEM

PRICE: dict[str, tuple[float, float]] = {  # dollars per million tokens (input, output), standard rate
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
}
BATCH_DISCOUNT: float = 0.5
MAX_TOKENS: int = 8000
CAP_DOLLARS: float = 60.0


def client(env_file: Path) -> anthropic.Anthropic:
    env = dotenv_values(env_file)
    key = env.get("GLYPHH_ANTHROPIC_API_KEY") or env.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit(f"no Anthropic key in {env_file}")
    return anthropic.Anthropic(api_key=key, max_retries=4)


def cost(model: str, usage: dict) -> float:
    pin, pout = PRICE[model]
    return BATCH_DISCOUNT * (usage["input_tokens"] * pin + usage["output_tokens"] * pout) / 1e6


def spent(ledger: Path) -> float:
    if not ledger.exists():
        return 0.0
    rows = [json.loads(line) for line in ledger.read_text().splitlines() if line]
    return sum({r["batch"]: r["dollars"] for r in rows}.values())  # a batch counted once, however often read


def guard(ledger: Path, projected: float) -> None:
    if spent(ledger) + projected > CAP_DOLLARS:
        raise SystemExit(f"cap: spent ${spent(ledger):.2f} + projected ${projected:.2f} > ${CAP_DOLLARS:.0f}")


def request(custom_id: str, model: str, prompt: str) -> Request:
    return Request(
        custom_id=custom_id,
        params=MessageCreateParamsNonStreaming(
            model=model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        ),
    )


def run(api: anthropic.Anthropic, reqs: list[Request], state: Path, label: str) -> str:
    """Submit once (the batch id is kept in state, so a rerun resumes), then wait until it ends."""
    state.parent.mkdir(parents=True, exist_ok=True)
    if state.exists():
        batch_id = state.read_text().strip()
    else:
        batch_id = api.messages.batches.create(requests=reqs).id
        state.write_text(batch_id)
    while (b := api.messages.batches.retrieve(batch_id)).processing_status != "ended":
        c = b.request_counts
        print(f"{label}: {c.succeeded} done, {c.processing} processing, {c.errored} errored", flush=True)
        time.sleep(30)
    return batch_id


def collect(api: anthropic.Anthropic, batch_id: str, models: dict[str, str], ledger: Path, label: str) -> dict:
    """The parsed JSON per custom_id; failures are left out and counted. The batch's cost goes in the ledger."""
    out: dict[str, dict] = {}
    dollars, failed = 0.0, 0
    for r in api.messages.batches.results(batch_id):
        if r.result.type != "succeeded":
            failed += 1
            continue
        msg = r.result.message
        usage = {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens}
        dollars += cost(models[r.custom_id], usage)
        text = next((b.text for b in msg.content if b.type == "text"), "")
        try:
            out[r.custom_id] = json.loads(text) if msg.stop_reason == "end_turn" else None
        except json.JSONDecodeError:
            out[r.custom_id] = None
        failed += out[r.custom_id] is None
    out = {k: v for k, v in out.items() if v is not None}
    with ledger.open("a") as f:
        f.write(
            json.dumps(
                {"label": label, "batch": batch_id, "ok": len(out), "failed": failed, "dollars": round(dollars, 4)}
            )
            + "\n"
        )
    return out
