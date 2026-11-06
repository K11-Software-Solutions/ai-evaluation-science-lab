# 04. Judge Biases: Position, Verbosity and Self-Preference

> **Series:** AI Evaluation Science Lab · [Index](../README.md#articles) · Previous: [03](03-kappa-paradox-krippendorff-alpha.md) · Next: [05. How Many Items?](05-how-many-items-intervals-and-power.md)

LLM judges have been shown to prefer the answer shown first, to prefer longer answers, and to prefer answers from their own model family. Each of these can change which system wins a comparison. None of them shows up in overall agreement.

## Agreement does not reveal bias

From the acceptance battery, 300 items each:

| Judge | Alpha with human consensus | First-shown wins | Longer wins (equal quality) | Own-family gap |
|---|---|---|---|---|
| fair | 0.84 | 0.48 | 0.52 | +0.01 |
| position-biased | 0.84 | **0.60** | 0.50 | −0.02 |
| verbose-loving | 0.82 | 0.47 | **0.86** | −0.14 |
| self-preferring | 0.83 | 0.51 | 0.52 | **+0.10** |

All four agree with humans equally well. Pointwise agreement cannot see position bias at all (it only exists in pairwise judging), and verbosity and self-preference only shift scores for some responses, which barely moves an overall statistic. **Each bias needs its own test.**

## Tests that isolate one bias

**Position: judge every pair in both orders.** A fair judge picks the same winner either way, apart from noise, and the first-shown response wins half the time. The position-biased judge's first-shown response wins 60% (95% interval 57% to 64%). The **order consistency** (same verdict both ways) is also reported, but it mixes bias with noise: even the fair judge is consistent on only 72% of pairs, because many pairs are close in quality.

**Verbosity: pairs that differ only in length.** Take a response, make a short and a long version with identical quality, and ask which is better. A fair judge picks the longer one about half the time; the verbose-loving judge picks it 86% of the time. With real systems, build these pairs with controlled rewrites: pad an answer with restatement and filler that add no content, and check humans rate them equal before using them.

**Self-preference: own-family against other-family answers, compared with humans.** On the same pairs, measure how often the judge prefers its own family's answer, and how often the human panel does. The difference isolates the judge's extra preference. The self-preferring judge's gap is +0.10 (interval +0.05 to +0.15).

## What the biases do to rankings

Experiment E2 ranks the four systems by pairwise win share with each judge (true ranking: alpha > beta > gamma > delta):

| Judge | Ranking | Correct? |
|---|---|---|
| fair, counterbalanced | alpha > beta > gamma > delta | yes |
| position-biased, candidate always shown first | alpha > beta > gamma > delta | yes, but the weakest system's win share rises from 0.33 to 0.46 |
| position-biased, counterbalanced | alpha > beta > gamma > delta | yes, and the win shares return to the fair judge's |
| verbose-loving, counterbalanced | alpha > beta > **delta > gamma** | **no**: the verbose, weakest system moves up |
| self-preferring, counterbalanced | alpha > **gamma > beta** > delta | **no**: its own family's weaker system moves up |

**Counterbalancing fixes position bias**, because the bias cancels out when each system is shown first half the time. That is cheap and should always be done. **Nothing in the study design fixes verbosity or self-preference**: the bias is attached to the responses themselves. The fixes are a different judge (avoid using a model to judge its own family), an instruction that is tested to reduce the bias, or length-controlled comparisons. Each fix has to be re-tested with the same battery.

## Takeaways

- **Overall agreement cannot detect position, length or family bias.**
- **Test each bias with a design that isolates it**: swapped order, length-only pairs, family pairs compared with humans.
- **Always counterbalance pairwise comparisons.** It removes position bias for free.
- **Don't let a model judge its own family** without testing for self-preference.
