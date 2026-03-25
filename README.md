# Identity Is Prime — Reference Implementation (Toy, executable)

This repository is an executable reference for our **citizen-first** identity, privacy, and security stack.

It is intentionally small and readable. It is meant to teach and to serve as a seed, not a finished product.

What’s included:

* **Event-IR ingestion** (JSON / JSONL)
* **Fog-first scoping** (`CITIZEN_FOG`, `CITIZEN_CLOUD`, `INSTITUTION`, `ADTECH`, `HSM`)
* **Prime-topic labeling** (identity-as-prime decomposition)
* **Explainable entity resolution (ER)** with a tiny boosting model
  * edges include a `match_key` and top feature contributions
* **Policy veto** on merges and events (prime-topic constraints)
* **Congruence lane** for modular evidence (nonce streams, wraparound-style)
* **Proof artifacts** (structured outputs with diagnostics)

Documentation lives in `docs/`:
* `00_EXEC_SUMMARY.md` — what we built and why
* `20_FORMAL_SPEC.md` — the math and semantics
* `25_HARD_MATH_APPENDIX.md` — deeper formal-methods spine
* `30_ARCHITECTURE_FOG_CITIZEN_CLOUD.md` — fog-first deployment model
* `40_WORKED_EXAMPLE_MICHAEL.md` — a runnable synthetic trace
* `50_SENZING_REVIEW_AND_UPGRADES.md` — what we keep and what we upgrade
* `60_BOOK_SYLLABUS.md` — class/book blueprint

---

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Analyze a synthetic trace and emit a proof artifact
python -m prime_er.cli analyze \
  --in examples/michael_identity_prime_trace.jsonl \
  --policy examples/policies/default_policy.json \
  --out /tmp/michael_artifact.json \
  --validate

cat /tmp/michael_artifact.json | python -m json.tool
```

Optional: marketer-safe aggregates (no actor IDs, no raw identifiers):

```bash
python -m prime_er.cli segment \
  --in examples/michael_identity_prime_trace.jsonl \
  --policy examples/policies/default_policy.json \
  --out /tmp/michael_segment.json \
  --epsilon 2.0 \
  --seed 7
```

---

## What this is / isn’t

✅ A compact, readable specimen you can teach from.  
✅ A foundation for a larger platform (SourceOS + Prophet + proof artifacts).  
✅ A place where ER, formal methods, and privacy policy meet coherently.

❌ Not production-hardened.  
❌ Not a drop-in replacement for enterprise ER engines.  
❌ Not a vetted differential privacy implementation (the “noise” in `segment` is toy).

---

## License

MIT (see `LICENSE`).
