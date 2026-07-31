from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jsonschema import Draft202012Validator  # noqa: E402

from prime_er.event import Event, Scope, load_event_ir  # noqa: E402
from prime_er.policy import default_policy  # noqa: E402
from prime_er.segment import release_to_proof_artifact, segment_summary  # noqa: E402

_REPO = Path(__file__).resolve().parents[1]
_SCHEMA = json.loads((_REPO / "schemas" / "proof_artifact.schema.json").read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_SCHEMA)


def _population():
    return load_event_ir(_REPO / "examples" / "synthetic_population_trace.jsonl").events


def test_released_segment_is_conformant_empirical_claim():
    rel = segment_summary(_population(), default_policy(), epsilon=2.0, seed=3)
    art = release_to_proof_artifact(rel, inputs={"events_path": "x"})
    obj = json.loads(art.to_json())

    errs = sorted(_validator().iter_errors(obj), key=lambda e: list(e.path))
    assert errs == [], [e.message for e in errs]

    assert obj["claim"] == "marketer_safe_segment"
    assert obj["status"] == "PROVED"
    assert obj["epistemicLevel"] == "empirical"
    # The DP warrant travels with the claim.
    assert obj["precision"]["mechanism"] == "laplace+noisy_threshold"
    assert "counts_by_prime" in obj["witnesses"]


def test_refused_segment_is_conformant_inconclusive_claim():
    single = [Event(ts="t", actor="solo", scope=Scope("d", "app", "citizen_fog"),
                    action="a", primes=["FOUNDER"], attrs={}, evidence={})]
    rel = segment_summary(single, default_policy(), epsilon=2.0, seed=0)
    art = release_to_proof_artifact(rel, inputs={"events_path": "x"})
    obj = json.loads(art.to_json())

    errs = sorted(_validator().iter_errors(obj), key=lambda e: list(e.path))
    assert errs == [], [e.message for e in errs]

    assert obj["status"] == "INCONCLUSIVE"
    # No epistemicLevel asserted for a withheld release; no counts leaked.
    assert "epistemicLevel" not in obj
    assert obj["violations"][0]["kind"] == "PRIVACY_REFUSAL"
    assert obj.get("witnesses", {}) == {}


def test_epistemic_level_roundtrips_and_only_valid_enum_passes():
    from prime_er.proofs import ProofArtifact

    art = ProofArtifact(claim="c", status="PROVED", epistemic_level="empirical")
    round = ProofArtifact.from_json(art.to_json())
    assert round.epistemic_level == "empirical"

    bad = json.loads(art.to_json())
    bad["epistemicLevel"] = "totally-made-up"
    errs = list(_validator().iter_errors(bad))
    assert errs, "schema must reject an out-of-enum epistemicLevel"


def test_analyze_style_artifact_without_level_still_conformant():
    from prime_er.proofs import ProofArtifact

    art = ProofArtifact(claim="identity_is_prime_demo", status="PROVED",
                        inputs={"a": 1}, domains=["X"])
    obj = json.loads(art.to_json())
    assert "epistemicLevel" not in obj  # omitted when unspecified
    errs = list(_validator().iter_errors(obj))
    assert errs == [], [e.message for e in errs]
