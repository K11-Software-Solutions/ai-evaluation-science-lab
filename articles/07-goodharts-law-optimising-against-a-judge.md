# 07. Goodhart's Law: Optimising Against a Judge

> **Series:** AI Evaluation Science Lab · [Index](../README.md#articles) · Previous: [06](06-drift-watching-a-judge-over-time.md) · Next: [08. The Judge Acceptance Test](08-judge-acceptance-test-ci-limitations.md)

"When a measure becomes a target, it ceases to be a good measure." (a paraphrase of Charles Goodhart, popularised by Marilyn Strathern). An LLM judge used only to **report** quality can be biased and still roughly right. A judge used to **select** or **train** outputs is different: whatever it rewards apart from quality, the system learns to supply.

## Best-of-n

The simplest form of optimisation: generate *n* candidate answers and keep the one the judge likes best. It is widely used, and it is a direct test of what the judge rewards.

Experiment E5 does this for system gamma on 400 prompts, with candidates that vary in quality and in length, selected by the fair judge or by the verbose-loving one:

| Selector | Candidates | True quality | The judge's own score | Length (tokens) |
|---|---|---|---|---|
| fair judge | 1 | −0.05 | −0.03 | 247 |
| fair judge | 4 | 0.40 | 0.40 | 230 |
| fair judge | 16 | **0.71** | 0.71 | 239 |
| verbose-loving judge | 1 | −0.05 | 0.09 | 247 |
| verbose-loving judge | 4 | 0.34 | 0.59 | 304 |
| verbose-loving judge | 16 | **0.60** | **1.03** | **375** |

With the fair judge, selection improves true quality and the judge's score tracks it closely. With the length-biased judge:

- **True quality improves less**: 0.60 instead of 0.71 at 16 candidates, because some of the selection pressure goes to length instead.
- **Answers get 50% longer**, a change users pay for in reading time and the business pays for in tokens.
- **The judge's own score overstates the gain**: it reports 1.03 where the truth is 0.60. A team watching only the judge's score would see a large improvement and ship it.

The gap between the judge's score and the truth **grows with optimisation pressure**: almost none with one candidate, about 0.25 with four, over 0.4 with sixteen. Training against a judge, which applies far more pressure than picking 1 of 16, magnifies it further.

## How to guard against it

1. **Never use the same judge to optimise and to evaluate.** Select or train with one judge; report with another, plus human spot checks.
2. **Track the features the judge might be rewarding**, such as length, formatting and confident tone, next to the score. If length rises with the score, suspect the judge.
3. **Hold out a human-labelled set** that is never used for selection or tuning, and re-measure on it after every optimisation round.
4. **Run the acceptance battery (article 04) before using a judge as an optimisation target**, not only before using it for reports. A bias that is harmless in reporting becomes the thing you optimise for.

## Takeaways

- **Optimising against a biased judge buys the bias, not just quality.**
- **The judge's score overstates the gain, more so the harder you optimise.**
- **Separate the judge you optimise against from the judge you report with.**
- **Watch length and other proxies alongside the score.**
