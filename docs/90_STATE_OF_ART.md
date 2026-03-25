# State of the art and where we win (draft)

This section is intentionally candid. It is a working map, not marketing copy.

---

## 1) Enterprise entity resolution (ER)

Typical enterprise ER stacks emphasize:
* centralized ingestion into a canonical repository,
* feature standardization + candidate selection,
* rule/principle-driven or probabilistic matching,
* resolved entity graphs for analytics,
* “why” explanations for merges.

Strengths:
* strong data engineering discipline
* decent explainability
* stable production behavior

Weaknesses (for humans):
* assumes institutional control of the data
* optimizes for linkage, not identity harm minimization
* weak primitives for consent, scope boundaries, and local sovereignty
* often poor at order-independent self-correction without reloads
* rarely produces cryptographically signed, replayable proof artifacts

---

## 2) Privacy tech

### 2.1 Tracker blocking and network privacy
Browser privacy modes, content blockers, VPNs, and privacy relays reduce data exhaust.

But they do not prove:
* that sensitive contexts never leaked
* that identity graphs weren’t built anyway from other channels

### 2.2 Differential privacy and k-anonymity
DP and k-anonymity help when you are exporting aggregates.

But they do not, on their own:
* prevent cross-context identity merges locally
* provide OS-level enforcement
* attach proof artifacts to event-level flows

---

## 3) Formal methods in security

Formal verification excels when:
* the system boundary is well-defined,
* the code is stable,
* and the claim is narrow (protocol correctness, memory safety).

But consumer identity lives in:
* messy event streams,
* heterogeneous apps,
* partial observability,
* adversarial telemetry.

Our key move is to bring formal methods to **event-space**, not only code-space:
* abstract interpretation over Event-IR traces
* terminating analyses with explicit precision metadata

---

## 4) Our combined win

We win by combining:
* ER discipline (feature libraries, candidate selection, relationship graphs)
* formal methods (abstract interpretation + congruence + widenings)
* typed resources (linear/affine capabilities, NoEscape witnesses)
* identity prime algebra + policy polytopes
* fog-first sovereignty and citizen cloud bridging
* proof artifacts as the unit of trust

This combination is rare because it spans communities that don’t normally talk:
* data integration / ER,
* static analysis / abstract interpretation,
* privacy math,
* OS security,
* and consumer product design.

---

## 5) What is not solved yet (and must be solved before “world” scale)

* Worked examples at consumer scale (SSO misuse, cross-site tracking, app SDK leakage)
* Policy UX: humans must set policies without becoming mathematicians
* Performance budgets: proofs must run on devices with battery limits
* Governance: open, auditable rules about what “safe” means for children vs adults
* Robustness: adversarial traces and deliberate obfuscation in the wild
