# Hard math appendix: abstract interpretation + identity primes + counting

This appendix tightens the mathematical spine behind the “Identity Is Prime” framing.

It is not required for basic implementation, but it is required for:
* proving soundness claims,
* understanding precision knobs,
* and publishing the work without handwaving.

---

## A. Abstract interpretation (the soundness contract)

We model a trace-analysis claim as a property of a concrete transition system.

### A.1 Concrete semantics

Let \(\Sigma\) be the set of concrete states.  
Let \(E\) be the set of events.

An event induces a transition relation:
\[
\rightarrow_e \subseteq \Sigma \times \Sigma.
\]

For a trace \(e_1,\dots,e_n\), define the concrete reachability transformer:
\[
F(X) := \{ \sigma' \mid \exists \sigma \in X: \sigma \rightarrow_{e_1} \cdots \rightarrow_{e_n} \sigma'\}.
\]

A safety property is a predicate \(P:\Sigma \to \{\mathsf{true},\mathsf{false}\}\).  
A standard verification goal is:
\[
\forall \sigma \in \mathrm{Reach}: P(\sigma).
\]

### A.2 Abstract domain and Galois connection

Let \((A,\sqsubseteq)\) be an abstract domain (a complete lattice).  
Let \((\mathcal{P}(\Sigma),\subseteq)\) be the concrete domain.

A Galois connection is a pair of monotone maps:
\[
\alpha: \mathcal{P}(\Sigma)\to A,\qquad
\gamma: A\to \mathcal{P}(\Sigma)
\]
such that:
\[
\alpha(X) \sqsubseteq a \iff X \subseteq \gamma(a).
\]

Soundness of an abstract transformer \(F^\sharp:A\to A\) is:
\[
F(X) \subseteq \gamma(F^\sharp(\alpha(X))).
\]

This is the central contract: **we may over-approximate, but we may not miss behaviors.**

### A.3 Fixpoints and termination

For loops/iteration, we compute least fixpoints.  
But exact iteration can diverge (infinite ascending chains).

We use widenings \(\nabla\) to force convergence:
\[
a_{i+1} := a_i \nabla F^\sharp(a_i).
\]

Precision is recovered (optionally) by narrowing steps \(\Delta\).

Our “base-\(e\) schedule” is an operational policy:
* do expensive global widenings at exponentially spaced checkpoints,
* do local cheap updates between checkpoints.

---

## B. Identity primes as an algebra (and why it helps)

### B.1 Topics as a free commutative monoid

Prime topics \(\mathcal{P}\) generate the monoid \(\mathbb{N}^k\) under addition.

This matters because:
* composition is canonical,
* decomposition is canonical,
* and policies can be expressed as constraints over \(\mathbb{N}^k\) or \(\{0,1\}^k\).

### B.2 Integer encoding and controlled disclosure

With \(\ell:\mathcal{P}\to\mathbb{P}\), we map topic states to integers:
\[
\mathrm{enc}(e)=\prod_{i}\ell(p_i)^{e_i}.
\]

Controlled disclosure becomes factor disclosure:
* reveal only selected primes,
* reveal modular reductions,
* reveal hashed buckets of \(\log(\mathrm{enc}(e))\).

This makes “privacy-preserving marketing segmentation” natural:
* marketing gets coarse topic mixtures (e.g., “parent + creator”),
* not raw identity features.

---

## C. Policies as polytopes and counting

### C.1 Discrete policies as constraint satisfaction

Binary topic states \(v \in \{0,1\}^k\) are subject to constraints:
* forbidden pairs,
* cardinality limits,
* realm-coupling constraints.

Even without convexity, this is a tractable form for small \(k\), and learnable for larger \(k\).

### C.2 Convex relaxation and lattice counting

For analysis, we often relax:
\[
K = \{x \in [0,1]^k \mid A x \le b\}.
\]

The discrete feasible set is \(K \cap \{0,1\}^k\).

We use lattice counting intuition (Ehrhart theory) to reason about:
* how many identity mixtures are possible under a policy,
* how much “optionality” a person retains,
* and how likely unique identification becomes.

Even coarse bounds (volume, sampling) are informative.

---

## D. Congruence domains over modular evidence

A congruence abstract value can be viewed as a subgroup/coset structure.

For modulus \(m\), define the equivalence:
\[
x \equiv y \pmod m \iff m \mid (x-y).
\]

Nonce streams are affine progressions modulo \(m\):
\[
n_{t+1} \equiv n_t + \delta \pmod m.
\]

Leak detection becomes a question of solvability:
\[
x \equiv n_0 + k\delta \pmod m
\]
for bounded \(k\).

This is a rare case where security invariants become small-number theory.

---

## E. A category-theoretic reframe (optional, but clarifying)

We can treat:

* objects = scoped states,
* morphisms = events that transform states,
* monoidal product = parallel composition of scopes (device × cloud × institution),
* prime topics = generators of a commutative monoid acting on objects,
* proof artifacts = functorial images of traces into an “evidence category.”

This is not decoration. It helps us separate:
* composition (how systems connect),
* from meaning (what inferences are allowed).

The practical payoff is clean interfaces:
* bridging = explicit morphisms with witnesses,
* policy = subobject constraints,
* proofs = compositional certificates.
