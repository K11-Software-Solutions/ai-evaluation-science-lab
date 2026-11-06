"""Experiments behind the articles' findings.

    python -m experiments.run_experiments          # about a minute; writes experiments/results/

E1  The kappa paradox: two equally accurate raters, different prevalence.
E2  Biased judges change system rankings; counterbalancing removes position bias but nothing
    removes verbosity bias or self-preference except fixing the judge.
E3  Sample sizes: how wide is the interval on a judge's agreement, and how many prompts does it
    take to tell two systems apart?
E4  Drift: a fixed threshold against CUSUM, for gradual drift and for small sudden shifts.
E5  Goodhart: best-of-n selection with a fair judge and with a length-biased one.
"""
from __future__ import annotations

import json
import random
import sys
from itertools import combinations
from pathlib import Path

from evalsci.agreement import cohen_kappa, krippendorff_alpha, percent_agreement
from evalsci.battery import agreement
from evalsci.raters import JUDGES, judge
from evalsci.studies import best_of_n, compare_systems, drift_monitor, true_win_rate
from evalsci.world import DEFAULT_SYSTEMS, prompts, responses

OUT = Path(__file__).parent / "results"


def mean(xs):
    return sum(xs) / len(xs)


def e1_kappa_paradox(n: int = 4000) -> dict:
    rows = []
    for prevalence in (0.5, 0.2, 0.05):
        rng = random.Random(int(prevalence * 100))
        truth = [rng.random() < prevalence for _ in range(n)]
        a = [t if rng.random() < 0.9 else not t for t in truth]       # each rater right 90% of the time
        b = [t if rng.random() < 0.9 else not t for t in truth]
        both_pos = sum(x and y for x, y in zip(a, b))
        both_neg = sum(not x and not y for x, y in zip(a, b))
        disagree = n - both_pos - both_neg
        rows.append({"prevalence_of_fail": prevalence, "rater_accuracy": 0.9,
                     "percent_agreement": round(percent_agreement(a, b), 3),
                     "cohen_kappa": round(cohen_kappa(a, b), 3),
                     "krippendorff_alpha": round(krippendorff_alpha([[x, y] for x, y in zip(a, b)], "nominal"), 3),
                     "agreement_on_fails": round(2 * both_pos / (2 * both_pos + disagree), 3),
                     "agreement_on_passes": round(2 * both_neg / (2 * both_neg + disagree), 3)})
    return {"items": n, "rows": rows}


def ranking(scores: dict[str, float]) -> list[str]:
    return sorted(scores, key=lambda s: -scores[s])


def e2_rankings(n: int = 400, seed: int = 0) -> dict:
    world = responses(n_prompts=n, seed=seed)
    names = [s.name for s in DEFAULT_SYSTEMS]
    truth = {s: sum(true_win_rate(world[s], world[o]) for o in names if o != s) for s in names}
    setups = [("fair, counterbalanced", JUDGES["fair"], True),
              ("position-biased, fixed order", JUDGES["position-biased"], False),
              ("position-biased, counterbalanced", JUDGES["position-biased"], True),
              ("verbose-loving, counterbalanced", JUDGES["verbose-loving"], True),
              ("self-preferring (family-x), counterbalanced", JUDGES["self-preferring"], True)]
    rows = []
    for label, j, cb in setups:
        wins = {s: 0.0 for s in names}
        for i, (a, b) in enumerate(combinations(names, 2)):
            # Fixed order shows the lower-listed system (the "candidate") first, as when a new model's
            # answer always sits in slot A. Counterbalanced: random order per pair.
            w = 1 - compare_systems(j, world[b], world[a], seed=seed + i, counterbalance=cb)[0]
            wins[a] += w
            wins[b] += 1 - w
        rows.append({"judge": label, "ranking": " > ".join(ranking(wins)),
                     "matches_truth": ranking(wins) == ranking(truth),
                     "delta_win_share": round(wins["delta"] / 3, 2), "gamma_win_share": round(wins["gamma"] / 3, 2)})
    return {"true_ranking": " > ".join(ranking(truth)), "systems": {s.name: {"skill": s.skill, "family": s.family,
            "verbosity": s.verbosity} for s in DEFAULT_SYSTEMS}, "rows": rows}


