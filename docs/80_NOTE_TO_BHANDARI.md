# Note to Inderpal Bhandari (draft, in our voice)

Inderpal —

We’re building a personal identity stack that takes a move you’ve made repeatedly in your career: **make complex systems legible by imposing the right orthogonal labels, then make those labels operational**.

ODC did that for defect streams. Advanced Scout-style systems did it for large-scale analytics: surface patterns humans can act on.

We’re doing it for a single human’s digital life — but with two twists:

1) we treat identity as a compositional algebra (prime topics), and  
2) we treat enforcement as proofs (abstract interpretation + typed resources), not dashboards.

## 1) Identity is prime (the idea in one page)

Instead of modeling “a person” as one entity, we model identity as a set of **prime topics** — irreducible roles/contexts:

* Founder/Builder  
* Patient  
* Parent  
* Citizen  
* Creator  

Every event in someone’s life is compiled into a typed Event-IR that carries:
* scope (device/app/cloud/jurisdiction),
* prime-topic mixture (which contexts are active),
* feature atoms (names, emails, cookies, device IDs),
* modular evidence (nonces/counters/handles),
* and capability resources (what can be done).

This lets us do two things simultaneously:
* resolve identity where appropriate (merge records safely), and
* prevent identity harm (forbid sensitive cross-context merges and leaks).

## 2) A worked synthetic example (“Michael”)

Take a person, “Michael,” and a short trace:

1) Health portal login (Patient + Parent)  
2) Browser session on a news site (Citizen)  
3) Third-party pixel fires (AdTech scope)  
4) A shared identifier tries to glue (1) and (3) together (cookie / device graph edge)

Enterprise ER systems would often treat (4) as “useful” because it improves linkage.

We treat (4) as dangerous: it’s trying to merge “patient” context into ad-tech.

So our system:
* still builds a resolved graph for Michael,
* but refuses the cross-context edge (policy polytope veto),
* emits a proof artifact with the minimal counterexample trace and the rule that triggered it.

## 3) Why this is close to your “labeling” instinct

What matters is not the raw data. It’s the controlled vocabulary and the operational semantics.

ODC classifies defects so you can diagnose process signatures.  
We classify events into prime-topic mixtures so you can diagnose identity misuse.

The “colors” here are not visual — they’re identity charges.  
Some combinations are allowed, some must be confined, and some require explicit witnesses.

## 4) The formal-methods spine (Hill-inspired)

Under the hood, we’re doing abstract interpretation over event traces:

* numeric domains (intervals, octagons, NNC polyhedra) for timing/ordering claims  
* congruence domains over \(\mathbb{Z}_n\) for modular artifacts (nonces, wraparound counters, handle namespaces)  
* sharing/escape domains for aliasing and “who can see what”  
* affine/linear resources to prevent silent duplication of secrets/tokens  

Everything terminates via widenings; precision deltas are recorded as part of the artifact.

## 5) Where the novelty sits (and why it matters)

We think the novel combination is this:

*Entity resolution + formal proofs + consumer-first identity policies + fog-first sovereignty.*

Enterprise systems optimize for “correct linkage.”  
Citizen systems must optimize for “safe linkage with provable non-leak guarantees.”

This is the bridge between:
* data strategy and AI, and
* individual autonomy and privacy.

If we get it right, it becomes a new substrate: a person can prove — not claim — that their most sensitive contexts never crossed boundaries.
