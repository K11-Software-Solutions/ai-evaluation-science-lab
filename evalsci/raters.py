"""Evaluators with known properties: human raters and LLM judges.

Two kinds of judgement:

- pointwise: a score from 1 to 5 for one response (or pass/fail at a threshold)
- pairwise:  which of two responses is better, A or B

Human raters have a severity (harsh or lenient) and noise. LLM judges have the same,
plus the biases documented for LLM-as-judge (Zheng et al., 2023):

- position_bias   extra pull towards whichever response is shown FIRST, in pairwise judging
- verbosity_bias  extra credit per 100 tokens of length, regardless of quality
- self_preference extra credit for responses from the judge's own model family
- drift           leniency that changes over time (per "day"), e.g. after a silent model update

All parameters are in quality units, so a bias of 0.2 is directly comparable to the
0.1-0.5 differences between the systems in the world.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from evalsci.world import Response

THRESHOLDS = (-1.0, -0.3, 0.3, 1.0)        # quality cut points for scores 1|2|3|4|5


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


@dataclass
class Rater:
    name: str
    severity: float = 0.0          # > 0 harsher
    noise: float = 0.35
    position_bias: float = 0.0
    verbosity_bias: float = 0.0    # per 100 tokens above 200
    self_preference: float = 0.0
    family: str = ""
    drift_per_day: float = 0.0
    day: int = 0

    def perceived(self, r: Response, rng: random.Random) -> float:
        q = r.quality - self.severity + self.drift_per_day * self.day + rng.gauss(0, self.noise)
        q += self.verbosity_bias * (r.length - 200) / 100
        if self.family and r.family == self.family:
            q += self.self_preference
        return q

    def score(self, r: Response, rng: random.Random) -> int:
        """1-5 score from perceived quality."""
        p = self.perceived(r, rng)
        return 1 + sum(p > t for t in THRESHOLDS)

    def passes(self, r: Response, rng: random.Random, at: int = 4) -> bool:
        return self.score(r, rng) >= at

    def prefer_first(self, first: Response, second: Response, rng: random.Random) -> bool:
        """Pairwise: True if the response shown first is judged better."""
        diff = self.perceived(first, rng) - self.perceived(second, rng) + self.position_bias
        return rng.random() < _sigmoid(4 * diff)


def human(name: str, severity: float = 0.0, noise: float = 0.35) -> Rater:
    return Rater(name, severity=severity, noise=noise)


def judge(name: str = "judge", **biases) -> Rater:
    """An LLM judge. Without arguments: unbiased and a little noisier than a careful human."""
    params = {"noise": 0.4, **biases}
    return Rater(name, **params)


# A reference panel of three human raters (known severities) and a set of judges, one bias each.
HUMANS = (human("human-1", -0.15), human("human-2", 0.15), human("human-3", 0.0))
JUDGES = {
    "fair": judge("fair"),
    "position-biased": judge("position-biased", position_bias=0.25),
    "verbose-loving": judge("verbose-loving", verbosity_bias=0.25),
    "self-preferring": judge("self-preferring", self_preference=0.35, family="family-x"),
    "lenient": judge("lenient", severity=-0.6),
    "noisy": judge("noisy", noise=1.2),
}
