# AI Evaluation Science Lab

[![CI quality gates](https://github.com/K11-Software-Solutions/ai-evaluation-science-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/K11-Software-Solutions/ai-evaluation-science-lab/actions/workflows/ci.yml)
[![Code: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24025309.svg)](https://doi.org/10.5281/zenodo.24025309) [![Articles: CC BY 4.0](https://img.shields.io/badge/Articles-CC%20BY%204.0-lightgrey.svg)](articles/LICENSE.md)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![No dependencies](https://img.shields.io/badge/runtime%20deps-none-success)
![No API key needed](https://img.shields.io/badge/API%20key-not%20required-success)

**How far can an evaluator be trusted, and how would you know? Reliability statistics beyond kappa, LLM-judge bias tests, sample sizes for validating judges and comparing systems, drift monitoring, Goodhart effects, and an acceptance test a judge must pass before it is used.**

The seventh lab in a series for quality engineers moving into AI:

| Lab | Question it answers |
|---|---|
| [Becoming an AI Quality Engineer](https://github.com/K11-Software-Solutions/becoming-ai-quality-engineer) | Is the RAG **application** good enough to ship? |
| [LLM Model Testing Lab](https://github.com/K11-Software-Solutions/llm-model-testing-lab) | Is the **model** good enough? |
| [Agent Testing Lab](https://github.com/K11-Software-Solutions/agent-testing-lab) | Is the **agent** safe to let act? |
| [AI Production Monitoring Lab](https://github.com/K11-Software-Solutions/ai-production-monitoring-lab) | Is it **still** good, for the users we actually have, right now? |
| [Multi-Agent Testing Lab](https://github.com/K11-Software-Solutions/multi-agent-testing-lab) | When **agents work together**, does the team do the right thing, and who broke it when it doesn't? |
| [AI Performance and Cost Lab](https://github.com/K11-Software-Solutions/ai-performance-cost-lab) | Is it **fast enough under load**, and what does each **good answer** cost? |
| **AI Evaluation Science Lab** (this repo) | Can we **trust the evaluator**, and how sure are we? |
| [AI Data Quality Lab](https://github.com/K11-Software-Solutions/ai-data-quality-lab) | Is the **data** behind it all fit to learn from, test with and retrieve? |
| [AI Security Testing Lab](https://github.com/K11-Software-Solutions/ai-security-testing-lab) | Can an **attacker** make it misbehave, and how sure are we that they can't? |
| [MCP Testing Lab](https://github.com/K11-Software-Solutions/mcp-testing-lab) | Can we trust the **tools our agents plug into**? |

## How it works

A simulated world where the truth is known: four AI systems of known skill (one weak but verbose, two from the same model family) answer the same prompts; a panel of three human raters with known severity and noise; and LLM judges, each with one known problem: position bias, verbosity bias, self-preference, leniency, noise or drift. Because every response's true quality is known, every statistic and every test can be checked against the truth before it is applied to real data, where the truth is hidden.

## Articles

| # | Article |
|---|---|
| 01 | [What Evaluation Science Adds](articles/01-what-evaluation-science-adds.md) |
| 02 | [A World Where the Truth Is Known](articles/02-a-world-where-the-truth-is-known.md) |
| 03 | [Reliability Statistics: Kappa's Paradox and Krippendorff's Alpha](articles/03-kappa-paradox-krippendorff-alpha.md) |
| 04 | [Judge Biases: Position, Verbosity and Self-Preference](articles/04-judge-biases-position-verbosity-self-preference.md) |
| 05 | [How Many Items? Intervals and Power for Evaluators](articles/05-how-many-items-intervals-and-power.md) |
| 06 | [Drift: Watching a Judge Over Time](articles/06-drift-watching-a-judge-over-time.md) |
| 07 | [Goodhart's Law: Optimising Against a Judge](articles/07-goodharts-law-optimising-against-a-judge.md) |
| 08 | [The Judge Acceptance Test, CI and Limitations](articles/08-judge-acceptance-test-ci-limitations.md) |

## Quick start

Requirements: Python 3.11+. No runtime dependencies and no API key.

```bash
git clone https://github.com/K11-Software-Solutions/ai-evaluation-science-lab.git
cd ai-evaluation-science-lab
python -m venv .venv
source .venv/bin/activate              # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

```bash
pytest                                                          # 26 tests
python -m evals.run_judge_acceptance                            # the fair judge: must pass
JUDGE=verbose-loving python -m evals.run_judge_acceptance       # a biased judge: must fail
python -m experiments.run_experiments                           # the five experiments behind the articles
```

## Repository layout

```text
evalsci/
  world.py       systems, prompts and responses with known true quality and length
  raters.py      human raters and LLM judges: severity, noise, position, verbosity, self-preference, drift
  agreement.py   percent agreement, Cohen's kappa, weighted kappa, Krippendorff's alpha, Wilson and bootstrap intervals
  battery.py     the judge acceptance tests, each designed to isolate one property
  studies.py     pairwise system comparison, drift monitoring (threshold and CUSUM), best-of-n selection
evals/
  run_judge_acceptance.py   runs the battery on a judge and gates on it
  thresholds.json           acceptance thresholds
experiments/    E1 kappa paradox, E2 biases and rankings, E3 sample sizes, E4 drift, E5 Goodhart; results committed
tests/          26 tests, including a check against Krippendorff's published example
articles/       the eight articles
.github/workflows/ci.yml   tests -> judge acceptance + 6 biased judges that must fail -> experiments reproducibility check
```

## What the lab finds

- **Agreement does not reveal bias.** Position-biased, length-biased and self-preferring judges agreed with humans as well as a fair judge (Krippendorff's alpha 0.82 to 0.84), and two of them changed which systems ranked higher.
- **The kappa paradox.** Two raters who are each right 90% of the time score kappa 0.63 when half the answers fail and 0.22 when 5% fail; on the rare failures they agree only a third of the time.
- **A fair comparison changed the verdict.** Compared with a three-human median, a judge looked better than the humans; compared with the same reference as the humans, it sat next to them.
- **Counterbalancing removes position bias; nothing in the study design removes length or family bias.**
- **24 labelled items give a ±0.09 interval on agreement;** telling two systems 0.2 apart in skill took about 400 prompts with a fair judge and was mostly impossible with a noisy one.
- **CUSUM caught small sudden shifts in a judge that a threshold missed** (90% against 43% for a 0.15 shift).
- **Best-of-16 selection with a length-biased judge** gained less true quality than with a fair judge (0.60 against 0.71), made answers 50% longer, and scored the answers it picked 0.43 above their true quality.

## CI quality gates

Every push runs three jobs: **tests**; **judge acceptance**, where the fair judge must pass and six biased judges (position, verbosity, self-preference, leniency, noise, drift) must each fail; and an **experiments** job that fails if the results differ from the committed ones.

## Limitations

A simulated world with one-dimensional quality, additive constant biases and independent raters; only the biases built in; exact equal-quality pairs; one task; teaching implementations of the statistics. [Article 08](articles/08-judge-acceptance-test-ci-limitations.md#limitations) covers each and how to run the battery on a real judge.

## About

Created by **Kavita Jadhav**, founder of [K11 Software Solutions](https://github.com/K11-Software-Solutions), Senior SDET and AI Quality Engineer working on LLM evaluation, red teaming and agentic QA systems.

**Licences:** code under the [MIT License](LICENSE); the written material in [`articles/`](articles/LICENSE.md) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (share and adapt with credit).

The systems, raters, judges and data are simulated.

## Citing

Use GitHub's **Cite this repository** button (from [`CITATION.cff`](CITATION.cff)). Each tagged release is archived on Zenodo with its own DOI. Cite the version you used:

> Jadhav, K. (2026). *AI Evaluation Science Lab* (Version v1.0.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.24025310

To refer to the project as a whole (always resolves to the latest version), use the concept DOI: https://doi.org/10.5281/zenodo.24025309
