"""Agreement statistics against hand-computable cases and known properties."""
import random

import pytest

from evalsci.agreement import (bootstrap_ci, cohen_kappa, krippendorff_alpha, percent_agreement,
                               weighted_kappa, wilson)


def test_perfect_and_chance_agreement():
    a = [1, 0, 1, 0, 1, 0, 1, 0]
    assert cohen_kappa(a, a) == 1.0 and percent_agreement(a, a) == 1.0
    assert cohen_kappa(a, [1, 1, 0, 0, 1, 1, 0, 0]) == pytest.approx(0.0)


def test_kappa_hand_computed():
    # 2x2: both yes 20, both no 15, a-yes-b-no 5, a-no-b-yes 10; n = 50
    a = [1] * 20 + [0] * 15 + [1] * 5 + [0] * 10
    b = [1] * 20 + [0] * 15 + [0] * 5 + [1] * 10
    po = 35 / 50
    pe = (25 / 50) * (30 / 50) + (25 / 50) * (20 / 50)
    assert cohen_kappa(a, b) == pytest.approx((po - pe) / (1 - pe))


def test_weighted_kappa_gives_partial_credit():
    truth = [1, 2, 3, 4, 5] * 10
    near = [min(5, x + 1) for x in truth]
    far = [6 - x for x in truth]
    assert weighted_kappa(truth, near) > 0.7 > 0 > weighted_kappa(truth, far)


def test_alpha_matches_kappa_for_two_raters_nominal_large_n():
    rng = random.Random(0)
    truth = [rng.random() < 0.3 for _ in range(3000)]
    a = [t if rng.random() < 0.85 else not t for t in truth]
    b = [t if rng.random() < 0.85 else not t for t in truth]
    assert krippendorff_alpha([[x, y] for x, y in zip(a, b)], "nominal") == pytest.approx(cohen_kappa(a, b), abs=0.01)


def test_alpha_reference_value():
    # Krippendorff's reliability data example (nominal, with missing values): alpha = 0.743
    data = [[1, 1, None, 1], [2, 2, 3, 2], [3, 3, 3, 3], [3, 3, 3, 3], [2, 2, 2, 2], [1, 2, 3, 4],
            [4, 4, 4, 4], [1, 1, 2, 1], [2, 2, 2, 2], [None, 5, 5, 5], [None, None, 1, 1], [None, None, 3, None]]
    assert krippendorff_alpha(data, "nominal") == pytest.approx(0.743, abs=0.001)


def test_alpha_ordinal_penalises_far_disagreements_more():
    close = [[3, 4]] * 10 + [[1, 1], [5, 5], [2, 2], [4, 4]] * 5
    far = [[1, 5]] * 10 + [[1, 1], [5, 5], [2, 2], [4, 4]] * 5
    assert krippendorff_alpha(close, "ordinal") > krippendorff_alpha(far, "ordinal")


def test_wilson_interval():
    p, lo, hi = wilson(50, 100)
    assert p == 0.5 and lo < 0.5 < hi and hi - lo == pytest.approx(0.19, abs=0.01)
    _, lo0, hi0 = wilson(0, 20)
    assert lo0 == pytest.approx(0.0, abs=1e-9) and 0 < hi0 < 0.2       # never a zero-width interval at 0


def test_bootstrap_interval_narrows_with_more_items():
    rng = random.Random(1)
    small = [rng.random() for _ in range(25)]
    large = [rng.random() for _ in range(400)]
    mean = lambda v: sum(v) / len(v)
    _, lo_s, hi_s = bootstrap_ci(small, mean)
    _, lo_l, hi_l = bootstrap_ci(large, mean)
    assert hi_l - lo_l < (hi_s - lo_s) / 2
