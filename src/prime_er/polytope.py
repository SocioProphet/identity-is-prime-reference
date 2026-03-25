from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from .primes import PrimeTopic


@dataclass(frozen=True)
class ForbiddenPairsPolicy:
    """A minimal discrete-policy model: forbid co-occurrence of topic pairs."""
    forbidden_pairs: Set[frozenset]

    def allowed(self, active: Iterable[str]) -> bool:
        s = set(active)
        for pair in self.forbidden_pairs:
            if pair.issubset(s):
                return False
        return True


def enumerate_topic_states(topics: Sequence[PrimeTopic]) -> List[Tuple[List[str], List[int]]]:
    """Enumerate all binary topic states (subsets) for a small topic set."""
    names = [t.name for t in topics]
    out = []
    for bits in itertools.product([0, 1], repeat=len(names)):
        active = [names[i] for i, b in enumerate(bits) if b == 1]
        out.append((active, list(bits)))
    return out


def count_allowed_states(topics: Sequence[PrimeTopic], policy: ForbiddenPairsPolicy) -> int:
    cnt = 0
    for active, _ in enumerate_topic_states(topics):
        if policy.allowed(active):
            cnt += 1
    return cnt
