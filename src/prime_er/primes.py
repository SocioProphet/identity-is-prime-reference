from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# Small primes are sufficient for toy implementations and pedagogy.
_DEFAULT_PRIMES = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
    31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
]


@dataclass(frozen=True)
class PrimeTopic:
    """An identity 'prime' (irreducible topic/context)."""
    name: str
    prime: int


def default_prime_topics() -> List[PrimeTopic]:
    """Canonical small set used throughout our examples."""
    names = [
        "FOUNDER",   # builder / technical operator
        "PATIENT",   # health context
        "PARENT",    # family / child context
        "CITIZEN",   # civic / public life context
        "CREATOR",   # writing / art context
        # We can add more later without changing the algebra:
        # "STUDENT", "WORKER", "BELIEVER", "FINANCE", ...
    ]
    return [PrimeTopic(n, _DEFAULT_PRIMES[i]) for i, n in enumerate(names)]


def topic_map(topics: Sequence[PrimeTopic]) -> Dict[str, PrimeTopic]:
    return {t.name: t for t in topics}


def encode_topics(active: Iterable[str], topics: Sequence[PrimeTopic]) -> int:
    """Encode a set of active topics into a uniquely factorable integer.

    This makes 'identity is prime' literal: the factorization recovers the topics.
    """
    m = topic_map(topics)
    out = 1
    for name in active:
        if name not in m:
            raise KeyError(f"Unknown prime topic: {name}")
        out *= m[name].prime
    return out


def decode_topics(code: int, topics: Sequence[PrimeTopic]) -> List[str]:
    """Decode a code produced by encode_topics (toy-scale factorization)."""
    if code < 1:
        raise ValueError("code must be a positive integer")
    out: List[str] = []
    remaining = code
    for t in topics:
        while remaining % t.prime == 0:
            out.append(t.name)
            remaining //= t.prime
    if remaining != 1:
        # Not necessarily an error in the wild (could include other primes),
        # but for our controlled examples we treat it as a mismatch.
        out.append(f"UNKNOWN_FACTOR({remaining})")
    return out


def indicator_vector(active: Iterable[str], topics: Sequence[PrimeTopic]) -> List[int]:
    s = set(active)
    return [1 if t.name in s else 0 for t in topics]


def cooccurs(a: Iterable[str], b: Iterable[str]) -> bool:
    sa, sb = set(a), set(b)
    return len(sa.intersection(sb)) > 0