def e3_sample_sizes(trials: int = 30) -> dict:
    widths = []
    for n in (24, 50, 100, 200, 400):
        w = []
        for t in range(trials // 3):
            world = responses(n_prompts=n, seed=100 + t)
            items = [world[s][i] for i, s in zip(range(n), ["alpha", "beta", "gamma", "delta"] * n)]
            _, lo, hi = agreement(JUDGES["fair"], items, seed=t)["judge_alpha"]
            w.append(hi - lo)
        widths.append({"items": n, "alpha_ci_width": round(mean(w), 3)})
    power = []
    for n in (25, 50, 100, 200, 400):
        row = {"prompts": n}
        for label, j in (("fair_judge", JUDGES["fair"]), ("noisy_judge", JUDGES["noisy"])):
            hits = 0
            for t in range(trials):
                world = responses(n_prompts=n, seed=200 + t)
                _, lo, hi = compare_systems(j, world["beta"], world["gamma"], seed=t)
                hits += lo > 0.5                                    # beta (skill 0.2) beats gamma (0.0)
            row[f"{label}_detects_beta_over_gamma"] = round(hits / trials, 2)
        power.append(row)
    return {"trials": trials, "alpha_interval": widths, "system_comparison_power": power}


def e4_drift(seeds: int = 200) -> dict:
    rows = []
    for label, kw in (("none (false alarms)", {"drift_from": None, "drift_per_day": 0.0}),
                      ("gradual: +0.03 leniency/day from day 10", {"drift_from": 10, "drift_per_day": 0.03}),
                      ("sudden: +0.10 on day 10", {"drift_from": 10, "drift_per_day": 0.0, "step": 0.10}),
                      ("sudden: +0.15 on day 10", {"drift_from": 10, "drift_per_day": 0.0, "step": 0.15}),
                      ("sudden: +0.20 on day 10", {"drift_from": 10, "drift_per_day": 0.0, "step": 0.20})):
        found = {"threshold": [], "cusum": []}
        early = {"threshold": 0, "cusum": 0}
        for seed in range(seeds):
            world = responses(n_prompts=100, seed=seed + 7)
            anchors = [r for rs in world.values() for r in rs][:100]
            a = drift_monitor(judge("fair"), anchors, 40, seed=seed, **kw)
            for m in found:
                if a[m] is None:
                    continue
                if kw["drift_from"] is None or a[m] < kw["drift_from"]:
                    early[m] += 1
                else:
                    found[m].append(a[m] - kw["drift_from"])
        row = {"change": label}
        for m in ("threshold", "cusum"):
            row[f"{m}_false_alarms"] = round(early[m] / seeds, 3)          # alarms before any change
            row[f"{m}_detected"] = round(len(found[m]) / seeds, 2) if kw["drift_from"] is not None else "-"
            row[f"{m}_mean_days"] = round(mean(found[m]), 1) if found[m] else "-"
        rows.append(row)
    return {"seeds": seeds, "days": 40, "anchor_items": 100, "rows": rows}


def e5_goodhart(n_prompts: int = 400) -> dict:
    gamma = next(s for s in DEFAULT_SYSTEMS if s.name == "gamma")
    ps = prompts(n_prompts, seed=9)
    rows = []
    for label, selector in (("fair judge", JUDGES["fair"]), ("verbose-loving judge", JUDGES["verbose-loving"])):
        for n in (1, 2, 4, 8, 16):
            r = best_of_n(gamma, ps, n, selector, seed=n)
            rows.append({"selector": label, "candidates": n, "true_quality": round(r["true_quality"], 3),
                         "judge_score": round(r["judge_score"], 3), "length_tokens": round(r["length"])})
    return {"prompts": n_prompts, "rows": rows}


def table(rows: list[dict]) -> list[str]:
    cols = list(rows[0])
    return ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + \
           ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]


def main() -> int:
    res = {"E1": e1_kappa_paradox(), "E2": e2_rankings(), "E3": e3_sample_sizes(), "E4": e4_drift(), "E5": e5_goodhart()}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "experiments.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    L = ["# Experiment results", "", "Generated by `python -m experiments.run_experiments`. Deterministic: rerunning gives the same numbers.", "",
         f"## E1. The kappa paradox ({res['E1']['items']} items; both raters 90% accurate)", ""] + table(res["E1"]["rows"])
    L += ["", f"## E2. Biased judges and system rankings (true ranking: {res['E2']['true_ranking']})", ""] + table(res["E2"]["rows"])
    L += ["", f"## E3a. Width of the 95% interval on a judge's agreement (alpha), by number of items", ""] + table(res["E3"]["alpha_interval"])
    L += ["", f"## E3b. Share of {res['E3']['trials']} trials where the 95% interval shows beta beats gamma (true skill gap 0.2)", ""] + table(res["E3"]["system_comparison_power"])
    L += ["", f"## E4. Drift detection on a {res['E4']['anchor_items']}-item anchor set ({res['E4']['seeds']} seeds, {res['E4']['days']} days, 5-day calibration)", ""] + table(res["E4"]["rows"])
    L += ["", f"## E5. Best-of-n selection ({res['E5']['prompts']} prompts, system gamma)", ""] + table(res["E5"]["rows"])
    (OUT / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
