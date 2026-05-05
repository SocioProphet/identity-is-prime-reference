# Platform Identity Contract Adapter

This document defines how the Identity Is Prime reference implementation aligns with the platform-facing identity contracts in `SocioProphet/prophet-platform`.

The short rule is:

```text
Identity Is Prime deep proof artifact
  -> platform IdentityProofIngressRecord
  -> optional IdentitySubjectContext / IdentitySessionContext references
  -> Regis graph deltas and proof attachments
```

Identity Is Prime remains the reasoning and evidence layer. `prophet-platform/contracts/identity/` remains the platform-facing contract layer. Regis remains the graph materialization layer.

---

## 1. Purpose

The Identity Is Prime reference implementation produces richer evidence than a platform ingress record should carry directly. It tracks prime-topic support, policy judgments, bounded-linkage judgments, counterexamples, precision metadata, and replay context.

`IdentityProofIngressRecord.v0.1.json` is intentionally narrower. It records whether a proof ingress was accepted, rejected, or inconclusive for platform consumption.

Therefore, this adapter must preserve both layers:

- the full proof artifact remains available as evidence,
- the platform receives a normalized ingress summary,
- graph consumers receive deltas and artifact references rather than raw proof internals.

---

## 2. Contract roles

### 2.1 Deep proof artifact

Owned by this repo.

It should contain:

- proof artifact id,
- claim block,
- input hashes,
- domains used,
- policy judgment,
- bounded-linkage judgment,
- counterexamples,
- precision mode,
- signatures or future signature envelope.

This artifact is evidence-rich and may be too detailed for platform ingress.

### 2.2 `IdentityProofIngressRecord`

Owned by `prophet-platform/contracts/identity/`.

It carries the platform-facing ingress result:

- `proof_record_id`,
- `proof_source`,
- `tenant_id`,
- `received_at`,
- `result`,
- optional `subject_id`,
- optional `issuer_ref`,
- optional `assurance_context`,
- optional `evidence_refs`,
- optional `correlation_id`.

### 2.3 `IdentitySubjectContext`

Owned by `prophet-platform/contracts/identity/`.

It represents normalized subject context after proof normalization. Identity Is Prime may contribute proof refs and policy refs into this context, but should not redefine the subject contract.

### 2.4 `IdentitySessionContext`

Owned by `prophet-platform/contracts/identity/`.

It represents first-party session context for platform consumers. Identity Is Prime may provide proof refs, evidence refs, and risk/step-up signals, but should not redefine the session contract.

### 2.5 Regis graph delta

Owned by the Regis graph contract.

It materializes proof, policy, identity, and relationship consequences as graph nodes and edges.

---

## 3. Mapping: deep artifact to proof ingress record

The adapter function should have this conceptual signature:

```python
def to_identity_proof_ingress_record(proof_artifact: dict) -> dict:
    ...
```

### 3.1 Required mapping

| Deep proof artifact | IdentityProofIngressRecord |
|---|---|
| `artifact_id` | `proof_record_id` |
| `producer.repo` / `artifact_class` | `proof_source` mapping input |
| `claim.subject_ids[0]` | `subject_id` when available |
| tenant from input/config | `tenant_id` |
| `created_at` | `received_at` |
| `result.status` | `result` |
| `claim.claim_id` | `correlation_id` or `evidence_refs[]` |
| `artifact_id` | `evidence_refs[]` |

### 3.2 Result mapping

The platform result enum is:

```text
accepted | rejected | inconclusive
```

The Identity Is Prime result enum may be richer:

```text
PROVED | VIOLATION | BLOCKED | INCONCLUSIVE
```

Use this mapping:

| IIP result | Platform result |
|---|---|
| `PROVED` | `accepted` |
| `VIOLATION` | `rejected` |
| `BLOCKED` | `rejected` |
| `INCONCLUSIVE` | `inconclusive` |

`BLOCKED` maps to `rejected` because the attempted proof ingress or flow is not accepted by the platform. The detailed reason remains in the evidence artifact.

### 3.3 Proof source mapping

`IdentityProofIngressRecord` currently permits:

- `first_party_passkey`,
- `enterprise_oidc`,
- `enterprise_saml`,
- `workload_identity`,
- `recovery_flow`.

Identity Is Prime may not always fit these categories. Until the platform enum expands, the adapter must choose the closest configured source and preserve the true artifact class in `assurance_context` or `evidence_refs`.

