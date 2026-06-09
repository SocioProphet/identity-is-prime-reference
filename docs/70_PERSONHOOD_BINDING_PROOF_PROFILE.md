# Personhood Binding Proof Profile v0.1

## Status

Companion proof-artifact profile for the Identity Is Prime reference implementation.

This document does not replace `20_FORMAL_SPEC.md`. It specializes the existing proof artifact discipline for the case where a governed identity mesh must be bound to a living human subject without collapsing that subject into a wallet, account, portrait, device, credential, agent, graph edge, or reputation score.

## Purpose

Identity Is Prime already treats identity as a composition of irreducible contexts and enforces policy-vetoed merge discipline. Personhood binding adds a higher-level proof profile:

> A personhood binding is a governed continuity claim that a living human subject controls or authorizes an identity mesh, supported by independent evidence classes, consent, recovery, revocation, and replayable receipts.

The profile exists because identifier control is not personhood. A key signs. A wallet signs. A platform account authenticates. A portrait presents. A credential attests. None of these is the person.

## Position in the existing formal model

The base Event-IR model represents events as tuples including timestamp, actor, scope, action, prime-topic vector, features, and evidence. This profile treats a personhood binding ceremony as a structured event trace whose proof artifact can be checked under identity-prime policy.

The base merge discipline says evidence proposes and policy disposes. Personhood binding follows the same rule:

- evidence may support a person-bound continuity claim;
- policy may veto the claim;
- no single object class may establish personhood;
- no proof may silently merge all identity contexts.

## Core definitions

### Personhood subject

A personhood subject is a living human participant in a governed identity mesh. The system may represent the subject with records, identifiers, credentials, and projections, but those records are not the person.

### Personhood binding ceremony

A ceremony is a replayable event bundle with at least:

- subject consent statement;
- scope and non-claims disclosure;
- evidence class collection;
- recovery policy acknowledgement;
- revocation or correction path;
- transition receipt.

### Personhood binding proof artifact

A personhood binding proof artifact extends the base proof artifact with:

- claim: subject `s` is person-bound to identity mesh subject `m` under scope `q`;
- inputs: source hashes, evidence refs, schema versions, policy versions;
- evidence classes: independent classes supporting the claim;
- witnesses: consent, recovery, revocation, non-collapse, and replay witnesses;
- veto diagnostics: explicit reasons if the claim fails;
- signatures or attestations for ceremony participants.

## Evidence classes

Allowed evidence classes are:

- `self_attestation`
- `liveness_or_presence`
- `credential_attestation`
- `guardian_or_witness_attestation`
- `device_key_continuity`
- `account_continuity`
- `recovery_policy`
- `revocation_policy`

The first four are person-facing or institution/witness-facing. The next two are control/continuity evidence. The last two are governance evidence.

## Independence requirement

For assurance level P3 or higher, a personhood binding requires at least three active independent evidence classes.

For P3, the minimum recommended set is:

```text
self_attestation
liveness_or_presence
guardian_or_witness_attestation
recovery_policy
revocation_policy
```

For P4 or higher, add:

```text
credential_attestation
```

This prevents one object from becoming the person by bureaucratic sleight of hand. No wallet monarchs. No face monarchy. No account monarchy. The crown is fake and the goblin knows it.

## Non-collapse rules

A valid personhood binding proof must reject:

1. wallet-only personhood;
2. portrait-only or biometric-only personhood;
3. platform-account-only personhood;
4. device-key-only personhood;
5. credential-only personhood;
6. reputation-only personhood;
7. agent-action-only personhood;
8. graph-inference-only personhood;
9. personhood binding without recovery;
10. personhood binding without revocation or correction.

The rule is:

```text
No personhood binding from a single object class.
```

## Policy polytope interpretation

Let evidence classes be binary indicators:

```text
E_self, E_live, E_cred, E_witness, E_device, E_account, E_recovery, E_revocation
```

For P3+ admissibility, require:

```text
E_self = 1
E_live = 1
E_witness = 1
E_recovery = 1
E_revocation = 1
sum(E_i) >= 3
```

For P4+ admissibility, additionally require:

```text
E_cred = 1
```

Object-only veto:

```text
E_self + E_live + E_cred + E_witness = 0 => veto
```

Missing-governance veto:

```text
E_recovery = 0 or E_revocation = 0 => veto
```

Biometric mandate veto:

```text
biometric_required = 1 => veto
```

Global correlation veto:

```text
public_projection_all_contexts = 1 without explicit consent and policy approval => veto
```

## Relation to IdentitySigilSeal

`IdentitySigilSeal` is downstream of personhood binding.

A sigil is a presentation artifact. It cannot establish personhood. A seal binds presentation, scoped signing authorities, delegation refs, reputation refs, consent policy refs, and transition receipts to an identity mesh. It must reference a valid personhood binding before it may be treated as person-bound presentation.

## Relation to Regis Entity Graph

Regis materializes this profile as graph state. The graph must preserve the distinction between:

- personhood binding;
- identity mesh subject;
- human digital twin reference;
- sigil seal;
- signing authority;
- portrait policy;
- recovery policy;
- reputation credential.

An inferred graph edge must not become a confirmed personhood edge without evidence, policy, and review.

## Relation to Human Digital Twin / HolographMe

HolographMe owns the first executable schema and validation surface for `PersonhoodBindingRecord`. Human Digital Twin should treat personhood-binding export as a governed outward claim requiring readiness, consent, provenance, and minimization.

## Valid proof sketch

A valid P3 proof artifact should include:

```text
claim: pbr_example_alpha person-binds sub_example_alpha to hdt_example_alpha under identity_mesh_root
inputs: schema hashes, policy hashes, evidence refs
classes: self_attestation, liveness_or_presence, guardian_or_witness_attestation, recovery_policy, revocation_policy
witnesses: subject consent, guardian/witness attestation, transition receipt
vetoes: none
non-claims: wallet/account/portrait/device/agent/reputation not person
```

## Rejected proof sketches

Wallet-only:

```text
classes: account_continuity
veto: single object class; missing self_attestation; missing liveness; missing witness; missing recovery; missing revocation
```

Portrait-only:

```text
classes: liveness_or_presence
veto: biometric-only; single object class; missing witness; missing recovery or revocation if absent
```

No recovery:

```text
classes: self_attestation, liveness_or_presence, guardian_or_witness_attestation
veto: missing recovery_policy
```

## Required proof artifact non-claims

Every valid artifact must include equivalent non-claims:

- personhood binding does not make any wallet the person;
- personhood binding does not make any portrait biometric proof by default;
- personhood binding does not make any account the person;
- personhood binding does not expose all identity contexts;
- personhood binding does not erase the human right to correct, revoke, or contest;
- personhood binding does not make any agent action direct human action.

## Non-goals

This profile does not define legal identity proofing.

This profile does not require biometrics.

This profile does not require public real-name identity.

This profile does not authorize global identity correlation.

This profile does not make the proof artifact the person.
