# Identity Is Prime — Formal Specification

This document is a **technical specification** of our framework. It is written to be:
* precise enough to implement,
* formal enough to audit,
* readable enough to teach.

We use standard mathematical notation. Where we introduce a term, we define it.

---

## 0. Notation

* Let \(\mathbb{N}\) be the natural numbers, \(\mathbb{Z}\) the integers.
* For modulus \(M \in \mathbb{N}\), let \(\mathbb{Z}_M = \mathbb{Z}/M\mathbb{Z}\) be integers modulo \(M\).
* For a set \(X\), \(\mathcal{P}(X)\) is its powerset.
* For vectors \(x,y \in \mathbb{R}^k\), \(x \le y\) means coordinatewise.

---

## 1. Prime topics and identity composition

### 1.1 Prime topics

**Definition 1 (Prime topics).**  
Fix a finite set of *prime topics*
\[
\mathcal{P} = \{p_1,\dots,p_k\}.
\]
Each \(p_i\) is intended to represent an identity-relevant “irreducible” context/role (e.g., *patient*, *parent*, *citizen*, *creator*, *founder*).

Prime topics are not “labels for a database.” They are a **basis** for decomposing the *meaning* of events.

### 1.2 Prime decomposition as a commutative monoid

We model composition of topics as a free commutative monoid.

**Definition 2 (Topic monoid).**  
Let \(\mathbb{N}^k\) be the set of exponent vectors \(e=(e_1,\dots,e_k)\).  
Interpret \(e\) as the multiset
\[
e \equiv \prod_{i=1}^k p_i^{e_i}.
\]
Composition is addition of exponents:
\[
e \oplus e' := e + e'.
\]
The identity element is \(0=(0,\dots,0)\).

This gives a stable, algebraic way to represent “identity mixtures.”

### 1.3 Prime integer encoding

Sometimes we want a *single scalar* that is uniquely factorable.

**Definition 3 (Prime integer encoding).**  
Choose an injective labeling \(\ell:\mathcal{P}\to\mathbb{P}\), where \(\mathbb{P}\) is the set of prime numbers.  
Define the integer encoding
\[
\mathrm{enc}(e) := \prod_{i=1}^k \ell(p_i)^{e_i}.
\]
By unique factorization, \(\mathrm{enc}\) is injective on \(\mathbb{N}^k\).

This makes “identity as prime” literal (not metaphor), and supports:
* compact hashing (via logs or modular reductions),
* controlled disclosure (reveal only selected factors),
* privacy math (release noisy or coarsened factor information).

---

## 2. Scopes, capabilities, and events

### 2.1 Scopes

We treat “where an action occurs” as first-class.

**Definition 4 (Scope).**  
A scope is a structured descriptor:
\[
s := (\text{device}, \text{process}, \text{container}, \text{app}, \text{jurisdiction}, \text{network-class}, \dots).
\]
Scopes form a **partial order** by containment/trust dominance (e.g., HSM \(\prec\) process \(\prec\) container \(\prec\) cloud).

We write \(s \preceq s'\) if \(s'\) is at least as “wide” (less trusted / more exposure).

### 2.2 Capabilities (affine/linear)

We model “things you’re allowed to do” as resources.

**Definition 5 (Capabilities).**  
Capabilities live in a lattice \((\mathcal{C},\sqsubseteq)\) (dominance = “can do at least as much”).  
Some capabilities are **linear** (must be consumed exactly once) or **affine** (at most once).

Examples:
* Linear: “use a signing handle once per protocol step.”
* Affine: “read a private record at most once per consent transaction.”

We denote linear/affine typing judgments informally:
* \(\mathrm{Linear}(c)\), \(\mathrm{Affine}(c)\).

### 2.3 Event-IR

