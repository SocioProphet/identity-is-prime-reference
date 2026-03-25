# Fog-first architecture: citizen cloud, bridges, and marketer-safe outputs

We use “fog” to mean: compute happens close to the person (devices, home hubs, local enclaves),
not only in centralized data centers owned by institutions.

This is not an anti-cloud ideology. It’s an identity-safety design:

* The most sensitive inferences happen locally.
* Only controlled, auditable projections leave the person’s boundary.

---

## 1) Components

### 1.1 SourceOS (local sovereignty)
SourceOS is our hardened operating system layer for individuals. It provides:

* deterministic ingestion into Event-IR
* local feature libraries and identity graphs
* local proof engine (abstract interpretation + ER)
* local policy enforcement (prime-topic polytopes)
* proof artifact signing and replay

### 1.2 Prophet (agentic control)
Prophet is the orchestrator:

* reads proof artifacts and constraints
* blocks disallowed flows
* suggests safe alternatives (e.g., use a different login method, strip tracking features)
* mediates bridging between device, citizen cloud, and external services

### 1.3 Citizen cloud (owned sync, not institutional capture)
Citizen cloud is:
* encrypted, user-controlled synchronization of the identity graph and artifacts
* provenance-preserving, hash-chained logs
* portable across devices
* able to run in a personal account, a family enclave, or a community cooperative

---

## 2) Bridging to institutions (seamless, but protective)

We do need bridges:
* schools, hospitals, banks, government portals, social platforms
* are real parts of modern life

But we treat bridging as a controlled action:

* events crossing into institutional domains are labeled with prime topics and scope
* we enforce constraints that prevent unrelated primes from being glued together
* consent witnesses are recorded when disclosure is intentional
* violations generate proofs, not merely alerts

---

## 3) How this helps marketers (without selling the person)

The world needs commerce. The question is: can commerce exist without identity harm?

We think yes, if we change what “marketing data” means.

### 3.1 Marketer-safe aggregates
Instead of exporting raw identity features, we export:

* topic-level interest signals (coarsened prime mixtures)
* noisy counts (DP-style budgets)
* bounded cohorts with k-anonymity guarantees
* time-windowed summaries (no long-term stitching keys)

Marketing can still answer:
* “what fraction of people in this region are interested in math games?”
* “which lesson modules correlate with retention?”
* “what creative themes resonate with families this month?”

…without learning:
* who a specific child is,
* what their health situation is,
* or how to stitch their identity across contexts.

### 3.2 Proof artifacts as trust infrastructure
Marketers (and regulators) can receive:
* signed statements about what the platform did not export,
* how segmenting was computed,
* and what privacy budget was spent.

This turns “trust us” into auditable math.

---

## 4) Why fog placement matters

If the identity graph is built in the cloud:
* the cloud operator becomes a default data broker

If the identity graph is built in the fog:
* the person becomes the default governor

We can still bridge, sync, and collaborate — but sovereignty starts at the edge.
