# Worked example: “Michael” in the citizen fog (synthetic data)

This example is intentionally **fake data**. It’s designed to demonstrate the model mechanics.

We simulate a person (“Michael”) living in the *fog*:
* some events happen on-device (browser, apps),
* some happen in a “citizen cloud” (their own encrypted sync),
* some touch institutional systems (health portal),
* and some touch commercial systems (ad-tech).

Our job is to:
1) build an entity graph that is accurate **and** safe, and  
2) prove that certain identity primes (e.g., *patient*) never leak into forbidden scopes.

---

## 1) Prime topics for Michael

We define a prime-topic basis:

* \(p_1\): Founder/Builder  
* \(p_2\): Patient  
* \(p_3\): Parent  
* \(p_4\): Citizen  
* \(p_5\): Creator

Each event has a prime mixture \(e \in \mathbb{N}^5\).  
For policy checks we often binarize: \(v \in \{0,1\}^5\).

---

## 2) A privacy policy as constraints

We encode policy at two levels:

### 2.1 Hard (non-negotiable)
* If \(p_2\) (Patient) is active, then:
  * no third-party cookie identifiers may be exported,
  * no ad-tech scope may receive the event,
  * no cross-site tracking features may be attached to the record.

### 2.2 Soft (bounded / auditable)
* Citizen + Patient co-occurrence is permitted only in civic-health contexts (e.g., public health reporting), with explicit consent witnesses.

---

## 3) Synthetic event trace

See: `examples/michael_identity_prime_trace.jsonl`

We include events like:
* HEALTH_PORTAL_LOGIN (primes: Patient+Parent)
* BROWSER_PAGE_VIEW (primes: Patient)
* THIRD_PARTY_PIXEL_FIRE (scope: ad-tech)  ← should be blocked/flagged
* SSO_TOKEN_REPLAY_ATTEMPT (modular nonce evidence)  ← congruence catches
* LOCAL_SYNC_TO_CITIZEN_CLOUD (allowed aggregate export)

---

## 4) Run the toy analyzer

From repo root:

```bash
python -m prime_er.cli analyze \
  --in examples/michael_identity_prime_trace.jsonl \
  --policy examples/policies/default_policy.json \
  --out /tmp/michael_artifact.json
```

Optional: emit a marketer-safe segment summary (privacy-preserving):

```bash
python -m prime_er.cli segment \
  --in examples/michael_identity_prime_trace.jsonl \
  --policy examples/policies/default_policy.json \
  --out /tmp/michael_segment.json
```

Precomputed outputs are also included for convenience:
* `examples/outputs/michael_artifact.json`
* `examples/outputs/michael_segment.json`

---

## 5) Expected outcome (human meaning)

### 5.1 The ER view
The system should still resolve “Michael” across devices/apps when allowed (device_id + email + stable links).

### 5.2 The identity-prime view
The system should reject or flag any event trying to attach ad-tech tracking identifiers to a Patient-labeled event.

### 5.3 The proof view
The proof artifact should contain:
* the claim being checked,
* the evidence atoms used,
* the policy constraints triggered,
* precision metadata,
* a minimal counterexample trace (for violations),
* and a “what would have made it safe” explanation.

---

## 6) Why this example matters

Enterprise ER optimizes for “merge the world correctly.”  
Citizen ER must also optimize for “don’t create identity harm.”

This trace demonstrates the difference:
* The *same* identifiers that help resolution (cookies, device IDs) can also become the channel by which sensitive identity primes leak.
* Our framework makes that channel explicit, constrained, and provable.
