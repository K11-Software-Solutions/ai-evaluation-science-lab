"""The judge acceptance battery: tests an LLM judge must pass before it is trusted.

Each test isolates one property, using pairs or items designed so that only that
property can explain the result:

1. Agreement   judge vs the human consensus (Krippendorff's alpha, ordinal), next to
               the agreement among the humans themselves (the ceiling).
2. Leniency    judge pass rate minus human pass rate on the same responses.
3. Position    every pair judged in BOTH orders: how often the verdict survives the
               swap, and how often the first-shown response wins.
4. Verbosity   pairs identical in quality, different only in length: how often the
               longer one wins. A fair judge: about half.
5. Self-preference  pairs of an own-family and another-family response: the judge's
               own-family win rate minus the humans' win rate on the same pairs.

With real data the "identical in quality" pairs come from controlled rewrites (padding
an answer without adding content); here the simulator builds them exactly.
"""
from __future__ import annotations

import random
from dataclasses import replace

from evalsci.agreement import bootstrap_ci, krippendorff_alpha, wilson
from evalsci.raters import HUMANS, Rater
from evalsci.world import Response, responses


def _median(xs):
    s = sorted(xs)
    return s[len(s) // 2]


def agreement(judge: Rater, items: list[Response], seed: int = 0) -> dict:
    """Compare like with like: every rater, human or judge, against the consensus of two OTHER humans.

    Comparing a judge with the median of three humans, but each human with the other
    individuals, flatters the judge: a consensus is less noisy than any one person.
    """
    rng = random.Random(seed)
    human_scores = [[h.score(r, rng) for h in HUMANS] for r in items]
    judge_scores = [judge.score(r, rng) for r in items]

    def others(row, i):              # consensus of the two humans other than i (rounded mean)
        rest = [s for k, s in enumerate(row) if k != i]
        return round(sum(rest) / len(rest) + 1e-9)

    # rows: (rater score, reference score) for each of the three leave-one-out references
    judge_rows = [[judge_scores[n], others(row, i)] for n, row in enumerate(human_scores) for i in range(3)]
    human_rows = [[row[i], others(row, i)] for row in human_scores for i in range(3)]
    a = bootstrap_ci(judge_rows, krippendorff_alpha, seed=seed)
    ceiling = bootstrap_ci(human_rows, krippendorff_alpha, seed=seed)
    consensus = [_median(s) for s in human_scores]
    human_pass = sum(c >= 4 for c in consensus) / len(items)
    judge_pass = sum(j >= 4 for j in judge_scores) / len(items)
    return {"judge_alpha": a, "human_alpha": ceiling, "pass_rate_gap": judge_pass - human_pass}


def position(judge: Rater, pairs: list[tuple[Response, Response]], seed: int = 0) -> dict:
    rng = random.Random(seed)
    consistent = first_wins = 0
    for a, b in pairs:
        ab = judge.prefer_first(a, b, rng)         # True: a wins
        ba = judge.prefer_first(b, a, rng)         # True: b wins
        consistent += ab != ba                     # same winner both ways
        first_wins += ab + ba
    n = len(pairs)
    return {"consistency": wilson(consistent, n), "first_position_win_rate": wilson(first_wins, 2 * n)}


def verbosity(judge: Rater, items: list[Response], seed: int = 0) -> dict:
    rng = random.Random(seed)
    wins = 0
    for r in items:
        short, long_ = replace(r, length=150), replace(r, length=450)    # same quality, 3x the length
        if rng.random() < 0.5:
            wins += judge.prefer_first(long_, short, rng)
        else:
            wins += not judge.prefer_first(short, long_, rng)
    return {"longer_wins": wilson(wins, len(items))}


def self_preference(judge: Rater, pairs: list[tuple[Response, Response]], seed: int = 0) -> dict:
    """pairs: (own-family response, other-family response)."""
    rng = random.Random(seed)

    def own_wins(rater: Rater, own: Response, other: Response) -> int:
        if rng.random() < 0.5:                                  # counterbalanced order
            return int(rater.prefer_first(own, other, rng))
        return int(not rater.prefer_first(other, own, rng))

    j = [own_wins(judge, own, other) for own, other in pairs]
    h = [int(sum(own_wins(hr, own, other) for hr in HUMANS) >= 2) for own, other in pairs]   # panel majority
    units = list(zip(j, h))
    gap = bootstrap_ci(units, lambda u: sum(a for a, _ in u) / len(u) - sum(b for _, b in u) / len(u), seed=seed)
    return {"own_family_gap": gap}


def run_battery(judge: Rater, n: int = 300, seed: int = 0, own_family: str = "family-x") -> dict:
    world = responses(n_prompts=n, seed=seed)
    systems = list(world)
    rng = random.Random(seed)
    items = [world[rng.choice(systems)][i] for i in range(n)]
    pairs = [(world[a][i], world[b][i]) for i in range(n) for a, b in [rng.sample(systems, 2)]]
    family = judge.family or own_family
    own = [r for name in systems for r in world[name] if r.family == family]
    other = [r for name in systems for r in world[name] if r.family != family]
    by_prompt_other = {r.prompt: r for r in other}
    fam_pairs = [(r, by_prompt_other[r.prompt]) for r in own if r.prompt in by_prompt_other][:n]
    return {"agreement": agreement(judge, items, seed), "position": position(judge, pairs, seed),
            "verbosity": verbosity(judge, items, seed), "self_preference": self_preference(judge, fam_pairs, seed)}
