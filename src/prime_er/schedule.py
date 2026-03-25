from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class ScheduleConfig:
    """Scheduling knobs for 'base-e packing' style checkpoints."""
    base: float = math.e
    start_power: int = 1
    max_power: int = 12  # ceil(e^12) ~ 162755; plenty for toy traces


def exp_checkpoints(cfg: ScheduleConfig) -> List[int]:
    """Return iteration indices where expensive global steps should run.

    We use ceil(base^j) for j=start_power..max_power.
    """
    out = []
    for j in range(cfg.start_power, cfg.max_power + 1):
        out.append(int(math.ceil(cfg.base ** j)))
    # Ensure strict monotonicity even if base ~ 1.
    out2 = []
    last = 0
    for n in out:
        if n <= last:
            n = last + 1
        out2.append(n)
        last = n
    return out2


def is_checkpoint(i: int, checkpoints: Iterable[int]) -> bool:
    return i in set(checkpoints)


def log_bucket(k: int, base: float = math.e) -> int:
    """Bucket a positive integer by floor(log_base(k)).

    Used to coarsen distances (e.g., nonce-step distances) into human-scale bins.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    if base <= 1.0:
        raise ValueError("base must be > 1")
    return int(math.floor(math.log(k, base)))
