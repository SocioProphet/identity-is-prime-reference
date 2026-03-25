from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Sequence


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


@dataclass
class Diagnostics:
    iter_count: int = 0
    widen_count: int = 0
    duration_ms: int = 0


@dataclass
class ProofArtifact:
    """A replayable, auditable artifact.

    In a production system this should be signed (Cosign/SLSA style), but for
    this toy implementation we include only hashes and structured witnesses.
    """

    claim: str
    status: str  # PROVED | VIOLATION | INCONCLUSIVE

    inputs: Dict[str, Any] = field(default_factory=dict)
    domains: List[str] = field(default_factory=list)

    violations: List[Dict[str, Any]] = field(default_factory=list)
    counterexample: List[Dict[str, Any]] = field(default_factory=list)

    witnesses: Dict[str, Any] = field(default_factory=dict)
    precision: Dict[str, Any] = field(default_factory=dict)
    schedule: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Diagnostics = field(default_factory=Diagnostics)

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d, indent=2, sort_keys=True)

    @staticmethod
    def from_json(s: str) -> "ProofArtifact":
        obj = json.loads(s)
        diag = obj.get("diagnostics", {}) or {}
        obj["diagnostics"] = Diagnostics(**diag)
        return ProofArtifact(**obj)
