"""Ledger-convergence: an identity-is-prime ProofArtifact maps to the CANONICAL estate ProofPack,
validated against the vendored proof-pack schema (prophet-core-contracts, commit 6e8a1647)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from prime_er.proofs import ProofArtifact
from prime_er.proof_pack import to_canonical_proof_pack

SCHEMA = json.loads((Path(__file__).resolve().parent / "fixtures" / "proof-pack.schema.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)


def _art(status="PROVED", epistemic="proved", violations=None):
    return ProofArtifact(claim="michael-safe", status=status, epistemic_level=epistemic,
                         domains=["health", "family"], violations=violations or [])


def _pack(art=None, **over):
    kw = dict(subject_id="citizen.synthetic.michael", signatures=["did:key:z6Mk"], created_at="2026-08-03T00:00:00Z")
    kw.update(over)
    return to_canonical_proof_pack(art or _art(), **kw)


def test_proved_artifact_maps_to_canonical_pack():
    pack = _pack()
    errors = sorted(VALIDATOR.iter_errors(pack), key=lambda e: list(e.path))
    assert errors == [], [e.message for e in errors]
    assert pack["epistemic_level"] == "proved"
    assert pack["ledger"]["algo"] == "sha256"
    assert pack["proof_pack_id"].startswith("proofpack_")


def test_violation_artifact_carries_failing_checks_and_maps_status():
    art = ProofArtifact(claim="patient-in-adtech", status="VIOLATION", epistemic_level="",
                        violations=[{"kind": "SENSITIVE_PRIME_IN_AD_REALM"}])
    pack = _pack(art)
    assert pack["epistemic_level"] == "rejected"  # status→epistemic when unset
    assert any(c["name"] == "SENSITIVE_PRIME_IN_AD_REALM" and c["passed"] is False for c in pack["checks"])
    assert list(VALIDATOR.iter_errors(pack)) == []


def test_unsigned_pack_is_unrepresentable():
    with pytest.raises(ValueError):
        _pack(signatures=[])
