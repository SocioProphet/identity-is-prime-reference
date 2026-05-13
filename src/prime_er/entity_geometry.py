from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class EntityState:
    """Minimal ER+ entity state for reference fixtures."""

    entity_id: str
    record_ids: frozenset[str]
    posterior: Mapping[str, Any] | None = None

    @staticmethod
    def of(entity_id: str, record_ids: Iterable[str], posterior: Mapping[str, Any] | None = None) -> "EntityState":
        return EntityState(entity_id, frozenset(record_ids), dict(posterior or {}))


@dataclass(frozen=True)
class EntityMoveStep:
    move_type: str
    record_id: str | None
    cost: float
    reason: str


@dataclass(frozen=True)
class EntityPathResult:
    source_entity_id: str
    target_entity_id: str
    reachable: bool
    cost: float
    steps: tuple[EntityMoveStep, ...]

    @property
    def certificate(self) -> dict[str, Any]:
        return {
            "artifact_type": "EntityMovePathCertificate",
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "reachable": self.reachable,
            "cost": self.cost,
            "steps": [step.__dict__ for step in self.steps],
        }


def _posterior_conflict_cost(source: EntityState, target: EntityState) -> float:
    source_post = dict(source.posterior or {})
    target_post = dict(target.posterior or {})
    cost = 0.0
    for key in sorted(set(source_post) & set(target_post)):
        if source_post[key] != target_post[key]:
            cost += 2.0
    return cost


def approximate_entity_path_cost(
    source: EntityState,
    target: EntityState,
    *,
    add_cost: float = 1.0,
    drop_cost: float = 1.0,
    max_moves: int = 8,
    max_cost: float = 20.0,
) -> EntityPathResult:
    """Approximate D_E with a deterministic set-difference move plan.

    This is a reference implementation. Production Regis lanes may replace it
    with bounded graph search or beam search over proposed merge/split moves.
    """
    steps: list[EntityMoveStep] = []
    current = set(source.record_ids)

    for record_id in sorted(source.record_ids - target.record_ids):
        steps.append(EntityMoveStep("drop_record", record_id, drop_cost, "record_absent_from_target"))
        current.remove(record_id)

    for record_id in sorted(target.record_ids - source.record_ids):
        steps.append(EntityMoveStep("add_record", record_id, add_cost, "record_required_by_target"))
        current.add(record_id)

    conflict_cost = _posterior_conflict_cost(source, target)
    if conflict_cost:
        steps.append(EntityMoveStep("posterior_refresh", None, conflict_cost, "posterior_conflict"))

    total = sum(step.cost for step in steps)
    reachable = frozenset(current) == target.record_ids and len(steps) <= max_moves and total <= max_cost
    return EntityPathResult(
        source.entity_id,
        target.entity_id,
        reachable,
        round(total, 10) if reachable else math.inf,
        tuple(steps) if reachable else tuple(),
    )


def local_expansion_exponent(count_at_r1: int, count_at_r2: int, r1: float, r2: float, *, epsilon: float = 1e-9) -> float:
    """Finite-graph local expansion exponent, not a Hausdorff dimension."""
    if r1 <= 0 or r2 <= 0 or r2 <= r1:
        raise ValueError("radii must satisfy 0 < r1 < r2")
    return (
        math.log(count_at_r2 + epsilon) - math.log(count_at_r1 + epsilon)
    ) / (math.log(r2) - math.log(r1))
