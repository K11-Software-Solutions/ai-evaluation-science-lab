# 06. Drift: Watching a Judge Over Time

> **Series:** AI Evaluation Science Lab · [Index](../README.md#articles) · Previous: [05](05-how-many-items-intervals-and-power.md) · Next: [07. Goodhart's Law](07-goodharts-law-optimising-against-a-judge.md)

A judge validated in January may not be the same instrument in March. Hosted models are updated, prompts are edited, temperature settings change. If the judge becomes more lenient, every quality metric built on it improves, and nothing in the product changed.

## Anchor items

The defence is an **anchor set**: a fixed set of items the judge re-scores on a schedule (here daily). Because the items never change, any change in the judge's pass rate on them is a change in the judge. The lab uses 100 anchors, a five-day calibration period to establish the judge's own baseline, then monitoring.

One design decision mattered: **drift is change relative to the judge itself, not relative to humans.** The first version compared the daily pass rate with the human pass rate, and every lenient or self-preferring judge "drifted" on day one. That is a leniency problem, caught at acceptance (article 08). Drift monitoring asks only "is this judge still the judge we accepted?".

## Two detectors

- **Threshold**: alarm if today's pass rate is more than 12 points from the baseline.
- **CUSUM** (Page, 1954): accumulate each day's deviation beyond a small allowance (3 points) and alarm when the running total passes a limit (0.25). Small deviations that keep pointing the same way add up; random ones cancel.

## Experiment E4

200 simulated months each, 40 days, drift starting on day 10:

| Change | Threshold: detected | days to detect | CUSUM: detected | days to detect |
|---|---|---|---|---|
| none: false alarms before day 40 | 0% | | 1.5% | |
| gradual: leniency +0.03 per day | 100% | 8.4 | 100% | 8.0 |
| sudden: +0.10 | 15% | 14.6 | **56%** | 14.8 |
| sudden: +0.15 | 43% | 11.0 | **90%** | 9.0 |
| sudden: +0.20 | 77% | 8.5 | **100%** | 5.7 |

**For gradual drift both work**: a steadily growing change soon exceeds any threshold. **For a sudden small shift**, the typical signature of a model update, the threshold mostly misses it, because one day's noise is as large as the shift. CUSUM catches it far more often because a persistent shift accumulates. The price is a small false-alarm rate (1.5% of quiet months). The limits trade one against the other: lower them and drift is found sooner, at the cost of more false alarms.

## In practice

1. **Keep a fixed anchor set**, labelled by humans, covering every item type that matters. Never tune the judge on it.
2. **Re-score it on a schedule and on every change** to the judge model, prompt or settings.
3. **Monitor with CUSUM**, alongside a threshold for large jumps, and **plot the pass rate** so a person can see the shape of a change.
4. **When an alarm fires, re-run the acceptance test** before trusting any metric produced since the change.
5. **Size the anchor set for the shift you need to see**: with 100 anchors, the daily pass rate varies by about 3 points (one standard deviation) from judge noise alone, so a single day cannot reliably show a shift of a few points; smaller shifts need more anchors or more days, which is exactly what CUSUM accumulates.

## Takeaways

- **An LLM judge is a moving instrument. Re-check it on fixed anchors.**
- **Measure drift against the judge's own baseline**, not against humans.
- **CUSUM catches small persistent shifts that thresholds miss.**
- **A drift alarm invalidates every metric since the change until the judge is re-accepted.**
