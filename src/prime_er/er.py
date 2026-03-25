from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .boost import BoostModel, default_boost_model
from .event import Event
from .features import compare
from .policy import Policy


@dataclass
class MergeReason:
    kind: str  # MATCH | POSSIBLE_MATCH | BLOCKED
    score: float
    match_key: str
    explanation: List[Dict[str, Any]]


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0]*n

    def find(self, a: int) -> int:
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


def _stable_exclusive_conflict(a: Event, b: Event) -> bool:
    """Hard contradiction principles (toy version)."""
    # Email: stable-ish and often exclusive in consumer contexts
    ea = (a.attrs or {}).get("email")
    eb = (b.attrs or {}).get("email")
    if ea and eb and str(ea).lower() != str(eb).lower():
        return True
    # Phone: can be shared, so not a hard contradiction by default
    return False


def _blocking_tokens(ev: Event) -> Set[str]:
    out: Set[str] = set()
    for k in ("email", "phone", "device_id", "cookie_id"):
        v = (ev.attrs or {}).get(k)
        if v:
            out.add(f"{k}:{str(v).lower()}")
    return out


def resolve_entities(
    events: Sequence[Event],
    policy: Policy,
    model: Optional[BoostModel] = None,
    match_threshold: float = 2.5,
    possible_threshold: float = 1.0,
) -> Tuple[List[int], Dict[Tuple[int,int], MergeReason]]:
    """Resolve events into entity clusters.

    Returns:
      * entity_id per event index
      * pairwise reasons for edges we considered (for explanations)
    """
    if model is None:
        model = default_boost_model()

    n = len(events)
    uf = UnionFind(n)
    reasons: Dict[Tuple[int,int], MergeReason] = {}

    # Blocking index: token -> list of event indices
    index: Dict[str, List[int]] = {}

    for i, ev in enumerate(events):
        # Candidate selection via blocking keys
        candidates: Set[int] = set()
        for tok in _blocking_tokens(ev):
            for j in index.get(tok, []):
                candidates.add(j)

        # Compare only to candidates
        for j in sorted(candidates):
            other = events[j]

            # Principle veto: stable-exclusive conflicts
            if _stable_exclusive_conflict(ev, other):
                reasons[(j, i)] = MergeReason(
                    kind="BLOCKED",
                    score=-999.0,
                    match_key="CONTRADICTION:email",
                    explanation=[{"principle": "stable_exclusive_conflict", "feature": "email"}],
                )
                continue

            feats = compare(ev.attrs, other.attrs)
            score = model.score(feats)
            explanation = model.explain(feats)

            kind = "UNRELATED"
            if score >= match_threshold:
                kind = "MATCH"
            elif score >= possible_threshold:
                kind = "POSSIBLE_MATCH"

            # Policy veto on merges (identity primes)
            if kind == "MATCH":
                if not policy.merge_allowed(ev.primes, other.primes, ev.scope.realm, other.scope.realm):
                    kind = "BLOCKED"

            # Derive a simple match_key: top contributing features
            top = sorted(explanation, key=lambda d: abs(d["contrib"]), reverse=True)[:3]
            mk = "+".join([t["feature"].upper() for t in top if abs(t["contrib"]) > 0.0]) or "NONE"

            reasons[(j, i)] = MergeReason(
                kind=kind,
                score=score,
                match_key=mk,
                explanation=top,
            )

            if kind == "MATCH":
                uf.union(i, j)

        # Update blocking index
        for tok in _blocking_tokens(ev):
            index.setdefault(tok, []).append(i)

    # Normalize entity ids
    root_to_id: Dict[int, int] = {}
    entity_ids: List[int] = []
    next_id = 1
    for i in range(n):
        r = uf.find(i)
        if r not in root_to_id:
            root_to_id[r] = next_id
            next_id += 1
        entity_ids.append(root_to_id[r])

    return entity_ids, reasons