Recommended default mapping for toy/reference examples:

```text
human local/fog proof -> first_party_passkey
enterprise/federated proof -> enterprise_oidc or enterprise_saml
service or agent proof -> workload_identity
recovery proof -> recovery_flow
```

---

## 4. Adapter output example

Given a deep proof artifact:

```json
{
  "artifact_id": "proof:identity_is_prime_demo:001",
  "artifact_class": "EXPORT_BLOCK",
  "created_at": "2026-01-01T09:05:01Z",
  "claim": {
    "claim_id": "claim:identity_is_prime_demo:001",
    "subject_ids": ["pseudo:michael_local_001"]
  },
  "result": {
    "status": "VIOLATION"
  }
}
```

The platform adapter may emit:

```json
{
  "version": "0.1",
  "proof_record_id": "proof:identity_is_prime_demo:001",
  "proof_source": "first_party_passkey",
  "subject_id": "pseudo:michael_local_001",
  "tenant_id": "tenant:local-demo",
  "received_at": "2026-01-01T09:05:01Z",
  "result": "rejected",
  "assurance_context": {
    "source_artifact_class": "EXPORT_BLOCK",
    "source_result": "VIOLATION"
  },
  "evidence_refs": [
    "proof:identity_is_prime_demo:001",
    "claim:identity_is_prime_demo:001"
  ],
  "correlation_id": "claim:identity_is_prime_demo:001"
}
```

---

## 5. Subject and session context alignment

Identity Is Prime must not invent incompatible subject or session models.

When producing downstream context:

- use `IdentitySubjectContext` for normalized subject/tenant/assurance state,
- use `IdentitySessionContext` for session state,
- refer to deep proof artifacts through `proof_refs` and `evidence_refs`,
- refer to policy material through `policy_refs`.

### 5.1 Subject context production

A subject context may be produced only after proof normalization. The adapter should preserve:

- subject id,
- subject class,
- tenant id,
- assurance level,
- proof refs,
- credential refs when available,
- policy refs.

### 5.2 Session context production

A session context may reference the same proof artifacts through `assurance_context.proof_refs` and `evidence_refs`.

Identity Is Prime may inform `risk_state` and `stepup_state`, but the platform owns the session contract.

---

## 6. Regis graph alignment

For every platform ingress record produced, the reasoning layer may also emit a Regis graph delta.

Recommended materialization:

- `IdentityProofIngressRecord` -> `PROOF_INGRESS_RECORD` graph node,
- deep proof artifact -> `PROOF_ARTIFACT` graph node,
- subject context -> `PERSON`, `PSEUDONYM`, `ROLE`, `ORG`, or `SERVICE_WORKLOAD` graph node family,
- session context -> `SESSION` graph node,
- relation between proof ingress and deep artifact -> `ATTESTED_BY_PROOF` edge,
- relation between subject/session and proof -> `ATTESTED_BY_PROOF` edge.

Regis should not recompute the proof. It should materialize the proof consequence and preserve the evidence references.

---

## 7. Validation expectations

A complete adapter validation path should check:

1. deep proof artifact validates against the IIP proof artifact schema,
2. generated `IdentityProofIngressRecord` validates against `prophet-platform/contracts/identity/IdentityProofIngressRecord.v0.1.json`,
3. optional subject/session contexts validate against the platform contracts,
4. graph deltas validate against Regis schemas,
5. evidence refs are stable and non-empty.

The adapter must fail closed if required platform fields cannot be produced.

---

## 8. Migration order

Use this migration order:

1. add deep proof artifact schema and examples,
2. add this adapter doc,
3. add `to_identity_proof_ingress_record()` helper,
4. add platform contract fixture examples,
5. add validation tests against the copied or vendored platform schemas,
6. add graph delta emission after proof-ingress compatibility is stable.

---

## 9. Claim boundary

This adapter does not make Identity Is Prime a full authentication runtime.

It only says:

- given a proof artifact,
- produce a platform-facing ingress record,
- preserve evidence refs,
- and optionally produce graph materialization deltas.

Authentication, session storage, passkey UX, enterprise federation, and machine identity issuance remain platform/runtime concerns.

---

## 10. Practical reading

In plain language:

- the deep proof artifact explains what happened,
- the platform ingress record says whether the platform accepted it,
- the subject/session contexts say what the platform may use,
- and Regis preserves the evidence as graph state.

That is the adapter boundary.