**Definition 6 (Event-IR).**  
An event is a tuple
\[
e = (\mathrm{ts}, \mathrm{actor}, \mathrm{scope}, \mathrm{action}, \mathrm{primes}, \mathrm{features}, \mathrm{evidence})
\]
where:
* \(\mathrm{ts}\) is time (possibly multi-clock: wall, monotonic).
* \(\mathrm{actor}\) is the subject (a person or local pseudonym).
* \(\mathrm{scope}\) is as above.
* \(\mathrm{action}\) is one of a finite event-kind set (login, api_call, key_create, sign, export_attempt, ipc_send, …).
* \(\mathrm{primes}\in \mathbb{N}^k\) is the prime-topic exponent vector for this event.
* \(\mathrm{features}\) is an attribute map (name, email, phone, cookie, device_id, …).
* \(\mathrm{evidence}\) includes modular counters/nonces/handles, hashes, provenance.

---

## 3. Identity resolution as constrained inference

We model entity resolution as building a partition of records/events into entities.

### 3.1 Records and features

Let \(R\) be the set of records. Each record \(r\in R\) carries features \(F(r)\).

We distinguish:
* **stable, exclusive identifiers** (e.g., passport-like tokens, HSM handle namespace tags),
* **stable, non-exclusive** (e.g., last name),
* **unstable** (address, phone),
* **high-frequency attributes** (gender, nationality).

This classification matters because matching must treat “common” features as weak evidence.

### 3.2 Comparators and evidence vectors

For a pair \(r,r'\), define a comparator vector
\[
\phi(r,r') \in \mathbb{R}^d
\]
whose components are feature-level similarity scores (name distance, email exact match, address normalized match, device cookie co-occurrence, etc.).

### 3.3 Boosted scoring (optional but useful)

We use “boosting” as an efficient way to combine many weak comparators.

**Definition 7 (Boosted score).**  
Let \(h_t:\mathbb{R}^d \to \{-1,+1\}\) be weak learners with weights \(\alpha_t\).  
Define
\[
S(r,r') := \sum_{t=1}^T \alpha_t h_t(\phi(r,r')).
\]
Decision thresholds map \(S\) to:
* MATCH,
* POSSIBLE_MATCH,
* POSSIBLY_RELATED,
* UNRELATED.

This is not “ML magic.” It is an additive evidence ledger. It becomes safer when we:
* constrain \(h_t\) to interpretable stumps,
* audit feature contributions,
* apply policy constraints (below) that can veto merges.

### 3.4 Policy-constrained merging (the critical flip)

Classical ER tries to merge whenever evidence is high.  
We must also enforce: **some merges are forbidden** even if evidence is high.

We model this as a constraint satisfaction layer:

**Definition 8 (Merge admissibility).**  
A merge \(r \sim r'\) is admissible iff:
1) the ER evidence is sufficient (principles/score), and  
2) the merge does not violate an identity-prime policy polytope (Section 4), and  
3) the merge preserves non-escape invariants (Section 6) when secrets are involved.

In other words, evidence proposes; policy disposes.

---

## 4. Policies as polytopes over prime-topic mixtures

### 4.1 Identity-mixture state

For a record/event, define the binary topic indicator \(v \in \{0,1\}^k\) by:
\[
v_i = \mathbf{1}[e_i > 0].
\]
(We can also use integer exponents; binary keeps policy simple.)

### 4.2 Safe region as a polytope

**Definition 9 (Policy polytope).**  
A privacy policy induces a (possibly non-convex) set of allowed mixtures.  
We begin with a convex relaxation:
\[
K := \{x \in \mathbb{R}^k \mid A x \le b,\; 0 \le x \le 1\}.
\]
A discrete mixture \(v\in\{0,1\}^k\) is allowed iff \(v \in K \cap \{0,1\}^k\).

Examples:
* “Patient must not co-occur with ad-tech scope” becomes a constraint linking prime topics and scope indicators.
* “Child context cannot be combined with cross-site tracking features” becomes a constraint on (topic × feature) indicators.

### 4.3 Lattice counting (Ehrhart-style) as risk and search bound

Let \(K\) be a rational polytope.

**Definition 10 (Ehrhart counting).**  
The Ehrhart function counts integer points in dilations:
\[
L_K(t) := |tK \cap \mathbb{Z}^k|,\qquad t\in\mathbb{N}.
\]
For rational polytopes, \(L_K(t)\) is a quasi-polynomial in \(t\).

