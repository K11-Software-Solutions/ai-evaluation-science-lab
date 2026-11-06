"""Simulated world and raters, the acceptance battery, and the study designs."""
import json
import random
from dataclasses import replace

import pytest

from evals import run_judge_acceptance as acc
from evalsci.battery import run_battery
from evalsci.raters import HUMANS, JUDGES, THRESHOLDS, judge
from evalsci.studies import best_of_n, compare_systems, drift_monitor, true_win_rate
from evalsci.world import DEFAULT_SYSTEMS, Response, prompts, responses


def test_world_is_deterministic_and_skills_order_quality():
    a, b = responses(seed=3), responses(seed=3)
    assert a == b
    mean_q = {s: sum(r.quality for r in rs) / len(rs) for s, rs in a.items()}
    assert mean_q["alpha"] > mean_q["beta"] > mean_q["gamma"] > mean_q["delta"]
    lengths = {s: sum(r.length for r in rs) / len(rs) for s, rs in a.items()}
    assert lengths["delta"] > 1.4 * lengths["gamma"]                  # verbose, not better


def test_scores_follow_quality_and_severity():
    rng = random.Random(0)
    good, bad = Response(0, "s", "f", 1.5, 200), Response(0, "s", "f", -1.5, 200)
    fair = judge("x", noise=0.0)
    assert fair.score(good, rng) == 5 and fair.score(bad, rng) == 1
    assert judge("x", noise=0.0, severity=1.0).score(good, rng) < 5
    assert len(THRESHOLDS) == 4


@pytest.mark.parametrize("bias, expect", [
    ({"verbosity_bias": 0.5}, "longer"), ({"self_preference": 0.5, "family": "f"}, "own"),
])
def test_biases_move_perceived_quality(bias, expect):
    rng = random.Random(0)
    j = judge("j", noise=0.0, **bias)
    base = Response(0, "s", "f" if expect == "own" else "g", 0.0, 500 if expect == "longer" else 200)
    assert j.perceived(base, rng) > 0.0


def test_position_bias_favours_the_first_shown():
    rng = random.Random(0)
    same = Response(0, "s", "f", 0.0, 200)
    biased = judge("p", noise=0.0, position_bias=0.5)
    assert sum(biased.prefer_first(same, same, rng) for _ in range(2000)) / 2000 > 0.8


def test_battery_separates_the_fair_judge_from_each_bias():
    fair = run_battery(JUDGES["fair"])
    assert fair["position"]["first_position_win_rate"][1] <= 0.5 <= fair["position"]["first_position_win_rate"][2]
    assert run_battery(JUDGES["position-biased"])["position"]["first_position_win_rate"][1] > 0.5
    assert run_battery(JUDGES["verbose-loving"])["verbosity"]["longer_wins"][1] > 0.5
    assert run_battery(JUDGES["self-preferring"])["self_preference"]["own_family_gap"][1] > 0
    assert run_battery(JUDGES["lenient"])["agreement"]["pass_rate_gap"] > 0.1


def test_agreement_alone_does_not_reveal_biases():
    alphas = {n: run_battery(JUDGES[n])["agreement"]["judge_alpha"][0]
              for n in ("fair", "position-biased", "verbose-loving", "self-preferring")}
    assert max(alphas.values()) - min(alphas.values()) < 0.05


def test_counterbalancing_removes_position_bias_from_a_comparison():
    world = responses(n_prompts=300, seed=4)
    pb = JUDGES["position-biased"]
    fixed = compare_systems(pb, world["gamma"], world["beta"], seed=1, counterbalance=False)[0]
    balanced = compare_systems(pb, world["gamma"], world["beta"], seed=1, counterbalance=True)[0]
    truth = true_win_rate(world["gamma"], world["beta"])
    assert abs(balanced - truth) < abs(fixed - truth)


def test_drift_monitor_finds_a_drift_and_stays_quiet_without_one():
    world = responses(n_prompts=100, seed=7)
    anchors = [r for rs in world.values() for r in rs][:100]
    quiet = drift_monitor(judge("fair"), anchors, 30, None, 0.0, seed=0)
    drifting = drift_monitor(judge("fair"), anchors, 30, 10, 0.03, seed=0)
    assert quiet == {"threshold": None, "cusum": None}
    assert drifting["cusum"] is not None and drifting["cusum"] >= 10


def test_best_of_n_with_a_length_biased_judge_buys_length_not_quality():
    gamma = next(s for s in DEFAULT_SYSTEMS if s.name == "gamma")
    ps = prompts(200, seed=2)
    fair = best_of_n(gamma, ps, 8, JUDGES["fair"], seed=1)
    verbose = best_of_n(gamma, ps, 8, JUDGES["verbose-loving"], seed=1)
    assert verbose["length"] > fair["length"] + 50
    assert verbose["true_quality"] < fair["true_quality"]
    assert verbose["judge_score"] > verbose["true_quality"] + 0.2           # the judge thinks it improved more


@pytest.mark.parametrize("name, passes", [
    ("fair", True), ("position-biased", False), ("verbose-loving", False), ("self-preferring", False),
    ("lenient", False), ("noisy", False), ("drifting", False),
])
def test_acceptance_gate_negative_controls(monkeypatch, tmp_path, name, passes):
    monkeypatch.setenv("JUDGE", name)
    assert (acc.main(["--out", str(tmp_path)]) == 0) is passes
    report = json.loads((tmp_path / "judge_report.json").read_text(encoding="utf-8"))
    assert bool(report["gate_failures"]) is not passes


def test_unknown_judge_is_an_error(monkeypatch, tmp_path):
    monkeypatch.setenv("JUDGE", "oracle")
    with pytest.raises(SystemExit):
        acc.main(["--out", str(tmp_path)])
