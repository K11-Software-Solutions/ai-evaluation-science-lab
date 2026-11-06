# 03. Reliability Statistics: Kappa's Paradox and Krippendorff's Alpha

> **Series:** AI Evaluation Science Lab · [Index](../README.md#articles) · Previous: [02](02-a-world-where-the-truth-is-known.md) · Next: [04. Judge Biases](04-judge-biases-position-verbosity-self-preference.md)

## Why chance correction

Two raters who label 95% of answers "pass" will agree 90% of the time by guessing "pass" for everything. Percent agreement cannot tell skill from that. Cohen's kappa corrects for the agreement expected by chance:

```text
kappa = (observed agreement - chance agreement) / (1 - chance agreement)
```

## The paradox

Chance correction has a side effect. Experiment E1 simulates two raters who are each **right 90% of the time**, on 4,000 items, varying only how common failures are:

| Share of answers that fail | Percent agreement | Cohen's kappa | Krippendorff's alpha | Agreement on fails | Agreement on passes |
|---|---|---|---|---|---|
| 50% | 0.82 | **0.63** | 0.63 | 0.82 | 0.82 |
| 20% | 0.82 | 0.54 | 0.54 | 0.66 | 0.88 |
| 5% | 0.81 | **0.22** | 0.22 | **0.33** | 0.89 |

The raters are equally good in all three rows. Percent agreement barely moves. Kappa falls from "substantial" to "fair" on the usual scales, purely because failures became rare. This is the **kappa paradox** (Feinstein and Cicchetti, 1990): when one category is rare, chance agreement is high, so the same skill earns a lower kappa.

It matters for AI evaluation because the interesting category is usually rare: hallucinations, unsafe answers, injection successes. A judge validated on a set where 5% of answers fail will show a low kappa even if it is as good as on a balanced set, and a judge validated on a balanced set will look better than it will be in production.

**What to report instead of a single number:** kappa (or alpha) **with the prevalence**, plus **specific agreement** for each category. The last two columns are the share of each category's ratings on which the raters agreed. They expose the real problem: on rare failures, the raters agreed only a third of the time.

## Krippendorff's alpha

Kappa compares two raters with complete data. Real labelling panels have more raters, missing ratings, and ordinal scales. **Krippendorff's alpha** handles all of that in one framework:

```text
alpha = 1 - observed disagreement / disagreement expected by chance
```

with the disagreement measured to suit the data: any difference counts fully for **nominal** labels; for **ordinal** scores, a 2-versus-3 disagreement costs less than 1-versus-5, weighted by how many ratings fall between them; for **interval** data, squared differences.

[`evalsci/agreement.py`](../evalsci/agreement.py) implements all three levels with missing ratings, and is tested against the value Krippendorff published for his own example data (0.743). On large samples with two raters and nominal labels, alpha and kappa agree to two decimals (E1), so alpha shares the paradox; its advantages are flexibility and a single method for every panel.

## Comparing like with like

When this lab first compared a judge's alpha with the humans', the judge looked **better** than the humans (0.85 against 0.81). It was being compared with the median of three humans, while each human was compared with other individuals: a consensus is less noisy than any one person, so anything compared with it scores higher. The battery now compares **every** rater, judge or human, with the consensus of two **other** humans. The fair judge's alpha (0.84) then sits right next to the human ceiling measured the same way (0.82), as it should.

## Takeaways

- **Always report prevalence next to kappa or alpha**, and the agreement within each category.
- **Rare-category agreement is the number that matters** for safety evaluations, and kappa hides it.
- **Use Krippendorff's alpha for panels**: any number of raters, missing data, ordinal scales.
- **Compare judge and human agreement against the same reference**, or the comparison flatters one of them.