How we use this:
* **Search bounding:** if candidate merges correspond to integer solutions in a constraint polytope, then \(L_K(t)\) bounds complexity.
* **Identity over-determination risk:** fewer allowed lattice states means a person is easier to uniquely identify; too many forbidden states can also force brittle behavior. We want controlled “optionality.”

We do not require exact Ehrhart computation at runtime; we can use:
* volume approximations,
* sampling,
* precomputed archetypes (polytopes with known counts),
* and incremental updates.

---

## 5. Sequence neutrality and self-correction

Real systems are streaming and out-of-order.

**Definition 11 (Sequence neutrality).**  
An ER pipeline is sequence neutral if, for a fixed multiset of records, the resolved entity graph is independent of arrival order (up to isomorphism).

Operationally: when new evidence contradicts earlier merges, the system can **split** entities and revise history without full reload.

Our analyzer implements a practical approximation:
* record provenance and merge reasons,
* allow “unmerge” if a hard-contradiction principle triggers (e.g., stable exclusive IDs conflict),
* schedule reevaluation (Section 7) rather than reevaluating everything always.

---

## 6. Congruence domains for non-escape (HSM + modular evidence)

Attackers love modular arithmetic: wraparound counters, nonces, sequence numbers.

### 6.1 Congruence classes

**Definition 12 (Congruence abstract value).**  
A congruence abstract value is
\[
x \in a\mathbb{Z} + b \pmod m
\]
meaning \(x \equiv b \pmod{\gcd(a,m)}\) and the set is closed under integer shifts by \(a\).

We use products (grids) for tuples \((\text{handle},\text{nonce},\text{ctr},\text{epoch})\).

### 6.2 Non-escape claim

**Claim (Non-escape).**  
If a handle \(h\) is created in HSM scope and is typed as \(\mathrm{NoEscape}(h,\mathrm{HSM})\), then there exists no event trace path where a value congruent with \(h\)’s reserved namespace appears in any scope \(s \not\preceq \mathrm{HSM}\), unless an explicit, audited witness authorizes the move.

This can be checked by:
* congruence constraints (namespace residue classes),
* sharing/alias analysis (MayAlias),
* affine/linear capability discipline (handles cannot be duplicated),
* SMT bit-vector backstops (nightly / triage).

---

## 7. Widenings, boosting, and schedules (base-\(e\) packing)

Abstract interpretation needs termination. Boosting needs stable updates. We schedule both.

### 7.1 Exponential checkpoints

Define checkpoint iterations:
\[
n_j := \lceil e^j \rceil,\quad j=1,2,\dots
\]
We perform expensive reevaluations (widening, global consistency checks) only at checkpoints, giving:
* rapid sensitivity early,
* stability later,
* predictable compute budgets.

### 7.2 Logarithmic buckets for distances

If \(k\) is a step distance (e.g., how far a nonce-stream match is), bucket it by:
\[
b(k) := \left\lfloor \log_\beta(k) \right\rfloor
\]
with base \(\beta=e\) by default.

Buckets are the right granularity for dashboards and for “human-scale” explanations.

---

## 8. Proof artifacts

A proof artifact is the unit we publish and sign.

**Definition 13 (Proof artifact).**  
A proof artifact \(\Pi\) is a structured object containing:
* the claim,
* inputs (hashes, versions),
* domains used (intervals, congruence, NNC, sharing),
* precision mode and deltas,
* witnesses (NoEscape, policy-satisfaction, non-merge constraints),
* any counterexample traces for violations,
* signatures.

Artifacts must be:
* replayable (same seeds/hashes ⇒ same results),
* audit-friendly (explicit explanations),
* composable (can be combined across agents/scopes).

---

## 9. Fog-first deployment and citizen-cloud bridging

We assume:
* the “state space” of a human is distributed across devices/apps/services,
* but identity must remain locally governable.

**Principle.**  
We do inference locally where possible; we export only:
* safe aggregates,
* noisy counts,
* or explicit consent-witnessed disclosures.

This is the difference between a citizen platform and a surveillance platform.
