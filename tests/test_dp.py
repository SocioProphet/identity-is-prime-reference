from __future__ import annotations

import random
import statistics
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prime_er.dp import (  # noqa: E402
    BudgetExhausted,
    PrivacyLedger,
    clamp_contribution,
    laplace_noise,
    release_histogram,
    suppression_delta,
)


def test_laplace_is_deterministic_under_seed():
    a = [laplace_noise(random.Random(42), 1.0) for _ in range(5)]
    b = [laplace_noise(random.Random(42), 1.0) for _ in range(5)]
    assert a == b


def test_laplace_zero_scale_is_zero():
    assert laplace_noise(random.Random(0), 0.0) == 0.0


def test_laplace_mean_and_variance_track_scale():
    rng = random.Random(7)
    scale = 2.0
    xs = [laplace_noise(rng, scale) for _ in range(20000)]
    # Mean ~ 0; variance of Laplace(0, b) = 2 b^2.
    assert abs(statistics.fmean(xs)) < 0.15
    assert abs(statistics.pvariance(xs) - 2 * scale * scale) < 1.5


def test_clamp_contribution_bounds_sensitivity():
    # One flooding actor present in 50 cells; others in 1 each.
    actor_cells = {"flood": {f"c{i}" for i in range(50)}}
    for j in range(10):
        actor_cells[f"u{j}"] = {"c0"}
    counts, clipped = clamp_contribution(actor_cells, max_contribution=2, seed=1)
    assert clipped == 1  # only the flooder was clipped
    # The flooder can now add to at most 2 cells, so c0 <= 10 (users) + 1 (maybe flood).
    assert counts["c0"] <= 11
    # No cell can exceed total actors.
    assert max(counts.values()) <= 11


def test_release_histogram_suppresses_small_cells_on_noisy_count():
    # Low noise (eps high) so the noisy count tracks the true count closely:
    # small (1) stays well under threshold 8; big (500) clears it.
    true_counts = {"big": 500, "small": 1}
    released, suppressed = release_histogram(
        true_counts, epsilon=5.0, sensitivity=1, threshold=8, rng=random.Random(3)
    )
    assert "small" in suppressed
    assert "small" not in released
    assert "big" in released
    assert released["big"] >= 0


def test_release_histogram_requires_positive_epsilon():
    with pytest.raises(ValueError):
        release_histogram({"a": 10}, epsilon=0.0, sensitivity=1, threshold=1, rng=random.Random(0))


def test_suppression_delta_decreases_with_threshold():
    # Higher threshold -> smaller delta; below sensitivity -> trivial 0.5 bound.
    d_low = suppression_delta(threshold=5, sensitivity=1, epsilon=1.0)
    d_high = suppression_delta(threshold=20, sensitivity=1, epsilon=1.0)
    assert 0.0 < d_high < d_low <= 0.5
    assert suppression_delta(threshold=1, sensitivity=2, epsilon=1.0) == 0.5


def test_ledger_spends_and_fails_closed():
    led = PrivacyLedger(total_budget=1.0)
    led.spend(0.6, "q1")
    assert abs(led.remaining - 0.4) < 1e-9
    with pytest.raises(BudgetExhausted):
        led.spend(0.6, "q2")  # would exceed
    # Spend state unchanged after refusal.
    assert abs(led.spent - 0.6) < 1e-9


def test_ledger_persists_across_load(tmp_path: Path):
    p = str(tmp_path / "ledger.json")
    led = PrivacyLedger.load_or_init(p, total_budget=2.0)
    led.spend(1.5, "run1")
    # Re-load: stored spend is authoritative, so only 0.5 remains.
    led2 = PrivacyLedger.load_or_init(p, total_budget=2.0)
    assert abs(led2.remaining - 0.5) < 1e-9
    with pytest.raises(BudgetExhausted):
        led2.spend(0.6, "run2")
