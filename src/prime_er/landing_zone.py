"""Landing-zone Phase-0 surfaces (Identity-Is-Prime doc §"Schemas to freeze").

The pieces the doc names as Phase-0 deliverables, built over the existing prime/policy/proof
core:

* frozen loaders for ``prime_basis.v1`` / ``topic23.v1`` / ``surface343.v1`` / ``naming_projection.v1``;
* :class:`Surface343` — the 7×49 = 343-trit harmonic surface (bounds-checked packing);
* surface-name projection grammar (:func:`render_name` / :func:`parse_name`, round-tripping) —
  names are DERIVED views, never a source of truth (registry-first);
* :class:`RecommendationObject` + :func:`recommend` — a remediation object generated from a
  policy violation (the RO loop), content-addressed and fail-closed.

Stdlib only. Frozen artifacts live in ``schemas/*.v1.json``.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Sequence

_SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas")


def _load(name: str) -> Dict[str, Any]:
    with open(os.path.join(_SCHEMA_DIR, name), encoding="utf-8") as fh:
        return json.load(fh)


def load_prime_basis() -> List[Dict[str, Any]]:
    """The frozen (topic, prime) basis (``prime_basis.v1``)."""
    return _load("prime_basis.v1.json")["basis"]


def load_topic23() -> List[str]:
    """The frozen 23-topic atlas (``topic23.v1``)."""
    return _load("topic23.v1.json")["topics"]


def load_surface343_spec() -> Dict[str, Any]:
    """The frozen 343-trit surface layout (``surface343.v1``)."""
    return _load("surface343.v1.json")


def load_naming_grammar() -> Dict[str, Any]:
    """The frozen surface-name grammar (``naming_projection.v1``)."""
    return _load("naming_projection.v1.json")


# ── surface343: 7 layers × 49 trits (23 topic + 23 witness + 3 control) ──────────

LAYER_SEMANTIC = 3  # the SEMANTIC layer index in surface343.v1 layer_names


@dataclass(frozen=True)
class Surface343:
    """A 343-trit harmonic surface: 7 layers × 49 trits, each trit in {-1, 0, 1}.

    Validated on construction against the frozen ``surface343.v1`` layout.
    """

    layers: "tuple[tuple[int, ...], ...]"

    def __post_init__(self) -> None:
        spec = load_surface343_spec()
        if len(self.layers) != spec["layers"]:
            raise ValueError(f"surface343 must have {spec['layers']} layers, got {len(self.layers)}")
        allowed = set(spec["trit_values"])
        for i, layer in enumerate(self.layers):
            if len(layer) != spec["cells_per_layer"]:
                raise ValueError(f"layer {i} must have {spec['cells_per_layer']} cells, got {len(layer)}")
            if any(t not in allowed for t in layer):
                raise ValueError(f"layer {i} has a trit outside {sorted(allowed)}")

    def flat(self) -> "tuple[int, ...]":
        """The 343-length flattened vector."""
        return tuple(t for layer in self.layers for t in layer)


def semantic_layer(active_topics: Sequence[str], topics23: "Sequence[str] | None" = None) -> "tuple[int, ...]":
    """One 49-cell layer frame: 23 topic-indicator cells + 23 witness cells + 3 control cells."""
    topics23 = list(topics23) if topics23 is not None else load_topic23()
    idx = {t: i for i, t in enumerate(topics23)}
    topic_cells = [0] * 23
    for t in active_topics:
        if t in idx:
            topic_cells[idx[t]] = 1
    witness_cells = [0] * 23
    control_cells = [0, 0, 0]
    return tuple(topic_cells + witness_cells + control_cells)


def surface_from_active(active_topics: Sequence[str]) -> Surface343:
    """Snapshot surface for an active-topic set: the SEMANTIC layer carries the indicator; the
    other six layers are blank (0) until their producers (accession/trust/…/proof) fill them."""
    blank = tuple([0] * 49)
    layers = [blank] * len(load_surface343_spec()["layer_names"])
    layers[LAYER_SEMANTIC] = semantic_layer(active_topics)
    return Surface343(tuple(layers))


# ── naming projection: names are DERIVED views (registry-first) ──────────────────

_NAME_RE = re.compile(
    r"^(?P<id_base>[^\[]+)\[(?P<topics>[^\]]*)\]@e(?P<epoch>\d+)\.p(?P<phase>[^.]+)"
    r"\.(?P<state>[^+]+)\+(?P<lineage>[^#]+)#(?P<env>.+)$"
)


def render_name(id_base: str, topics: Sequence[str], epoch: int, phase: str, state: str,
                lineage: str, env: str) -> str:
    """Render a surface name per ``naming_projection.v1``:
    ``{id_base}[{topics}]@e{epoch}.p{phase}.{state}+{lineage}#{env}``."""
    if epoch < 0:
        raise ValueError("epoch must be >= 0")
    return f"{id_base}[{'+'.join(topics)}]@e{epoch:03d}.p{phase}.{state}+{lineage}#{env}"


