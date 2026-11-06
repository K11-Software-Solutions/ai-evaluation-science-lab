# 08. The Judge Acceptance Test, CI and Limitations

> **Series:** AI Evaluation Science Lab · [Index](../README.md#articles) · Previous: [07](07-goodharts-law-optimising-against-a-judge.md)

## An acceptance test for judges

Before an LLM judge is used to report or optimise anything, it should pass a fixed battery, the same way a new build passes its tests. `python -m evals.run_judge_acceptance` runs it:

| Check | Requirement |
|---|---|
| Agreement with the human consensus (Krippendorff's alpha) | no more than 0.05 below the humans' own alpha, measured the same way |
| Leniency | pass rate within 8 points of the human pass rate |
| Order consistency | the same verdict with the order swapped, at least 65% of pairs |
| Position bias | the 95% interval of the first-shown win rate contains 0.5 |
| Verbosity bias | the 95% interval of the longer-response win rate (equal quality) contains 0.5 |
| Self-preference | the 95% interval of the own-family gap is not entirely above 0 |
| Drift | no CUSUM alarm on the anchor set over a month |

Two choices are deliberate. Agreement is compared with the **human ceiling**, not a fixed number, so the requirement adapts to how hard the task is. Bias checks use **intervals**, so a judge fails only on evidence of bias, not on noise.

## Negative controls

CI runs the battery on every simulated judge. The fair judge must pass; every other judge must fail, each for its own reason:

| Judge | Fails on |
|---|---|
| position-biased | position |
| verbose-loving | verbosity |
| self-preferring | self-preference |
| lenient | leniency and agreement |
| noisy | agreement and consistency |
| drifting | drift |

If any of them passes, the battery has lost the ability to see that problem, and the build fails.

## Reproducible experiments

The five experiments behind articles 03 to 07 are deterministic. CI re-runs them and fails if the results differ from the committed [`experiments/results/summary.md`](../experiments/results/summary.md).

## Limitations

- **Simulated world.** True quality is one number, biases are additive and constant, and raters are independent. Real quality is multi-dimensional, biases interact and vary by task, and human raters influence each other.
- **The biases are the ones we built in.** Real judges have others: preference for confident tone, for formatting, for answers that match their own; sensitivity to prompt wording. The battery's structure (one isolating design per bias) extends to them; the list does not.
- **Equal-quality pairs are exact here.** With real data, length-controlled and family-controlled pairs have to be constructed and checked by humans, and that check has its own error.
- **One judge, one task.** A judge accepted for groundedness is not accepted for helpfulness or safety. Run the battery per task.
- **Teaching implementations.** For publication-grade analysis, use established packages (for example `krippendorff` in Python, or `irr` in R) and report your methods in full.

## Using it with a real judge

1. Collect human ratings on a few hundred items (article 05 for how many), with at least two raters per item, to measure the human ceiling.
2. Build bias pairs: swapped order for every pair; length-padded rewrites checked by humans as equal; own-family against other-family answers.
3. Replace the simulated judge with calls to your judge, keeping the checks and thresholds.
4. Keep the anchor set and the drift monitor running for as long as the judge is in use.

## Takeaways

- **Accept a judge on evidence**: agreement against the human ceiling, and a targeted test for every bias that matters.
- **Prove the battery with biased judges that must fail.**
- **Re-accept after any change, and watch for drift in between.**
