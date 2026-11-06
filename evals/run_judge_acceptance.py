"""The judge acceptance test: a judge must pass every check before it is used as an evaluator.

Usage (from the repo root):

    python -m evals.run_judge_acceptance                      # the "fair" judge: must pass
    JUDGE=position-biased python -m evals.run_judge_acceptance   # a biased judge: must FAIL

Checks (thresholds in evals/thresholds.json):
  agreement       judge alpha with the human consensus, at most `max_alpha_shortfall` below
                  the humans' own alpha with the same consensus
  leniency        |judge pass rate - human pass rate| within `max_pass_rate_gap`
  consistency     the same verdict when the pair order is swapped, at least `min_consistency`
  position        the 95% interval of the first-position win rate contains 0.5
  verbosity       the 95% interval of the longer-response win rate (equal quality) contains 0.5
  self-preference the 95% interval of the own-family gap does not lie above 0
  drift           no CUSUM alarm on a 100-item anchor set over a simulated month, against the
                  judge's own first five days (the "drifting" judge's leniency starts changing
                  on day 10)

Writes evals/results/judge_report.md and .json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

from evalsci.battery import run_battery
from evalsci.raters import JUDGES, judge
from evalsci.studies import drift_monitor
from evalsci.world import responses

HERE = Path(__file__).parent
ALL_JUDGES = {**JUDGES, "drifting": judge("drifting")}
DRIFTING_FROM, DRIFT_PER_DAY, DAYS = 10, 0.03, 30


def drift_check(name: str, j, seed: int = 0) -> dict:
    world = responses(n_prompts=100, seed=seed + 7)
    anchors = [r for rs in world.values() for r in rs][:100]
    drift_from = DRIFTING_FROM if name == "drifting" else None
    return drift_monitor(j, anchors, DAYS, drift_from, DRIFT_PER_DAY, seed=seed)


def check(report: dict, t: dict) -> list[str]:
    a, p, v, s = report["agreement"], report["position"], report["verbosity"], report["self_preference"]
    out = []
    shortfall = a["human_alpha"][0] - a["judge_alpha"][0]
    if shortfall > t["max_alpha_shortfall"]:
        out.append(f"agreement: judge alpha {a['judge_alpha'][0]:.2f} is {shortfall:.2f} below the human ceiling {a['human_alpha'][0]:.2f}")
    if abs(a["pass_rate_gap"]) > t["max_pass_rate_gap"]:
        out.append(f"leniency: pass rate differs from humans by {a['pass_rate_gap']:+.2f}")
    if p["consistency"][0] < t["min_consistency"]:
        out.append(f"consistency: {p['consistency'][0]:.2f} < {t['min_consistency']}")
    lo, hi = p["first_position_win_rate"][1:]
    if not lo <= 0.5 <= hi:
        out.append(f"position bias: first-shown response wins {p['first_position_win_rate'][0]:.2f} (95% CI {lo:.2f}-{hi:.2f})")
    lo, hi = v["longer_wins"][1:]
    if not lo <= 0.5 <= hi:
        out.append(f"verbosity bias: longer response wins {v['longer_wins'][0]:.2f} of equal-quality pairs (95% CI {lo:.2f}-{hi:.2f})")
    if s["own_family_gap"][1] > 0:
        out.append(f"self-preference: own-family gap {s['own_family_gap'][0]:+.2f} (95% CI {s['own_family_gap'][1]:+.2f} to {s['own_family_gap'][2]:+.2f})")
    if report["drift"]["cusum"] is not None:
        out.append(f"drift: CUSUM alarm on day {report['drift']['cusum']} of {DAYS}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-gate", action="store_true")
    parser.add_argument("--out", type=Path, default=HERE / "results")
    args = parser.parse_args(argv)
    name = os.environ.get("JUDGE", "fair")
    if name not in ALL_JUDGES:
        raise SystemExit(f"unknown JUDGE '{name}'; choose from {', '.join(ALL_JUDGES)}")
    j = ALL_JUDGES[name]
    thresholds = json.loads((HERE / "thresholds.json").read_text(encoding="utf-8"))
    report = run_battery(j if name != "drifting" else replace(j, name="drifting"))
    report["drift"] = drift_check(name, j)
    failures = check(report, thresholds)

    a, p, v, s = report["agreement"], report["position"], report["verbosity"], report["self_preference"]
    ci = lambda x: f"{x[0]:.2f} ({x[1]:.2f}-{x[2]:.2f})"
    L = [f"# Judge acceptance report: `{name}`", "", "| Check | Result (95% CI) | Requirement |", "|---|---|---|",
         f"| Agreement with human consensus (alpha) | {ci(a['judge_alpha'])} | within {thresholds['max_alpha_shortfall']} of humans: {ci(a['human_alpha'])} |",
         f"| Pass rate minus human pass rate | {a['pass_rate_gap']:+.2f} | within ±{thresholds['max_pass_rate_gap']} |",
         f"| Same verdict when order is swapped | {ci(p['consistency'])} | at least {thresholds['min_consistency']} |",
         f"| First-shown response wins | {ci(p['first_position_win_rate'])} | interval contains 0.50 |",
         f"| Longer response wins (equal quality) | {ci(v['longer_wins'])} | interval contains 0.50 |",
         f"| Own-family win rate minus humans' | {s['own_family_gap'][0]:+.2f} ({s['own_family_gap'][1]:+.2f} to {s['own_family_gap'][2]:+.2f}) | interval not above 0 |",
         f"| Drift on the anchor set over {DAYS} days | CUSUM alarm: {report['drift']['cusum'] if report['drift']['cusum'] is not None else 'none'} | no alarm |",
         "", "## Gate", "", "PASSED" if not failures else "FAILED:\n" + "\n".join(f"- {f}" for f in failures), ""]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "judge_report.md").write_text("\n".join(L), encoding="utf-8")
    (args.out / "judge_report.json").write_text(json.dumps({"judge": name, "report": report, "gate_failures": failures},
                                                          indent=2), encoding="utf-8")
    print("\n".join(L))
    if failures and not args.no_gate:
        print("Judge acceptance FAILED", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