def parse_name(name: str) -> Dict[str, Any]:
    """Parse a surface name back into its fields (inverse of :func:`render_name`)."""
    m = _NAME_RE.match(name)
    if not m:
        raise ValueError(f"not a valid surface name: {name!r}")
    d = m.groupdict()
    return {
        "id_base": d["id_base"],
        "topics": [t for t in d["topics"].split("+") if t],
        "epoch": int(d["epoch"]),
        "phase": d["phase"],
        "state": d["state"],
        "lineage": d["lineage"],
        "env": d["env"],
    }


# ── Recommendation Object: remediation generated from a violation ────────────────

# All three policy violation kinds are hard identity-safety rules (the doc's Patient-safety
# invariants); a forbidden co-occurrence / feature / sensitive-realm leak is high severity.
_HIGH_SEVERITY_KINDS = {"SENSITIVE_PRIME_IN_AD_REALM", "FORBIDDEN_FEATURE_FOR_PRIME", "FORBIDDEN_PRIME_COOC"}


@dataclass
class RecommendationObject:
    ro_id: str
    evidence: Dict[str, Any]
    risk: Dict[str, Any]
    recommendation: Dict[str, Any]
    rollback: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def recommend(violation: Dict[str, Any], *, trace_id: str, event_kind: str,
              active_primes: Sequence[str], blocked_scope: str) -> RecommendationObject:
    """Generate a content-addressed Recommendation Object from a policy violation.

    Fail-closed remediation: a sensitive-prime/forbidden-feature violation is ``high`` severity and
    recommends stripping the offending channel and keeping only a first-party/local flow.
    """
    kind = violation.get("kind", "")
    severity = "high" if kind in _HIGH_SEVERITY_KINDS else "medium"
    reason = f"{kind}: {json.dumps(violation.get('details', {}), sort_keys=True)}"
    if kind in _HIGH_SEVERITY_KINDS:
        action = "strip_tracking_and_replay_locally"
        alternative = "first_party_session_only"
    else:
        action = "review_and_coarsen_projection"
        alternative = "aggregate_only_export"

    body = {
        "trace_id": trace_id, "violating_event": event_kind,
        "active_primes": sorted(active_primes), "blocked_scope": blocked_scope, "kind": kind,
    }
    ro_id = "ro:" + hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return RecommendationObject(
        ro_id=ro_id,
        evidence={"trace_id": trace_id, "violating_event": event_kind,
                  "active_primes": sorted(active_primes), "blocked_scope": blocked_scope},
        risk={"severity": severity, "reason": reason},
        recommendation={"action": action, "alternative": alternative},
        rollback={"restore": "reinstate_prior_policy_snapshot", "requires_approval": True},
        validation={"expected_guardrail_delta": {"privacy_violations": "decrease", "task_success_rate": "unchanged"}},
    )


def validate_recommendation(ro: Dict[str, Any]) -> List[str]:
    """Lightweight structural check against ``recommendation_object.v1`` (stdlib; no jsonschema dep)."""
    problems: List[str] = []
    for key in ("ro_id", "evidence", "risk", "recommendation", "rollback", "validation"):
        if key not in ro:
            problems.append(f"missing '{key}'")
    if isinstance(ro.get("risk"), dict) and ro["risk"].get("severity") not in {"low", "medium", "high", "critical"}:
        problems.append("risk.severity must be low|medium|high|critical")
    for key in ("trace_id", "violating_event", "active_primes", "blocked_scope"):
        if isinstance(ro.get("evidence"), dict) and key not in ro["evidence"]:
            problems.append(f"evidence.{key} required")
    return problems
