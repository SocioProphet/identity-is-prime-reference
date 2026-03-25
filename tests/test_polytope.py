from __future__ import annotations

from prime_er.polytope import ForbiddenPairsPolicy, count_allowed_states
from prime_er.primes import default_prime_topics


def test_count_allowed_states_with_forbidden_pairs():
    topics = default_prime_topics()
    # Forbid a real pair within the default set:
    pol = ForbiddenPairsPolicy(forbidden_pairs={frozenset(["PATIENT", "CREATOR"])})
    # Total binary states: 2^5 = 32
    # States containing both PATIENT and CREATOR: 2^(5-2)=8 (the other 3 topics free)
    # Allowed = 32 - 8 = 24
    assert count_allowed_states(topics, pol) == 24
