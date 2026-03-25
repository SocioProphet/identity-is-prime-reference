# Senzing (Senzing-style ER) — What it does well, and what we improve

This document does two jobs:

1) reconstruct the key ideas from the Senzing slide deck we were given (schema, pipeline, DB, SDK), and  
2) state our upgrades: how we keep the parts that are timeless and replace the parts that are dated.

We treat Senzing here as a representative of a whole class of enterprise ER systems: strong deterministic ingestion, feature libraries, candidate selection, match principles, a resolved entity graph, and explanation tooling.

---

## 1) Input format and mapping principles

### 1.1 Industry-standard JSON ingestion

Senzing uses a standardized JSON schema (“Generic Entity Specification”) to ingest records.

The core structural components (as presented) are:

* `DATA_SOURCE` (required): source system identifier  
* `RECORD_ID` (recommended): unique record identifier  
* `FEATURES[]` (required): array of feature objects  
* Optional payload attributes (metadata: status, create_date, etc.)

### 1.2 Feature types and the “one feature per object” rule

The slides emphasize:

* “More features = better” (more data per record improves accuracy)
* “One feature per object” (each `FEATURES[]` array item is one feature instance)
* Usage types optional (e.g., HOME, MOBILE, PRIMARY have special meanings)

Feature types shown include (non-exhaustive): name, address, phone, email, DOB, SSN, passport, driver’s license, tax_id, national_id, account, relationship pointer/anchor.

**What we keep:**  
The “one feature per object” design is excellent. It forces normalized ingestion and preserves provenance.

**Our upgrade:**  
We make the feature-object rule *typed* and *provable* in the Event-IR: every feature object becomes a typed atom with stability/exclusivity/frequency metadata (see Section 4 below), and downstream decisions must cite the specific feature atoms used.

---

## 2) SDK operations (what the engine exposes)

The Senzing SDK functionality (as presented) splits into:

### 2.1 Core operations
* `addRecord()` – add new records, resolve entities automatically  
* `updateRecord()` / `replaceRecord()` – update existing records  
* `deleteRecord()` – remove records, update entity graph  
* `reevaluate()` – re-process records with updated rules

### 2.2 Query & search
* `getEntityByRecordID()` – retrieve resolved entity for a record  
* `getEntityByEntityID()` – get full entity details  
* `searchByAttributes()` – search by name/address/attributes  
* `findPathByEntityID()` – discover relationship paths between entities

### 2.3 Advanced capabilities
* `whyEntities()` – explain why records matched  
* `howEntityByEntityID()` – show entity construction history  
* `getVirtualEntity()` – preview resolution without loading  
* `findNetworkByEntityID()` – discover entity networks  
* `exportJSONEntityReport()` – export resolved entities  
* `getStats()` – system statistics

**What we keep:**  
This API division is clean: mutate, query, explain, export, stats.

**Our upgrade:**  
We add:
* proof artifacts (signed explanations with precision metadata),
* policy constraints as first-class inputs (identity primes + privacy polytopes),
* “unmerge” and “explain-unmerge” as first-class operations (sequence neutrality isn’t optional in citizen systems),
* local-first / fog-first controls (export is always consent-witnessed or privacy-preserving aggregate).

---

## 3) Architecture and storage model

### 3.1 Basic architecture

The slides describe the SDK as a library integrated into your application, connecting to a relational database repository.

Key points:
* “fits within your architecture, doesn’t force one on you”
* single-node can use SQLite in-process DB
* wrappers for Java, .NET, Python
* configuration stored as JSON and can be part of DevOps

### 3.2 Supported databases and deployment

Supported RDBMS list shown: PostgreSQL, MySQL, MS SQL Server, SQLite, MariaDB, DB2.

Deployment shown: on-prem, cloud (AWS/Azure/GCP), hybrid, air-gapped, docker.

### 3.3 Clustered databases

Slides state the SDK supports horizontally clustered DB architecture, with some environments using up to five nodes.

### 3.4 “Graph database” at core

Slides emphasize: the core result is an entity-resolved graph:
* nodes = resolved entities
* edges = relationships
* real-time updates
* network analysis ready

**What we keep:**  
The resolved entity graph is the right conceptual output.

**Our upgrade:**  
We treat the graph as:
* **temporal** (versioned over time),
* **policy-constrained** (some edges are forbidden, some require witnesses),
* and **locally sovereign** (a person’s graph is primarily computed/held on their devices, with safe bridging).

