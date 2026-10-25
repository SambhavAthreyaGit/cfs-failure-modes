"""Claude Science arm: the simulator writes each persona turn, you paste it into Claude Science,
then paste Claude Science's reply back here. Saves the same transcript format as the API arm.

    python -m harness.relay --scenario <id>

Paste the reply, then type END on its own line and press Enter.
Type REFUSED on its own line if Claude Science declined to answer.
"""

import argparse
import sys

from harness.common import client, load_scenarios, new_record, save_session, simulate_user_turn, turn_plan


def read_paste() -> str:
    lines = []
    for line in sys.stdin:
        if line.strip() in ("END", "REFUSED"):
            return "[REFUSAL]" if line.strip() == "REFUSED" else "\n".join(lines).strip()
        lines.append(line.rstrip("\n"))
    return "\n".join(lines).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    personas, scenarios = load_scenarios()
    scenario = next(s for s in scenarios if s["id"] == args.scenario)
    c = client()
    record = new_record(scenario, "claude_science", args.seed, "Claude Science (desktop app)")
    record["app_version"] = input("Claude Science version (Help > About), then Enter: ").strip()

    plan = turn_plan(scenario)
    for turn_idx in range(len(plan)):
        user_text = simulate_user_turn(c, personas[scenario["persona"]], scenario,
                                       record["turns"], turn_idx)
        record["turns"].append({"role": "user", "text": user_text})
        print("\n" + "=" * 70 + f"\nTURN {turn_idx + 1}/{len(plan)}: paste this into Claude Science:\n")
        print(user_text)
        print("\n" + "-" * 70 + "\nNow paste Claude Science's full reply, then END on its own line:")
        reply = read_paste()
        record["turns"].append({"role": "assistant", "text": reply})
        if reply == "[REFUSAL]":
            record["refused"] = True
            break
        save_session(record)  # save after every turn so nothing is lost

    save_session(record)
    print(f"\nSaved {record['session_id']}. Also export the session log from Claude Science "
          f"into data/claude_science_logs/ if you can.")


if __name__ == "__main__":
    main()
