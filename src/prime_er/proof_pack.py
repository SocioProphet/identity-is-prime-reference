"""Map an identity-is-prime ProofArtifact onto the CANONICAL estate ProofPack
(prophet-core-contracts proof-pack.schema.json) — ledger-convergence migration (#35).

ProofArtifact already carries the sp-core epistemic level; here it becomes the canonical pack's
epistemic_level, its status maps when unset, its violations become failing checks, and a sha256 over
the canonical serialization is the ledger.head. The caller supplies signatures (>=1)."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from .proofs import ProofArtifact

_STATUS_TO_EPISTEMIC = {"PROVED": "proved", "VIOLATION": "rejected", "INCONCLUSIVE": "speculative"}


def to_canonical_proof_pack(
    art: ProofArtifact,
    *,
    subject_id: str,
    signatures: List[str],
    created_at: str,
    claim_mode: str = "fixture_validated",
) -> Dict[str, Any]:
    if not signatures or any(not s for s in signatures):
        raise ValueError("a canonical ProofPack requires >=1 non-empty signature")
    body = art.to_json()
    head = hashlib.sha256(body.encode("utf-8")).hexdigest()
    epistemic = art.epistemic_level or _STATUS_TO_EPISTEMIC.get(art.status, "speculative")

    checks: List[Dict[str, Any]] = []
    for v in art.violations:
        checks.append({"name": str(v.get("kind", "violation")), "passed": False})
    if not checks:
        checks.append({"name": "no_violations", "passed": art.status == "PROVED"})

    return {
        "schema_version": "0.1.0",
        "proof_pack_id": "proofpack_" + head,
        "subject_ref": {"ref_type": "identity_proof", "ref_id": subject_id},
        "claim_mode": claim_mode,
        "epistemic_level": epistemic,
        "ledger": {"algo": "sha256", "head": head},
        "checks": checks,
        "evidence_refs": list(art.domains),
        "signatures": list(signatures),
        "provenance": {"producer": "identity-is-prime.proofs", "claim": art.claim, "status": art.status},
        "created_at": created_at,
    }
