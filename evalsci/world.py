"""A world with known ground truth: prompts, AI systems and their responses.

Every response has a TRUE quality (a latent number) and observable features an
evaluator might be swayed by: its length, and which model family produced it.
Because the truth is known, every evaluator in this lab can be scored against it,
something you can never do with real data, which is why simulation is the right
place to learn what each statistic can and cannot tell you.

Quality = system skill - prompt difficulty + noise. Length is drawn independently
of quality unless a system is explicitly verbose, so any evaluator that rewards
length is rewarding something other than quality.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class System:
    name: str
    family: str           # model family; judges may prefer their own
    skill: float          # latent, in quality units
    verbosity: float = 1.0   # multiplies response length


@dataclass(frozen=True)
class Prompt:
    id: int
    difficulty: float


@dataclass(frozen=True)
class Response:
    prompt: int
    system: str
    family: str
    quality: float        # the truth
    length: int           # tokens


DEFAULT_SYSTEMS = (
    System("alpha", "family-x", 0.30),
    System("beta", "family-y", 0.20),
    System("gamma", "family-x", 0.00),
    System("delta", "family-z", -0.20, verbosity=1.6),     # weaker, but writes long answers
)


def prompts(n: int, seed: int = 0) -> list[Prompt]:
    rng = random.Random(seed)
    return [Prompt(i, rng.gauss(0, 0.8)) for i in range(n)]


def respond(system: System, prompt: Prompt, rng: random.Random, noise: float = 0.5) -> Response:
    quality = system.skill - prompt.difficulty + rng.gauss(0, noise)
    length = max(20, int(rng.lognormvariate(5.3, 0.35) * system.verbosity))   # ~200 tokens typical
    return Response(prompt.id, system.name, system.family, quality, length)


def responses(systems=DEFAULT_SYSTEMS, n_prompts: int = 200, seed: int = 0) -> dict[str, list[Response]]:
    rng = random.Random(seed + 1)
    ps = prompts(n_prompts, seed)
    return {s.name: [respond(s, p, rng) for p in ps] for s in systems}
