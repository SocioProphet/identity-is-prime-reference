from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from typing import Any, Callable, Iterable, Mapping, Sequence

Record = Mapping[str, Any]
CanonicalRecord = tuple[tuple[str, str], ...]


def canonicalize_value(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().casefold()
    while "  " in text:
        text = text.replace("  ", " ")
    digits = "".join(ch for ch in text if ch.isdigit())
    punctuation = set("+()-. ")
    if len(digits) >= 7 and all(ch.isdigit() or ch in punctuation for ch in text):
        return digits
    return text


def canonicalize_record(record: Record, keys: Iterable[str] | None = None) -> CanonicalRecord:
    selected = set(keys) if keys is not None else set(record.keys())
    return tuple(sorted((key, canonicalize_value(record.get(key))) for key in selected))


@dataclass(frozen=True)
class RecordEditGenerator:
    id: str
    attribute: str
    cost: float
    transform: Callable[[Any], Any | None]
    inverse_id: str | None = None
    symmetric: bool = False

    def apply(self, record: Record) -> dict[str, Any] | None:
        if self.attribute not in record:
            return None
        new_value = self.transform(record.get(self.attribute))
        if new_value is None or new_value == record.get(self.attribute):
            return None
        out = dict(record)
        out[self.attribute] = new_value
        return out


@dataclass(frozen=True)
class RecordPathStep:
    generator_id: str
    attribute: str
    before: str
    after: str
    cost: float


@dataclass(frozen=True)
class RecordPathResult:
    source: CanonicalRecord
    target: CanonicalRecord
    reachable: bool
    cost: float
    steps: tuple[RecordPathStep, ...]
    expanded_nodes: int

    @property
    def certificate(self) -> dict[str, Any]:
        return {
            "artifact_type": "RecordPathCertificate",
            "reachable": self.reachable,
            "cost": self.cost,
            "expanded_nodes": self.expanded_nodes,
            "source": list(self.source),
            "target": list(self.target),
            "steps": [step.__dict__ for step in self.steps],
        }


def _nickname(value: Any) -> Any | None:
    aliases = {"mike": "michael", "jon": "john", "johnny": "john", "liz": "elizabeth", "beth": "elizabeth"}
    return aliases.get(canonicalize_value(value))


def _casefold(value: Any) -> Any | None:
    raw = str(value).strip()
    folded = raw.casefold()
    return folded if folded != raw else None


def _digits(value: Any) -> Any | None:
    raw = str(value)
    digits = "".join(ch for ch in raw if ch.isdigit())
    return digits if len(digits) >= 7 and digits != raw else None


def default_record_edit_generators() -> tuple[RecordEditGenerator, ...]:
    return (
        RecordEditGenerator("name.nickname.en", "name", 0.7, _nickname),
        RecordEditGenerator("email.casefold", "email", 0.1, _casefold, symmetric=True),
        RecordEditGenerator("phone.digits", "phone", 0.15, _digits),
    )


def approximate_record_path_cost(
    source: Record,
    target: Record,
    generators: Sequence[RecordEditGenerator] | None = None,
    *,
    keys: Iterable[str] | None = None,
    max_depth: int = 4,
    max_cost: float = 10.0,
    beam_width: int = 512,
) -> RecordPathResult:
    if generators is None:
        generators = default_record_edit_generators()
    source_can = canonicalize_record(source, keys)
    target_can = canonicalize_record(target, keys)
    if source_can == target_can:
        return RecordPathResult(source_can, target_can, True, 0.0, tuple(), 0)

    frontier: list[tuple[float, int, int, dict[str, Any], tuple[RecordPathStep, ...]]] = []
    heapq.heappush(frontier, (0.0, 0, 0, dict(source), tuple()))
    best: dict[CanonicalRecord, float] = {source_can: 0.0}
    expanded = 0
    counter = 0
    while frontier and expanded < beam_width:
        cost, depth, _, record, steps = heapq.heappop(frontier)
        state = canonicalize_record(record, keys)
        if cost > best.get(state, math.inf):
            continue
        expanded += 1
        if state == target_can:
            return RecordPathResult(source_can, target_can, True, round(cost, 10), steps, expanded)
        if depth >= max_depth:
            continue
        for gen in generators:
            next_record = gen.apply(record)
            if next_record is None:
                continue
            next_cost = cost + gen.cost
            if next_cost > max_cost:
                continue
            next_state = canonicalize_record(next_record, keys)
            if next_cost >= best.get(next_state, math.inf):
                continue
            step = RecordPathStep(
                gen.id,
                gen.attribute,
                canonicalize_value(record.get(gen.attribute)),
                canonicalize_value(next_record.get(gen.attribute)),
                gen.cost,
            )
            best[next_state] = next_cost
            counter += 1
            heapq.heappush(frontier, (next_cost, depth + 1, counter, next_record, steps + (step,)))
    return RecordPathResult(source_can, target_can, False, math.inf, tuple(), expanded)


def path_score(result: RecordPathResult, *, lam: float = 1.0) -> float:
    if not result.reachable or math.isinf(result.cost):
        return 0.0
    return math.exp(-lam * result.cost)
