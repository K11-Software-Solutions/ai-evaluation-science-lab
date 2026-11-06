# 02. A World Where the Truth Is Known

> **Series:** AI Evaluation Science Lab · [Index](../README.md#articles) · Previous: [01](01-what-evaluation-science-adds.md) · Next: [03. Kappa's Paradox and Krippendorff's Alpha](03-kappa-paradox-krippendorff-alpha.md)

## Systems and responses

[`evalsci/world.py`](../evalsci/world.py) defines four AI systems answering the same prompts:

| System | Family | Skill | Notes |
|---|---|---|---|
| alpha | family-x | +0.30 | best |
| beta | family-y | +0.20 | |
| gamma | family-x | 0.00 | same family as alpha |
| delta | family-z | −0.20 | weakest, and writes **60% longer** answers |

Each response's **true quality** is the system's skill minus the prompt's difficulty plus noise. Its **length** is drawn independently of quality, except that delta is verbose. So any evaluator that rewards length is rewarding something other than quality, and the simulation can tell exactly how much.

## Raters and judges

[`evalsci/raters.py`](../evalsci/raters.py) defines every evaluator by the same parameters, in quality units:

| Parameter | Meaning |
|---|---|
| severity | harsher (+) or more lenient (−) than the truth |
| noise | random error per judgement |
| position_bias | pull towards whichever response is shown first (pairwise) |
| verbosity_bias | extra credit per 100 tokens above 200 |
| self_preference | extra credit for responses from the judge's own family |
| drift_per_day | leniency that changes over time |

Raters give **pointwise** scores (1 to 5, pass at 4 or above) or **pairwise** preferences (which of two is better).

The **human panel** has three raters with severities −0.15, +0.15 and 0, and noise 0.35: careful, but not identical. The **judges** each have one problem:

| Judge | Problem |
|---|---|
| fair | none (noise 0.4, a little noisier than a careful human) |
| position-biased | +0.25 towards the first-shown response |
| verbose-loving | +0.25 per 100 extra tokens |
| self-preferring | +0.35 for family-x responses |
| lenient | 0.6 more lenient than the truth |
| noisy | noise 1.2 |
| drifting | becomes more lenient each day from day 10 |

The biases are sized to be comparable to the differences between systems (0.1 to 0.5), which is what makes them matter. They mirror the biases documented for LLM-as-judge in the research literature (Zheng et al., 2023, among others).

## What the lab measures

| Module | Purpose |
|---|---|
| [`agreement.py`](../evalsci/agreement.py) | percent agreement, Cohen's kappa, weighted kappa, Krippendorff's alpha, Wilson and bootstrap intervals |
| [`battery.py`](../evalsci/battery.py) | the judge acceptance tests: agreement, leniency, order consistency, position, verbosity, self-preference |
| [`studies.py`](../evalsci/studies.py) | pairwise system comparison (counterbalanced or fixed order), drift monitoring, best-of-n selection |

The statistics are checked against cases you can compute by hand, and Krippendorff's alpha against the published value (0.743) for Krippendorff's own example data, so the tools can be trusted before they are used to judge anything else.
