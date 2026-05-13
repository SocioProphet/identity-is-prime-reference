# ER+ Intrinsic Geometry

Status: v0.1 reference implementation spine.

This document adds the ER+ layer to Identity Is Prime. It does not replace the existing Event-IR, prime-topic, policy-polytope, congruence, or proof-artifact model. It makes the entity-resolution layer more explicit by defining the admissible moves that generate record and entity geometry.

## 1. Correct object: path cost, not automatic metric

ER+ uses intrinsic path costs.

A record path cost `D_R(r, r')` is the least discovered cost of transforming record `r` into record `r'`, up to canonicalization, using declared atomic edit generators. An entity path cost `D_E(e, e')` is the least discovered cost of transforming one entity state into another using declared entity moves.

These are not automatically mathematical metrics. They may be asymmetric, partial, or infinite. They become metrics only when the generator set is symmetric, inverse costs are equal, reachable components are connected, and zero-cost paths identify only equivalent canonical states.

Implementation language must therefore use `path_cost`, `quasi_metric`, or `intrinsic_cost` unless a configuration explicitly declares the stronger metric assumptions.

## 2. Record edit algebra

A record is a schema-keyed map. A canonicalization profile maps raw values into canonical comparison values. A record edit generator is a partial, costed transformation over one attribute.

Reference fields:

- `id`
- `attribute`
- `cost`
- `inverse_id`
- `symmetric`
- `canonicalization_profile`
- `policy_scope`
- `evidence_class`

The reference implementation provides a small deterministic generator registry for name aliases, punctuation stripping, email case folding, and phone normalization. Production lanes should replace this with a schema-aware registry trained and audited from real source distributions.

## 3. Record path certificate

A record path certificate records:

- source canonical record
- target canonical record
- reachable / unreachable result
- total path cost
- expanded node count
- ordered edit steps
- generator ids and per-step costs

The path cost may be used as an energy-style feature:

```text
score_R = exp(-lambda_R * D_R)
```

This score is not a posterior probability. It must be calibrated with source priors, base rates, negative-pair evidence, and policy constraints.

## 4. Entity move algebra

An entity state contains:

- entity id
- assigned source record ids
- posterior summary state
- optional graph/policy/certificate pointers

Reference entity moves are:

- `add_record`
- `drop_record`
- `reassign_record`
- `merge_entities`
- `split_entity`
- `posterior_refresh`

The initial implementation uses a deterministic bounded set-difference move plan. This is intentionally simple so conformance fixtures can assert exact paths. Regis and production runners can replace it with bounded graph search or beam search while preserving the certificate shape.

## 5. Local expansion exponent

ER+ uses a finite-graph local expansion exponent:

```text
delta_e(r1, r2) =
  (log(N_e(r2)+epsilon) - log(N_e(r1)+epsilon)) /
  (log(r2) - log(r1))
```

This is a graph diagnostic, not a Hausdorff dimension. It measures local ambiguity and density in the entity graph under the configured path-cost neighborhood.

## 6. Behavioral delay features

Behavioral ER+ features are Takens-inspired delay-coordinate features, not literal dynamical-system reconstruction guarantees. Production identity data is sparse, irregular, and partially observed.

The reference implementation exposes dense delay vectors and sampled symmetric average-min-distance similarity. Later lanes should add irregular-time masks, event-lag windows, wall-clock buckets, and segment-specific parameter selection.

## 7. Neutrality as conformance, not assumption

Sequence neutrality is treated as a replay invariant. For a canonical event order and an admissible reordered event list, the reducer is replayed twice. The run passes when final states are equivalent under the declared tolerance.

Neutrality must be tested, not asserted.

## 8. Boundary with Identity Is Prime

Identity Is Prime policy constraints still govern human identity mixing and prime-topic non-escape. ER+ does not make every graph correlation an identity merge. Defensive/investigative lanes may carry separate evidence edges, but those edges must not be silently promoted into canonical human identity truth.

## 9. Reference implementation files

- `src/prime_er/edit_geometry.py`
- `src/prime_er/entity_geometry.py`
- `src/prime_er/behavior.py`
- `src/prime_er/neutrality.py`
- `schemas/er_plus/ERPlusConfig.v0.1.json`
- `tests/test_er_plus_geometry.py`

## 10. Acceptance criteria

A valid ER+ implementation must:

1. distinguish path costs from true metrics;
2. emit certificates for record and entity path decisions;
3. keep energy scores separate from calibrated posterior claims;
4. label finite-graph expansion as a diagnostic;
5. label delay features as Takens-inspired, not Takens-guaranteed;
6. enforce neutrality through replay tests;
7. preserve Identity Is Prime policy vetoes for human identity merges.
