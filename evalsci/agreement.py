"""Agreement and reliability statistics, with bootstrap confidence intervals.

- percent agreement: easy to read, ignores chance
- Cohen's kappa: two raters, corrects for chance; suffers the "kappa paradox" when one
  category is rare (high agreement, low kappa), because chance agreement is then high
- weighted kappa (quadratic): two raters, ordinal scores, near misses get partial credit
- Krippendorff's alpha: any number of raters, missing ratings allowed, nominal, ordinal
  or interval data. The most general of the four, and the one to use for rating panels
  (Krippendorff, 2004; Hayes & Krippendorff, 2007).
"""
from __future__ import annotations

import random
from collections import Counter
from typing import Callable, Sequence


def percent_agreement(a: Sequence, b: Sequence) -> float:
    return sum(x == y for x, y in zip(a, b)) / len(a)


def cohen_kappa(a: Sequence, b: Sequence) -> float:
    n = len(a)
    labels = set(a) | set(b)
    po = percent_agreement(a, b)
    pe = sum((list(a).count(c) / n) * (list(b).count(c) / n) for c in labels)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def weighted_kappa(a: Sequence[int], b: Sequence[int], categories: Sequence[int] = (1, 2, 3, 4, 5)) -> float:
    n, k = len(a), len(categories)
    idx = {c: i for i, c in enumerate(categories)}
    w = [[(i - j) ** 2 / (k - 1) ** 2 for j in range(k)] for i in range(k)]
    pa = [sum(idx[x] == i for x in a) / n for i in range(k)]
    pb = [sum(idx[x] == i for x in b) / n for i in range(k)]
    observed = sum(w[idx[x]][idx[y]] for x, y in zip(a, b)) / n
    expected = sum(w[i][j] * pa[i] * pb[j] for i in range(k) for j in range(k))
    return 1.0 if expected == 0 else 1 - observed / expected


def krippendorff_alpha(units: Sequence[Sequence], level: str = "ordinal") -> float:
    """units: one list per item, holding each rater's value (None = not rated)."""
    o: Counter = Counter()
    for unit in units:
        vals = [v for v in unit if v is not None]
        m = len(vals)
        if m < 2:
            continue
        for i, c in enumerate(vals):
            for j, k in enumerate(vals):
                if i != j:
                    o[(c, k)] += 1 / (m - 1)
    values = sorted({c for c, _ in o})
    n_c = {c: sum(o[(c, k)] for k in values) for c in values}
    n = sum(n_c.values())
    if n <= 1 or len(values) < 2:
        return 1.0

    def delta(c, k) -> float:
        if c == k:
            return 0.0
        if level == "nominal":
            return 1.0
        if level == "interval":
            return float((c - k) ** 2)
        lo, hi = min(c, k), max(c, k)                     # ordinal
        between = sum(n_c[g] for g in values if lo <= g <= hi)
        return (between - (n_c[c] + n_c[k]) / 2) ** 2

    d_o = sum(o[(c, k)] * delta(c, k) for c in values for k in values) / n
    d_e = sum(n_c[c] * n_c[k] * delta(c, k) for c in values for k in values) / (n * (n - 1))
    return 1.0 if d_e == 0 else 1 - d_o / d_e


def bootstrap_ci(units: Sequence, stat: Callable[[Sequence], float], n_boot: int = 300,
                 seed: int = 0, level: float = 0.95) -> tuple[float, float, float]:
    """Point estimate and percentile CI, resampling ITEMS (the usual source of uncertainty)."""
    rng = random.Random(seed)
    point = stat(units)
    sims = sorted(stat([rng.choice(units) for _ in units]) for _ in range(n_boot))
    return point, sims[int((1 - level) / 2 * n_boot)], sims[int((1 + level) / 2 * n_boot) - 1]


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Proportion with a Wilson score interval: well-behaved near 0 and 1 and for small n."""
    if n == 0:
        return float("nan"), 0.0, 1.0
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return p, centre - half, centre + half
