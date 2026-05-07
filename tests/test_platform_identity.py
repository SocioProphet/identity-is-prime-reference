from __future__ import annotations

import json
from pathlib import Path

from prime_er.platform_identity import to_identity_proof_ingress_record
from prime_er.proofs import ProofArtifact


def test_to_identity_proof_ingress_record_from_legacy_artifact():
    artifact = ProofArtifact(
        claim="identity_is_prime_demo",
        status="VIOLATION",
        inputs={"events_sha256": "abc"},
    )

    record = to_identity_proof_ingress_record(
        artifact,
        tenant_id="tenant:local-demo",
        subject_id="pseudo:michael_local_001",
        received_at="2026-01-01T09:05:01Z",
    )

    assert record["version"] == "0.1"
    assert record["proof_record_id"] == "proof:identity_is_prime_demo"
    assert record["proof_source"] == "first_party_passkey"
    assert record["subject_id"] == "pseudo:michael_local_001"
    assert record["tenant_id"] == "tenant:local-demo"
    assert record["received_at"] == "2026-01-01T09:05:01Z"
    assert record["result"] == "rejected"
    assert record["assurance_context"]["source_result"] == "VIOLATION"
    assert "proof:identity_is_prime_demo" in record["evidence_refs"]
    assert "claim:identity_is_prime_demo" in record["evidence_refs"]


def test_platform_example_matches_adapter_shape():
    repo = Path(__file__).resolve().parents[1]
    example = repo / "examples" / "platform" / "identity_proof_ingress_record.from_michael.example.json"
    obj = json.loads(example.read_text(encoding="utf-8"))

    required = {
        "version",
        "proof_record_id",
        "proof_source",
        "tenant_id",
        "received_at",
        "result",
    }
    assert required <= set(obj)
    assert obj["version"] == "0.1"
    assert obj["result"] == "rejected"
    assert obj["proof_source"] == "first_party_passkey"
    assert obj["tenant_id"] == "tenant:local-demo"
