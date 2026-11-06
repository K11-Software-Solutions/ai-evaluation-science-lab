"""Study designs: comparing systems, monitoring a judge over time, and optimising against a judge.

compare_systems   pairwise win rate of system A over B on shared prompts, with a CI,
                  judged in counterbalanced order (or, to show the danger, in a fixed order)
drift_monitor     a judge re-scores a fixed anchor set every day; detect a change in its
                  pass rate with a simple threshold or with CUSUM (Page, 1954)
best_of_n         generate n candidates per prompt and keep the one the judge likes best:
                  what happens to TRUE quality and to length (Goodhart's law)
"""
from __future__ import annotations

import random
from dataclasses import replace

from evalsci.agreement import wilson
from evalsci.raters import Rater
from evalsci.world import Prompt, Response, System, respond


def compare_systems(rater: Rater, a: list[Response], b: list[Response], seed: int = 0,
                    counterbalance: bool = True) -> tuple[float, float, float]:
    """Win rate of A over B (Wilson CI). Without counterbalancing, A is always shown first."""
    rng = random.Random(seed)
    wins = 0
    for ra, rb in zip(a, b):
        if not counterbalance or rng.random() < 0.5:
            wins += rater.prefer_first(ra, rb, rng)
        else:
            wins += not rater.prefer_first(rb, ra, rng)
    return wilson(wins, len(a))


def true_win_rate(a: list[Response], b: list[Response]) -> float:
    return sum(x.quality > y.quality for x, y in zip(a, b)) / len(a)


CALIBRATION_DAYS = 5


def drift_monitor(judge: Rater, anchors: list[Response], days: int, drift_from: int | None,
                  drift_per_day: float, seed: int = 0, threshold: float = 0.12,
                  k: float = 0.03, h: float = 0.25, step: float = 0.0) -> dict:
    """First alarm day for each method (None = no alarm). Drift starts on `drift_from`.

    Drift is change relative to the judge's OWN behaviour: the baseline is its mean pass rate on
    the anchor set over the first CALIBRATION_DAYS days. (A judge that differs from humans from
    day one is a leniency problem, caught at acceptance, not drift.) Alarms are counted only after
    calibration.
    """
    rng = random.Random(seed)
    alarms = {"threshold": None, "cusum": None}
    s_hi = s_lo = 0.0
    calibration = []
    for day in range(days):
        started = drift_from is not None and day >= drift_from
        # a ramp (gradual drift) or, with `step`, a sudden small persistent change (e.g. a model update)
        shift = (step if step else drift_per_day * (day - drift_from + 1)) if started else 0.0
        today = replace(judge, severity=judge.severity - shift)          # drifting leniency
        rate = sum(today.passes(r, rng) for r in anchors) / len(anchors)
        if day < CALIBRATION_DAYS:
            calibration.append(rate)
            continue
        d = rate - sum(calibration) / len(calibration)
        if alarms["threshold"] is None and abs(d) > threshold:
            alarms["threshold"] = day
        s_hi, s_lo = max(0.0, s_hi + d - k), max(0.0, s_lo - d - k)
        if alarms["cusum"] is None and (s_hi > h or s_lo > h):
            alarms["cusum"] = day
    return alarms


def best_of_n(system: System, prompts: list[Prompt], n: int, selector: Rater, seed: int = 0) -> dict:
    """Pick the candidate the selector judges best; report true quality and length of the picks."""
    rng = random.Random(seed)
    picked = []
    for p in prompts:
        cands = [respond(system, p, rng) for _ in range(n)]
        cands = [replace(c, length=max(20, int(c.length * rng.uniform(0.5, 1.8)))) for c in cands]   # varied length
        picked.append(max(cands, key=lambda c: selector.perceived(c, rng)))
    return {"true_quality": sum(c.quality for c in picked) / len(picked),
            "length": sum(c.length for c in picked) / len(picked),
            "judge_score": sum(selector.perceived(c, rng) for c in picked) / len(picked)}
