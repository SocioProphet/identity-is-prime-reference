from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .event import Event


def _canon(s: str) -> str:
    return (s or "").strip().upper()


@dataclass(frozen=True)
class Policy:
    """Prime-topic policy + realm/feature constraints.

    This is our minimal 'polytope' layer: veto merges and events that create forbidden
    prime-topic mixtures in sensitive realms.
    """

    forbidden_prime_pairs: Set[frozenset] = field(default_factory=set)
    ad_realm_markers: Tuple[str, ...] = ("ADTECH", "ADS", "MARKETING", "TRACK")
    forbidden_feature_keys_by_prime: Dict[str, Set[str]] = field(default_factory=dict)

    def is_ad_realm(self, realm: str) -> bool:
        r = _canon(realm)
        return any(m in r for m in self.ad_realm_markers)

    def normalize_primes(self, primes: Sequence[str], realm: str) -> Set[str]:
        p = {_canon(x) for x in (primes or []) if _canon(x)}
        if self.is_ad_realm(realm):
            p.add("ADS")
        return p

    def violates_prime_pairs(self, primes: Iterable[str]) -> List[Tuple[str, str]]:
        s = set(primes)
        bad: List[Tuple[str, str]] = []
        for pair in self.forbidden_prime_pairs:
            if pair.issubset(s):
                a, b = sorted(list(pair))
                bad.append((a, b))
        return bad

    def event_violations(self, ev: Event) -> List[Dict[str, Any]]:
        """Return structured violations for a single event."""
        violations: List[Dict[str, Any]] = []
        primes = self.normalize_primes(ev.primes, ev.scope.realm)

        # (1) Prime-pair constraints
        for a, b in self.violates_prime_pairs(primes):
            violations.append({
                "kind": "FORBIDDEN_PRIME_COOC",
                "details": {"pair": [a, b], "primes": sorted(list(primes))},
            })

        # (2) Forbidden feature keys attached to a sensitive prime
        attrs_keys = {_canon(k) for k in (ev.attrs or {}).keys()}
        for p, bad_keys in self.forbidden_feature_keys_by_prime.items():
            if _canon(p) in primes:
                overlap = sorted(list(attrs_keys.intersection({_canon(k) for k in bad_keys})))
                if overlap:
                    violations.append({
                        "kind": "FORBIDDEN_FEATURE_FOR_PRIME",
                        "details": {"prime": _canon(p), "keys": overlap},
                    })

        # (3) Realm-based hard rule: sensitive primes cannot exist in ad realms
        if self.is_ad_realm(ev.scope.realm):
            if "PATIENT" in primes or "PARENT" in primes:
                violations.append({
                    "kind": "SENSITIVE_PRIME_IN_AD_REALM",
                    "details": {"realm": ev.scope.realm, "primes": sorted(list(primes))},
                })

        return violations

    def merge_allowed(self, primes_a: Sequence[str], primes_b: Sequence[str], realm_a: str, realm_b: str) -> bool:
        pa = self.normalize_primes(primes_a, realm_a)
        pb = self.normalize_primes(primes_b, realm_b)
        merged = pa.union(pb)
        return len(self.violates_prime_pairs(merged)) == 0


def default_policy() -> Policy:
    forbidden = {
        frozenset(["PATIENT", "ADS"]),
        frozenset(["PARENT", "ADS"]),
        # Civic can be allowed or not depending on design; we keep it conservative for toy:
        frozenset(["CITIZEN", "ADS"]),
    }
    forbidden_feature = {
        "PATIENT": {"THIRD_PARTY_COOKIE", "AD_ID", "PIXEL_ID"},
        "PARENT": {"THIRD_PARTY_COOKIE", "AD_ID", "PIXEL_ID"},
    }
    return Policy(
        forbidden_prime_pairs=forbidden,
        forbidden_feature_keys_by_prime=forbidden_feature,
    )


def load_policy(path: Optional[str]) -> Policy:
    if not path:
        return default_policy()
    p = Path(path)
    obj = json.loads(p.read_text(encoding="utf-8"))
    forbidden_pairs = set()
    for pair in obj.get("forbidden_prime_pairs", []):
        forbidden_pairs.add(frozenset([_canon(pair[0]), _canon(pair[1])]))
    forbidden_feature: Dict[str, Set[str]] = {}
    for prime, keys in (obj.get("forbidden_feature_keys_by_prime", {}) or {}).items():
        forbidden_feature[_canon(prime)] = {_canon(k) for k in keys}
    markers = tuple(_canon(x) for x in (obj.get("ad_realm_markers", []) or [])) or Policy().ad_realm_markers
    return Policy(
        forbidden_prime_pairs=forbidden_pairs,
        ad_realm_markers=markers,
        forbidden_feature_keys_by_prime=forbidden_feature,
    )
