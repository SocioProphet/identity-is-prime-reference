from __future__ import annotations

from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prime_er.event import load_event_ir  # noqa: E402
from prime_er.policy import default_policy  # noqa: E402
from prime_er.segment import segment_summary  # noqa: E402


def _population():
    repo = Path(__file__).resolve().parents[1]
    ir = load_event_ir(repo / "examples" / "synthetic_population_trace.jsonl")
    return ir.events


def test_release_is_deterministic_under_seed():
    ev = _population()
    a = segment_summary(ev, default_policy(), epsilon=2.0, seed=11)
    b = segment_summary(ev, default_policy(), epsilon=2.0, seed=11)
    assert a["status"] == "RELEASED"
    assert a["counts_by_prime"] == b["counts_by_prime"]
    assert a["cohorts"] == b["cohorts"]


def test_epsilon_required_refuses():
    ev = _population()
    out = segment_summary(ev, default_policy(), epsilon=None)
    assert out["status"] == "REFUSED"
    assert out["refusal"]["reason"] == "epsilon_required"
    assert out["counts_by_prime"] == {}


def test_persistent_ledger_exhausts_and_fails_closed(tmp_path: Path):
    ev = _population()
    ledger = str(tmp_path / "eps_ledger.json")
    # Budget of 3.0; each release spends 2.0.
    first = segment_summary(ev, default_policy(), epsilon=2.0, seed=1, budget=3.0, ledger_path=ledger)
    assert first["status"] == "RELEASED"
    assert abs(first["privacy"]["budget"]["remaining"] - 1.0) < 1e-9
    # Second release wants 2.0 but only 1.0 remains -> fail-closed refusal.
    second = segment_summary(ev, default_policy(), epsilon=2.0, seed=2, budget=3.0, ledger_path=ledger)
    assert second["status"] == "REFUSED"
    assert second["refusal"]["reason"] == "budget_exhausted"
    assert second["counts_by_prime"] == {}


def test_contribution_bounding_caps_a_flooding_actor():
    # Build a flooder present under many primes/realms vs. one honest actor per prime.
    from prime_er.event import Event, Scope

    events = []
    # 10 honest founders in fog.
    for i in range(10):
        events.append(Event(ts="t", actor=f"h{i}", scope=Scope("d", "app", "citizen_fog"),
                            action="a", primes=["FOUNDER"], attrs={}, evidence={}))
    # A flooder trying to dominate every prime bin many times.
    for p in ["FOUNDER", "CITIZEN", "CREATOR", "PATIENT", "PARENT"]:
        for _ in range(50):
            events.append(Event(ts="t", actor="flood", scope=Scope("d", "app", "citizen_fog"),
                                action="a", primes=[p], attrs={}, evidence={}))

    # High-ish epsilon (low noise) within budget so we can inspect the bound.
    out = segment_summary(events, default_policy(), epsilon=6.0, seed=0,
                          max_contribution=2, k_anonymity=1, budget=50.0)
    assert out["status"] == "RELEASED"
    # The flooder contributes presence to at most max_contribution (2) prime cells,
    # so it cannot inflate all five. FOUNDER is anchored by 10 honest actors.
    assert out["privacy"]["clipped_actors"]["by_prime"] == 1
    # With low noise, FOUNDER ~ 10 or 11 (honest actors), never ~60.
    assert out["counts_by_prime"]["FOUNDER"] <= 13


def test_no_raw_identifiers_in_release():
    import json
    ev = _population()
    out = segment_summary(ev, default_policy(), epsilon=2.0, seed=5)
    blob = json.dumps(out).lower()
    assert "device_id" not in blob
    assert "dev00" not in blob
