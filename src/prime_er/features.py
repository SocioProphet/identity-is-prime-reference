from __future__ import annotations
from typing import Dict, Any, Tuple
import math

def jaccard(a:set[str], b:set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))

def simple_pair_features(r1: Dict[str,Any], r2: Dict[str,Any]) -> Dict[str,float]:
    """Toy pairwise features for ER matching.

    Each record has: emails, phones, cookies, device_ids, names.
    """
    f: Dict[str,float] = {}
    f["email_j"] = jaccard(set(r1.get("emails", [])), set(r2.get("emails", [])))
    f["phone_j"] = jaccard(set(r1.get("phones", [])), set(r2.get("phones", [])))
    f["cookie_j"] = jaccard(set(r1.get("cookies", [])), set(r2.get("cookies", [])))
    f["device_j"] = jaccard(set(r1.get("device_ids", [])), set(r2.get("device_ids", [])))
    # crude name similarity: 1 if normalized equal else 0
    n1 = (r1.get("name","") or "").strip().lower()
    n2 = (r2.get("name","") or "").strip().lower()
    f["name_eq"] = 1.0 if n1 and n1 == n2 else 0.0
    return f


def compare(r1, r2):
    """Alias for simple_pair_features (kept for readability)."""
    return simple_pair_features(r1, r2)

