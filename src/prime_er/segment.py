from __future__ import annotations

import hashlib
import math
import random
from collections import Counter
from typing import Any, Dict, List, Optional, Sequence

from .event import Event
from .policy import Policy
from .primes import default_prime_topics, encode_topics


def _hash_cohort(code: int) -> str:
    # Stable short hash for cohort IDs (toy; not a cryptographic privacy guarantee).
    return hashlib.sha256(str(code).encode("utf-8")).hexdigest()[:16]


def segment_summary(
    events: Sequence[Event],
    policy: Policy,
    *,
    epsilon: Optional[float] = None,
    seed: int = 0,
) -> Dict[str, Any]:
    """Produce a marketer-safe aggregate summary.

    Design intent:
    * no actor IDs
    * no raw identifiers (emails, cookies)
    * only prime-topic mixture aggregates, optionally with light noise

    NOTE: For real differential privacy, use a vetted DP library and formal threat model.
    """
    topics = default_prime_topics()
    rng = random.Random(seed)

    counts_by_prime = Counter()
    counts_by_realm = Counter()
    cohort_counts = Counter()

    ts_values: List[str] = []
    for ev in events:
        ts_values.append(ev.ts)
        primes = policy.normalize_primes(ev.primes, ev.scope.realm)
        # Drop ADS from cohorts: marketing gets context, not tracking identifiers.
        primes_no_ads = [p for p in primes if p != "ADS"]
        for p in primes_no_ads:
            counts_by_prime[p] += 1
        counts_by_realm[ev.scope.realm] += 1
        code = encode_topics(primes_no_ads, topics=topics)
        cohort_counts[code] += 1

    # Optional toy noise (bounded, deterministic)
    if epsilon and epsilon > 0:
        scale = 1.0 / float(epsilon)

        def noisy(c: int) -> int:
            # Bounded noise in [-scale, +scale]
            noise = (rng.random() - 0.5) * 2.0 * scale
            return max(0, int(round(c + noise)))

        counts_by_prime = Counter({k: noisy(v) for k, v in counts_by_prime.items()})
        counts_by_realm = Counter({k: noisy(v) for k, v in counts_by_realm.items()})
        cohort_counts = Counter({k: noisy(v) for k, v in cohort_counts.items()})

    cohorts = []
    for code, cnt in cohort_counts.most_common():
        cohorts.append({
            "cohort_id": _hash_cohort(code),
            "prime_code": str(code),
            "count": int(cnt),
        })

    return {
        "window": {"start_ts": min(ts_values) if ts_values else "", "end_ts": max(ts_values) if ts_values else ""},
        "counts_by_prime": dict(counts_by_prime),
        "counts_by_realm": dict(counts_by_realm),
        "cohorts": cohorts,
        "privacy": {
            "epsilon": epsilon,
            "seed": seed,
            "note": "Toy bounded noise; use a vetted DP mechanism for production.",
        },
    }
