from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List, Optional, Sequence

from .dp import (
    BudgetExhausted,
    PrivacyLedger,
    clamp_contribution,
    release_histogram,
)
from .event import Event
from .policy import Policy
from .primes import default_prime_topics, encode_topics

# Number of independent histograms released (by_prime, by_realm, cohort).
# The total epsilon budget is split across these via sequential composition.
_N_HISTOGRAMS = 3


def _hash_cohort(code: int) -> str:
    # Stable short label for a cohort DEFINITION (not an actor identifier).
    return hashlib.sha256(str(code).encode("utf-8")).hexdigest()[:16]


def _refusal(reason: str, **details: Any) -> Dict[str, Any]:
    return {
        "status": "REFUSED",
        "refusal": {"reason": reason, **details},
        "counts_by_prime": {},
        "counts_by_realm": {},
        "cohorts": [],
    }


def segment_summary(
    events: Sequence[Event],
    policy: Policy,
    *,
    epsilon: Optional[float] = None,
    seed: int = 0,
    max_contribution: int = 2,
    k_anonymity: int = 5,
    min_actors: Optional[int] = None,
    budget: float = 10.0,
    ledger_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Produce a marketer-safe, differentially-private aggregate summary.

    Guarantees (see ``dp.py`` for the threat model):
      * no actor IDs, no raw identifiers — only prime-topic mixture aggregates;
      * person-level (not event-level) contribution bounding;
      * pure epsilon-DP Laplace noise on surviving cells;
      * k-anonymity suppression of small cells on TRUE counts before release;
      * an exhaustible epsilon budget — **fail-closed** when spent.

    Returns a dict with ``status`` in {"RELEASED", "REFUSED"}. On REFUSED, no
    counts are emitted (the refusal surface, not a degraded leak).
    """
    if min_actors is None:
        min_actors = k_anonymity

    # --- Refusal surface: no private release without a positive epsilon. ---
    if not epsilon or epsilon <= 0:
        return _refusal("epsilon_required", note="A positive --epsilon is required for a private release.")

    topics = default_prime_topics()

    # --- Build person-level presence sets (drop ADS: marketing gets context, not tracking). ---
    prime_cells: Dict[str, set] = {}
    realm_cells: Dict[str, set] = {}
    cohort_cells: Dict[str, set] = {}
    ts_values: List[str] = []
    actors: set = set()

    for ev in events:
        actor = ev.actor or "<none>"
        actors.add(actor)
        ts_values.append(ev.ts)
        primes = policy.normalize_primes(ev.primes, ev.scope.realm)
        primes_no_ads = sorted(p for p in primes if p != "ADS")

        for p in primes_no_ads:
            prime_cells.setdefault(actor, set()).add(p)
        realm_cells.setdefault(actor, set()).add(ev.scope.realm)
        if primes_no_ads:
            code = encode_topics(primes_no_ads, topics=topics)
            cohort_cells.setdefault(actor, set()).add(str(code))

    n_actors = len(actors)

    # --- Refusal surface: too few contributors to release anything safely. ---
    if n_actors < min_actors:
        return _refusal(
            "insufficient_actors",
            contributors=n_actors,
            min_actors=min_actors,
            note="Cohort too small to release under the declared privacy floor.",
        )

    # --- Budget: split total epsilon across the histograms (sequential composition). ---
    eps_each = float(epsilon) / _N_HISTOGRAMS
    ledger = PrivacyLedger.load_or_init(ledger_path, total_budget=budget)
    try:
        ledger.spend(float(epsilon), label=f"segment(seed={seed})")
    except BudgetExhausted as e:
        return _refusal(
            "budget_exhausted",
            requested=float(epsilon),
            remaining=ledger.remaining,
            total_budget=ledger.total_budget,
            ledger_ref=ledger_path or "<ephemeral>",
            note=str(e),
        )

    rng = random.Random(seed)

    prime_true, clip_p = clamp_contribution(prime_cells, max_contribution, seed=seed)
    realm_true, clip_r = clamp_contribution(realm_cells, max_contribution, seed=seed + 1)
    cohort_true, clip_c = clamp_contribution(cohort_cells, max_contribution, seed=seed + 2)

    counts_by_prime, supp_p = release_histogram(
        prime_true, epsilon=eps_each, sensitivity=max_contribution, k_anonymity=k_anonymity, rng=rng
    )
    counts_by_realm, supp_r = release_histogram(
        realm_true, epsilon=eps_each, sensitivity=max_contribution, k_anonymity=k_anonymity, rng=rng
    )
    cohort_counts, supp_c = release_histogram(
        cohort_true, epsilon=eps_each, sensitivity=max_contribution, k_anonymity=k_anonymity, rng=rng
    )

    cohorts = [
        {"cohort_id": _hash_cohort(int(code)), "prime_code": str(code), "count": int(cnt)}
        for code, cnt in sorted(cohort_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    return {
        "status": "RELEASED",
        "window": {
            "start_ts": min(ts_values) if ts_values else "",
            "end_ts": max(ts_values) if ts_values else "",
        },
        "counts_by_prime": counts_by_prime,
        "counts_by_realm": counts_by_realm,
        "cohorts": cohorts,
        "privacy": {
            "mechanism": "laplace",
            "delta": 0.0,
            "epsilon_total": float(epsilon),
            "epsilon_per_histogram": eps_each,
            "sensitivity": max_contribution,
            "max_contribution": max_contribution,
            "k_anonymity": k_anonymity,
            "min_actors": min_actors,
            "contributors": n_actors,
            "clipped_actors": {"by_prime": clip_p, "by_realm": clip_r, "cohort": clip_c},
            "suppressed_cells": {
                "by_prime": supp_p,
                "by_realm": supp_r,
                "cohort_count": len(supp_c),
            },
            "budget": {
                "total": ledger.total_budget,
                "spent": ledger.spent,
                "remaining": ledger.remaining,
                "ledger_ref": ledger_path or "<ephemeral>",
            },
            "seed": seed,
            "note": "Person-level epsilon-DP (Laplace) with contribution bounding and k-anonymity suppression.",
        },
    }