We also decouple:
* the event log (append-only, hash-chained),
* the derived graph views (materialized, rebuildable),
* and the proof artifacts (signed, replayable outputs).

---

## 4) Resolution pipeline (and the parts that matter)

The slides lay out a clear, classic pipeline:

1. **Receive and process records**
   * store original record in a record library
   * generate unique ID if source lacks one
   * map and standardize features (including generating variants)
   * store in a feature library
   * compute new features as combinations (e.g., name+DOB)

2. **Identify candidate entities to consider**
   * determine candidate features (ignore generic values like a bank toll-free number)
   * select candidates from the resolved graph

3. **Resolve entities and detect relationships**
   * compare features (same/close/likely/plausible/unlikely)
   * apply principles to decide match/possible-match/related/unrelated
   * “learn something new?” – reevaluate earlier decisions as stats evolve

4. **Update database and respond with outcomes**
   * update graph
   * return response explaining handling
   * process complete

### 4.1 The attribute-triad (frequency, exclusivity, stability)

A key slide assigns each attribute three behaviors:

1) **Frequency:** how many entities share the same value?  
   * F1 (one): SSN/email/passport  
   * FF (few): address/phone  
   * FM (many): date of birth  
   * FVM (very many): gender/nationality

2) **Exclusivity:** should an entity have only one of these?  
   * yes: SSN, DOB, gender (different values suggest different entities)  
   * no: phone numbers, credit cards

3) **Stability:** does the value remain constant over a lifetime?  
   * yes: SSN, DOB  
   * no: address, phone

**What we keep:**  
This triad is gold. It is one of the best “small” ideas in ER because it converts messy reality into a usable prior.

**Our upgrade:**  
We make the triad *typed metadata* carried by each feature atom and used explicitly in:
* candidate selection,
* comparator weighting,
* merge admissibility,
* and unmerge triggers.

---

## 5) Relationship awareness

Slides distinguish:
1) **Disclosed relationships** (told about them): corporate hierarchies, family, co-signers  
2) **Derived relationships** (machine detects): shared addresses, common phone numbers, same email domain, household members  
3) **NORA** (Non-Obvious Relationship Awareness): hidden connections, obfuscation, fraud rings, criminal networks

**What we keep:**  
Relationship awareness is mandatory if you care about fraud, coercion, influence, and context.

**Our upgrade:**  
We treat relationships as *typed edges* with:
* provenance,
* confidence/precision,
* and policy permissions (who is allowed to infer or retain which edges).

In a citizen-first system, relationship inference must be a *controlled power*, not an ambient data exhaust.

---

## 6) Sequence neutrality (real-time self-correction)

Slides define sequence neutrality as producing the same result regardless of arrival order, and self-correcting in real-time when new info makes past decisions wrong (including splitting entities).

**What we keep:**  
Sequence neutrality is a real differentiator; it matters.

**Our upgrade:**  
We formalize it and instrument it:
* every merge is recorded with a witness (why it merged),
* every split cites the contradiction principle that triggered it,
* reevaluations are scheduled with exponential checkpoints (base-e packing),
* and all of this is emitted as proof artifacts (not just JSON blobs).

---

## 7) What makes Senzing “old” for our target, and the concrete upgrades

Senzing is built for enterprise data-fabric patterns: centralized ingestion, organizational ownership, and a lot of implicit trust.

Citizen systems have different physics:
* adversarial client environments,
* cross-app tracking,
* privacy law boundaries,
* “identity harm” as a first-class failure mode,
* and the need for local sovereignty.

Our upgrades are therefore structural:

### 7.1 Proof artifacts instead of explanations
Senzing’s “why” output explains matches. We go further:
* proofs include domains used, precision deltas, and signed witnesses
* we can prove *non-leak* claims, not only explain merges

### 7.2 Policy-constrained ER (identity primes)
We forbid merges and cross-context edges that violate identity policies (prime-topic polytopes).

### 7.3 Congruence + affine/linear types for the attack surface
We treat modular artifacts (nonces, counters, handles, cookies) as the primary attack surface for subtle leakage and replay.

### 7.4 Fog-first architecture (citizen cloud)
We assume the “entity graph of a person” lives primarily on their devices, with consented/aggregated bridging.

### 7.5 Modern candidate selection and comparators
We keep deterministic feature libraries, but:
* add vector/ANN candidate selection (when appropriate),
* add modern address parsing and name transliteration,
* and allow boosting over interpretable weak learners (with veto by policy).

The result is better ER, but more importantly: safer identity.
