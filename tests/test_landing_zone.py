from __future__ import annotations

import pytest

from prime_er.event import Event
from prime_er.policy import default_policy
from prime_er.landing_zone import (
    RecommendationObject,
    Surface343,
    load_naming_grammar,
    load_prime_basis,
    load_surface343_spec,
    load_topic23,
    parse_name,
    recommend,
    render_name,
    semantic_layer,
    surface_from_active,
    validate_recommendation,
)


# ── frozen Phase-0 schemas ───────────────────────────────────────────────────
def test_frozen_basis_and_atlas_shapes():
    basis = load_prime_basis()
    assert len(basis) == 23
    primes = [b["prime"] for b in basis]
    assert len(set(primes)) == 23  # distinct primes
    assert load_topic23() == [b["topic"] for b in basis]  # atlas aligns with basis order


def test_surface343_spec_frame_sums_to_49():
    spec = load_surface343_spec()
    f = spec["layer_frame"]
    assert f["topic_cells"] + f["witness_cells"] + f["control_cells"] == spec["cells_per_layer"] == 49
    assert spec["layers"] * spec["cells_per_layer"] == spec["total_trits"] == 343


# ── surface343 ───────────────────────────────────────────────────────────────
def test_surface_from_active_marks_semantic_layer():
    s = surface_from_active(["PATIENT", "PARENT"])
    assert len(s.flat()) == 343
    topics = load_topic23()
    sem = s.layers[3]  # SEMANTIC layer
    assert sem[topics.index("PATIENT")] == 1
    assert sem[topics.index("PARENT")] == 1
    assert sum(sem) == 2  # only the two active topic cells set


def test_surface343_bounds_fail_closed():
    with pytest.raises(ValueError):
        Surface343(tuple([tuple([0] * 49)] * 6))  # only 6 layers
    with pytest.raises(ValueError):
        Surface343(tuple([tuple([0] * 48)] + [tuple([0] * 49)] * 6))  # bad cell count
    with pytest.raises(ValueError):
        Surface343(tuple([tuple([9] + [0] * 48)] + [tuple([0] * 49)] * 6))  # trit out of range


def test_unknown_topic_is_ignored_in_semantic_layer():
    assert sum(semantic_layer(["NOT_A_TOPIC"])) == 0


# ── naming projection round-trip ─────────────────────────────────────────────
def test_name_render_parse_roundtrip():
    assert "grammar" in load_naming_grammar()
    name = render_name("citizen.synthetic.michael", ["health", "family"], 4, "2", "allowed", "l1", "local")
    assert name == "citizen.synthetic.michael[health+family]@e004.p2.allowed+l1#local"
    d = parse_name(name)
    assert d["id_base"] == "citizen.synthetic.michael"
    assert d["topics"] == ["health", "family"]
    assert d["epoch"] == 4 and d["phase"] == "2" and d["state"] == "allowed"
    assert d["lineage"] == "l1" and d["env"] == "local"


def test_parse_rejects_malformed_name():
    with pytest.raises(ValueError):
        parse_name("not-a-surface-name")


# ── Recommendation Object (synergy with the real Policy engine) ──────────────
def test_recommend_from_real_policy_violation_is_high_severity():
    # a Patient-bearing event in an ad realm is a hard violation (the doc's blocked-pixel case).
    ev = Event.from_obj({
        "ts": "2026-08-02T00:00:00Z", "actor": "michael", "action": "THIRD_PARTY_PIXEL_FIRE",
        "scope": {"realm": "ADTECH"}, "primes": ["PATIENT"],
        "attrs": {"third_party_cookie": "abc"},
    })
    violations = default_policy().event_violations(ev)
    assert violations, "expected at least one violation for Patient-in-adtech"
    ro = recommend(violations[0], trace_id="michael-trace", event_kind=ev.action,
                   active_primes=["PATIENT"], blocked_scope="ADTECH")
    assert isinstance(ro, RecommendationObject)
    assert ro.risk["severity"] == "high"
    assert ro.recommendation["action"] == "strip_tracking_and_replay_locally"
    assert ro.rollback["requires_approval"] is True
    assert validate_recommendation(ro.to_dict()) == []
    assert ro.ro_id.startswith("ro:")


def test_ro_id_is_content_addressed():
    v = {"kind": "SENSITIVE_PRIME_IN_AD_REALM", "details": {"realm": "ADTECH"}}
    a = recommend(v, trace_id="t1", event_kind="K", active_primes=["PATIENT"], blocked_scope="ADTECH")
    b = recommend(v, trace_id="t1", event_kind="K", active_primes=["PATIENT"], blocked_scope="ADTECH")
    c = recommend(v, trace_id="t2", event_kind="K", active_primes=["PATIENT"], blocked_scope="ADTECH")
    assert a.ro_id == b.ro_id and a.ro_id != c.ro_id
