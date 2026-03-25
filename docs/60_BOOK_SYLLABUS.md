# Course / book blueprint: Identity Is Prime

This is a teaching-first outline. It is organized as a 12-week course (or 12 chapters),
with implementation labs. The goal is to produce operators and builders who can
*reason about identity* with proofs, not vibes.

---

## Learning objectives

By the end, a student can:

1) Build a typed Event-IR from messy real signals (logs, browser traces, app telemetry).  
2) Implement a minimal entity resolution engine with:
   * feature standardization,
   * candidate selection,
   * principled decisions,
   * relationship inference,
   * and order-independent self-correction.  
3) Prove an **identity non-escape** property using congruence + affine/linear resources.  
4) Express identity policies as constraints over prime-topic mixtures and enforce them.  
5) Generate replayable proof artifacts (hashes, seeds, precision deltas).  
6) Deploy fog-first: local inference + safe bridging to citizen cloud.  
7) Explain to non-technical humans why this matters without lying.

---

## Chapter 1 — The problem: identity as an attack surface
* Identity harm vs data breach
* Why “privacy policies” fail as enforcement
* Threat models: tracking, coercion, inference, replay

Lab: build a tiny Event-IR from a browser trace.

---

## Chapter 2 — Entity resolution 101 (what Senzing gets right)
* Features, record library, feature library, candidate selection
* Match outcomes and relationship edges
* Sequence neutrality / self-correction

Lab: implement normalization + candidate retrieval.

---

## Chapter 3 — Principles, not rules
* Why “rules” don’t scale
* Attribute triad: frequency/exclusivity/stability
* Contradiction principles and unmerge

Lab: implement principle table and a contradiction-triggered split.

---

## Chapter 4 — Boosting as an evidence ledger
* Weak learners = small, interpretable comparators
* Additive scores, calibrated thresholds
* When boosting is a footgun (and how policy veto saves you)

Lab: implement AdaBoost stumps over comparator vectors.

---

## Chapter 5 — Identity is prime (the algebra)
* Prime topics as basis
* Free commutative monoid and integer encodings
* Composition and decomposition as operations

Lab: implement prime-topic encoding/decoding.

---

## Chapter 6 — Policies as polytopes
* From “don’t do X” to constraints \(A x \le b\)
* Discrete topic states vs convex relaxations
* Counting states (Ehrhart intuition) as risk metric

Lab: implement a constraint checker + state counting on a small topic set.

---

## Chapter 7 — Abstract interpretation (Hill-inspired backbone)
* Complete lattices, transfer functions, fixpoints
* Widenings for termination
* Product domains: intervals × congruence × sharing

Lab: implement an incremental fixpoint over an event trace.

---

## Chapter 8 — Congruence domains and modular evidence
* \(\mathbb{Z}_n\), residue classes, wraparound
* Why attackers love modular space
* Bounded congruence checks to avoid false positives

Lab: detect nonce-stream leakage with bounded steps.

---

## Chapter 9 — HSM non-escape with affine/linear types
* Linear capabilities for key handles
* NoEscape witnesses and scope dominance
* SMT backstop (BV) for counterexample hunting

Lab: prove non-escape (or emit violation artifact) on a toy HSM trace.

---

## Chapter 10 — Fog-first deployment and citizen cloud
* Local sovereignty
* Consent-witnessed bridging
* Privacy-preserving marketing aggregates

Lab: export marketer-safe segments without exporting identity.

---

## Chapter 11 — Proof artifacts and operator UX
* Precision metadata (Exact / Approx{δ})
* Minimal counterexamples
* Dashboards that teach (not frighten)

Lab: generate a signed-ish artifact (hash chain + JSON schema validation).

---

## Chapter 12 — State of the art, ethics, and “what we are not building”
* Contrast with enterprise ER, data brokers, surveillance
* The line between help and control
* Why education is the distribution strategy

Lab: write a policy for children and show how it blocks cross-context leakage.
