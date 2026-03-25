# Identity Is Prime — Executive Summary

We are building a personal identity, privacy, and security stack that treats a human’s digital life the way mature systems treat money: as something that must be **accounted for**, **constrained**, **audited**, and **proven**—not merely “monitored.”

The thesis is simple to say and hard to do:

> **Identity is prime.**  
> A person’s identity is not one blob. It is a structured composition of irreducible “prime topics” (roles/contexts) that must not be merged or leaked across scopes without explicit, provable authorization.

Where classical entity resolution (ER) systems (e.g., Senzing-style) aim to unify records into a stable entity graph for organizations, our framework flips the locus of control:

* **Audience:** individuals (including children and families), not enterprises.
* **Compute placement:** citizen devices + fog (“the dispersed computing realm of people”), not centralized institutional silos.
* **Objective:** prevent harmful merges and cross-context leakage by default; prove non-leakage where required; allow controlled sharing only with explicit witnesses.

We unify four lines of work into one coherent framework:

1. **Better-than-Senzing entity resolution**  
   We keep the good parts: feature standardization, candidate selection, principled match decisions, relationship awareness, and sequence-neutral self-correction.  
   We upgrade the weak parts: explainability as a *proof artifact*, modern comparators, careful boosting, and privacy-first deployment.

2. **Hill-inspired abstract interpretation for agentic security**  
   We compile heterogeneous evidence into a typed Event-IR, interpret it through abstract domains (intervals, NNC polyhedra, congruences, sharing/escape), and produce terminating analyses with tunable precision.

3. **HSM non-escape via congruence + affine/linear types**  
   We treat modular IDs, nonces, counters, and namespaces as first-class invariants, then prove secrets and their enabling referents cannot exit their allowed scope—using both abstract interpretation and SMT backstops when needed.

4. **Prime decomposition + polytopes + “zeta-like” counting**  
   Prime topics become composable basis elements. Policies become polytopes over topic-mixture states. Lattice counting (Ehrhart-style) becomes a way to bound the number of identity states a system can force on a person. “Prime-counting” analogues become a way to quantify over-determination (profiling) risk.

The deliverable is not only an algorithm. It is a **platform pattern**:

* **SourceOS:** a security-first OS for individuals.
* **Prophet:** an agent/orchestrator that uses proofs to allow, deny, or synthesize safe alternatives.
* **Proof artifacts:** signed, replayable evidence of what was enforced, with precision metadata.
* **Education-first deployment:** teach humans how identity, privacy, and inference really work—then ship protective defaults.

The rest of this repository contains:
* a formal specification (math + semantics),
* a worked example (synthetic “Michael” trace),
* an implementation sketch (toy analyzer),
* a Senzing review and our improvements,
* a class syllabus for turning this into a course.
