# 05. How Many Items? Intervals and Power for Evaluators

> **Series:** AI Evaluation Science Lab · [Index](../README.md#articles) · Previous: [04](04-judge-biases-position-verbosity-self-preference.md) · Next: [06. Drift](06-drift-watching-a-judge-over-time.md)

Two sample-size questions come up in every evaluation programme: how many labelled items do I need to **validate a judge**, and how many prompts do I need to **tell two systems apart**? Both have answers you can compute before labelling anything.

## Validating a judge: how wide is the interval?

Experiment E3a computes the judge's Krippendorff's alpha with a bootstrap 95% interval, by number of labelled items:

| Labelled items | Width of the 95% interval on alpha |
|---|---|
| 24 | **0.18** |
| 50 | 0.10 |
| 100 | 0.08 |
| 200 | 0.05 |
| 400 | 0.04 |

With 24 items, a judge reported as "alpha 0.80" could plausibly be anywhere from about 0.71 to 0.89: the difference between "good" and "not good enough" on most scales. That is the size of many hand-labelled validation sets, including the starter set in [Becoming an AI Quality Engineer](https://github.com/K11-Software-Solutions/becoming-ai-quality-engineer). Interval width shrinks with the square root of the number of items: four times the items, half the width.

**Practical rule:** decide how precisely you need to know agreement (for example ±0.05), then label enough items to get there (here, about 200), and report the interval, not just the number.

## Comparing systems: what is the power?

Experiment E3b compares beta with gamma, whose true skills differ by 0.2 (beta's answer is truly better on about 61% of prompts; a judge's noise pulls the observed rate closer to 50%). Each comparison is pairwise and counterbalanced; it "detects" the difference if the 95% interval on beta's win rate lies entirely above 0.5. Thirty trials per row:

| Prompts | Fair judge detects it | Noisy judge detects it |
|---|---|---|
| 25 | 10% | 10% |
| 50 | 27% | 20% |
| 100 | 23% | 7% |
| 200 | 50% | 13% |
| 400 | **83%** | **27%** |

Two lessons:

1. **Small differences need hundreds of prompts.** With 100 prompts, a real 0.2-skill difference is detected less than a quarter of the time. "No significant difference" on a small eval set usually means "not enough data", not "no difference".
2. **A noisier judge needs far more data.** At 400 prompts the noisy judge detects the difference about a third as often as the fair one. Judge noise is not just an accuracy problem; it multiplies the cost of every comparison you make with that judge.

The rows are not perfectly monotonic (100 prompts did slightly worse than 50) because each row is 30 trials: the power estimates themselves have sampling error of several points. More trials would smooth them; the pattern does not change.

## Before you label

1. **Fix the smallest difference that matters**: in agreement (for validation) or in win rate (for comparison). That is a product decision.
2. **Estimate the noise**: from a pilot, or from the judge's measured consistency.
3. **Simulate the study**, as E3 does, or use a power formula, and pick the sample size that gives the precision or power you need (80% is conventional).
4. **Report intervals with every result**, so readers can see when a study was too small to say anything.

## Takeaways

- **24 labelled items give an interval of about ±0.09 on agreement.** Plan for hundreds.
- **Interval width falls with the square root of the sample size.**
- **Telling similar systems apart takes hundreds of prompts,** more with a noisy judge.
- **"No significant difference" from a small study is usually just a small study.**
