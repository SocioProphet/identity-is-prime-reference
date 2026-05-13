from __future__ import annotations

import math
from typing import Iterable, Sequence

Vector = tuple[float, ...]


def delay_vectors(values: Sequence[float], *, tau: int = 1, dimension: int = 3) -> list[Vector]:
    """Build deterministic delay-coordinate vectors for dense toy streams."""
    if tau <= 0:
        raise ValueError("tau must be positive")
    if dimension <= 0:
        raise ValueError("dimension must be positive")
    need = (dimension - 1) * tau
    if len(values) <= need:
        return []
    out: list[Vector] = []
    for idx in range(need, len(values)):
        out.append(tuple(float(values[idx - j * tau]) for j in range(dimension)))
    return out


def euclidean(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have equal dimension")
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def average_min_distance(left: Iterable[Sequence[float]], right: Iterable[Sequence[float]]) -> float:
    """Cheap symmetric sampled-Hausdorff-style distance."""
    lvecs = [tuple(map(float, item)) for item in left]
    rvecs = [tuple(map(float, item)) for item in right]
    if not lvecs or not rvecs:
        return math.inf

    def one_way(src: list[Vector], dst: list[Vector]) -> float:
        return sum(min(euclidean(a, b) for b in dst) for a in src) / len(src)

    return 0.5 * (one_way(lvecs, rvecs) + one_way(rvecs, lvecs))


def behavioral_similarity(left: Iterable[Sequence[float]], right: Iterable[Sequence[float]], *, kappa: float = 1.0) -> float:
    """Energy-style behavioral similarity. Not a calibrated posterior."""
    distance = average_min_distance(left, right)
    if math.isinf(distance):
        return 0.0
    return math.exp(-kappa * distance)
