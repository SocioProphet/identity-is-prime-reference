from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


IIP_TO_PLATFORM_RESULT = {
    "PROVED": "accepted",
    "VIOLATION": "rejected",
    "BLOCKED": "rejected",
    "INCONCLUSIVE": "inconclusive",
}

ALLOWED_PROOF_SOURCES = {
    "first_party_passkey",
    "enterprise_oidc",
    "enterprise_saml",
    "workload_identity",
    "recovery_flow",
}


def _as_mapping(artifact: Any) -> Mapping[str, Any]:
    if isinstance(artifact, Mapping):
        return artifact
    if is_dataclass(artifact):
        return asdict(artifact)
    raise TypeError("artifact must be a mapping or dataclass instance")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _first_subject_id(obj: Mapping[str, Any], explicit: str | None) -> str | None:
    if explicit:
        return explicit
    claim = obj.get("claim")
    if isinstance(claim, Mapping):
        subject_ids = claim.get("subject_ids")
        if isinstance(subject_ids, list) and subject_ids:
            return str(subject_ids[0])
    witnesses = obj.get("witnesses")
    if isinstance(witnesses, Mapping):
        subject_id = witnesses.get("subject_id") or witnesses.get("subject")
        if subject_id:
            return str(subject_id)
    return None


def _artifact_id(obj: Mapping[str, Any]) -> str:
    artifact_id = obj.get("artifact_id")
    if artifact_id:
        return str(artifact_id)
    claim = obj.get("claim")
    if isinstance(claim, Mapping):
        claim_id = claim.get("claim_id")
        if claim_id:
            return f"proof:{claim_id}"
    if isinstance(claim, str) and claim:
        return f"proof:{claim}"
    return "proof:identity-is-prime:unknown"


def _claim_id(obj: Mapping[str, Any]) -> str | None:
    claim = obj.get("claim")
    if isinstance(claim, Mapping):
        claim_id = claim.get("claim_id")
        return str(claim_id) if claim_id else None
    if isinstance(claim, str) and claim:
        return f"claim:{claim}"
    return None


def _result_status(obj: Mapping[str, Any]) -> str:
    result = obj.get("result")
    if isinstance(result, Mapping):
        status = result.get("status")
        if status:
            return str(status)
    status = obj.get("status")
    if status:
        return str(status)
    return "INCONCLUSIVE"


def _created_at(obj: Mapping[str, Any], explicit: str | None) -> str:
    if explicit:
        return explicit
    created_at = obj.get("created_at")
    if created_at:
        return str(created_at)
    return _utc_now_iso()


def to_identity_proof_ingress_record(
    artifact: Any,
    *,
    tenant_id: str,
    proof_source: str = "first_party_passkey",
    subject_id: str | None = None,
    received_at: str | None = None,
    issuer_ref: str | None = None,
    upstream_subject: str | None = None,
) -> dict[str, Any]:
    """Convert an Identity Is Prime proof artifact into Prophet Platform's
    IdentityProofIngressRecord.v0.1 shape.

    This adapter intentionally emits the platform-facing summary, not the full
    deep proof artifact. The deep artifact should remain available through
    evidence_refs.
    """

    if proof_source not in ALLOWED_PROOF_SOURCES:
        raise ValueError(f"unsupported proof_source: {proof_source}")
    if not tenant_id:
        raise ValueError("tenant_id is required")

    obj = _as_mapping(artifact)
    artifact_id = _artifact_id(obj)
    claim_id = _claim_id(obj)
    source_status = _result_status(obj)
    platform_result = IIP_TO_PLATFORM_RESULT.get(source_status, "inconclusive")
    resolved_subject = _first_subject_id(obj, subject_id)

    evidence_refs = [artifact_id]
    if claim_id:
        evidence_refs.append(claim_id)

    record: dict[str, Any] = {
        "version": "0.1",
        "proof_record_id": artifact_id,
        "proof_source": proof_source,
        "tenant_id": tenant_id,
        "received_at": _created_at(obj, received_at),
        "result": platform_result,
        "assurance_context": {
            "source_artifact_class": str(obj.get("artifact_class", "legacy_proof_artifact")),
            "source_result": source_status,
        },
        "evidence_refs": evidence_refs,
    }

    if resolved_subject:
        record["subject_id"] = resolved_subject
    if issuer_ref:
        record["issuer_ref"] = issuer_ref
    if upstream_subject:
        record["upstream_subject"] = upstream_subject
    if claim_id:
        record["correlation_id"] = claim_id

    return record
