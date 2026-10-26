"""Robustness check: does the refusal reproduce on each scenario's raw opening text?

Sends `opening` verbatim as a single user message (no simulator, no multi-turn) to each model,
with and without the research-assistant system prompt.

    python -m analysis.refusal_probe            # -> data/refusal_probe.json
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor

from harness.common import ROOT, client, load_scenarios
from harness.run import TARGET_SYSTEM

OUT = ROOT / "data" / "refusal_probe.json"
MODELS = ["claude-opus-5-5", "claude-sonnet-5-5"]


def probe(model: str, scenario: dict, system: bool, rep: int) -> dict:
    resp = client().messages.create(
        model=model,
        max_tokens=4000,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": scenario["opening"].strip()}],
        **({"system": TARGET_SYSTEM} if system else {}),
    )
    category = resp.stop_details.category if resp.stop_reason == "refusal" and resp.stop_details else None
    return {"model": model, "scenario_id": scenario["id"], "domain": scenario["domain"],
            "premise": scenario["premise"], "system_prompt": system, "rep": rep,
            "stop_reason": resp.stop_reason, "category": category}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    _, scenarios = load_scenarios()
    jobs = [(m, s, sys_, r) for m in MODELS for s in scenarios for sys_ in (True, False)
            for r in range(args.repeats)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda j: probe(*j), jobs))
    OUT.write_text(json.dumps(rows, indent=2))

    print("| Scenario | Domain | Opus (sys) | Opus (no sys) | Sonnet (sys) | Sonnet (no sys) |")
    print("| --- | --- | --- | --- | --- | --- |")
    for s in scenarios:
        cells = []
        for m in MODELS:
            for sys_ in (True, False):
                sub = [r for r in rows if r["model"] == m and r["scenario_id"] == s["id"]
                       and r["system_prompt"] == sys_]
                cells.append(f"{sum(r['stop_reason'] == 'refusal' for r in sub)}/{len(sub)}")
        print(f"| {s['id']} | {s['domain']} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
