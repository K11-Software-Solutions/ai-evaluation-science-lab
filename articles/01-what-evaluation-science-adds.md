# 01. What Evaluation Science Adds

> **Series:** AI Evaluation Science Lab · [Index](../README.md#articles) · Next: [02. A World Where the Truth Is Known](02-a-world-where-the-truth-is-known.md)

This is the seventh lab in a series for quality engineers moving into AI. Every earlier lab relied on an **evaluator**: a rule, a human label or an LLM judge deciding whether an answer was good. This lab turns the question around: **how far can the evaluator itself be trusted, and how would you know?**

[Becoming an AI Quality Engineer](https://github.com/K11-Software-Solutions/becoming-ai-quality-engineer) introduced the basics: validating a judge against human labels with Cohen's kappa, per-item-type agreement, a two-reviewer human ceiling and a Rasch model of grader severity. This lab goes further, into the questions that decide whether an evaluation result means anything:

| Question | Article |
|---|---|
| Is my agreement statistic telling me what I think it is? | 03: kappa's paradox, Krippendorff's alpha |
| Does my LLM judge prefer the first answer, the longer answer, or its own family's answer? | 04: bias tests |
| How many items do I need to trust a judge, or to say one system is better? | 05: intervals and power |
| Has my judge changed since I validated it? | 06: drift monitoring |
| What happens when someone optimises against my judge? | 07: Goodhart's law |
| What should a judge pass before I use it? | 08: an acceptance test in CI |

## Measurement, not just testing

Testing asks "does it pass?". Measurement asks "how big is it, how sure are we, and would we get the same answer again?". An evaluator is a measuring instrument, and instruments have properties that can be studied:

- **Reliability**: would two raters, or the same rater twice, give the same verdict?
- **Validity**: does the verdict track what we actually care about, or something correlated with it (like length)?
- **Bias**: does it shift systematically for reasons unrelated to quality (position, family)?
- **Stability**: is it the same instrument today as on the day it was validated?
- **Precision**: how wide is the interval around any number it produces?

## The central finding

Experiment E2 and article 04 make the point that runs through the whole lab: **a judge can agree with humans as well as a fair judge does and still be badly biased.** Position-biased, length-biased and self-preferring judges all reached the same Krippendorff's alpha with the human consensus as the fair judge (0.82 to 0.84). Yet two of them changed which system came out on top. Agreement is necessary; it is not sufficient. Bias has to be tested directly, with designs that isolate it.

## Why simulate

With real data you never know the true quality of an answer, so you can never check whether a statistic got the right answer. In this lab's simulated world every response has a known true quality, every rater has a known severity and noise, and every judge has known biases. That makes it possible to show what each method **can** detect, how much data it needs, and where it fails, before you apply it to data where the truth is hidden. Article 08 lists what simulation leaves out.
