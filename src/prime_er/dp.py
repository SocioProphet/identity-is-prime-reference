from __future__ import annotations

"""Vetted-shape differential privacy primitives for marketer-safe aggregates.

Stdlib-only (no numpy / no third-party DP lib) to honour the estate's
no-bloat, MIT-clean constraint. This replaces the previous *toy* bounded-uniform
noise in ``segment`` with a defensible mechanism and an honest threat model.

Threat model (declared first, per "the system states its own limits"):

* **Neighbouring datasets** differ by the addition/removal of exactly ONE actor
  (person-level, not event-level, privacy).
* **Contribution bounding.** Each actor contributes presence (0/1) to at most
  ``max_contribution`` distinct cells of a histogram. That caps the L1
  sensitivity of the histogram to ``max_contribution``.
* **Mechanism.** Laplace mechanism (scale = sensitivity / epsilon) plus
  **noisy-count thresholding** (a "stability histogram"): a cell is released only
  if its *noised* count clears the threshold. Because the keep/drop decision is
  made on the DP-noised value it is valid post-processing, giving **(epsilon,
  delta)-DP** — thresholding on the *true* count would be data-dependent and leak.
* Small cells are dropped, not leaked; callers publish suppressed *counts*, never
  the suppressed cell keys, and never the RNG seed.
* **Sequential composition.** Releasing several histograms over the same actors
  spends the sum of their epsilons; the caller must budget accordingly.

This is a careful, readable reference. For adversarial production use, swap in a
formally audited engine (OpenDP / Tumult) behind the same interface — the point
of the contract below is that the call site does not change.
"""

import json
import math
import os
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


class BudgetExhausted(Exception):
    """Raised when a release would exceed the declared epsilon budget (fail-closed)."""


def laplace_noise(rng: random.Random, scale: float) -> float:
    """Sample Laplace(0, scale) via inverse-CDF from a seeded RNG.

    Deterministic given ``rng`` state, so releases are replayable.
    """
    if scale <= 0.0:
        return 0.0
    u = rng.random() - 0.5  # in [-0.5, 0.5)
    # Clamp magnitude away from 0.5 so log(1 - 2|u|) stays finite.
    mag = min(abs(u), 0.5 - 1e-12)
    return -scale * math.copysign(1.0, u) * math.log(1.0 - 2.0 * mag)


def clamp_contribution(
    actor_cells: Dict[str, "set[str]"],
    max_contribution: int,
    *,
    seed: int = 0,
) -> Tuple[Dict[str, int], int]:
    """Bound each actor to at most ``max_contribution`` cells, then count actors per cell.

    ``actor_cells`` maps actor -> set of cell keys they are present in.
    Returns ``(true_counts_by_cell, n_clipped_actors)`` where ``true_counts`` is
    the number of *distinct actors* present in each cell after clamping.

    Clamping is deterministic (sorted + seeded) so the release is reproducible.
    """
    if max_contribution < 1:
        raise ValueError("max_contribution must be >= 1")
    rng = random.Random(seed)
    counts: Dict[str, int] = {}
    clipped = 0
    for actor in sorted(actor_cells):
        cells = sorted(actor_cells[actor])
        if len(cells) > max_contribution:
            clipped += 1
            rng.shuffle(cells)
            cells = sorted(cells[:max_contribution])
        for c in cells:
            counts[c] = counts.get(c, 0) + 1
    return counts, clipped


def release_histogram(
    true_counts: Dict[str, int],
    *,
    epsilon: float,
    sensitivity: int,
    threshold: int,
    rng: random.Random,
) -> Tuple[Dict[str, int], List[str]]:
    """Noisy-count thresholding ("stability histogram") -> (epsilon, delta)-DP.

    Adds Laplace(sensitivity/epsilon) noise to each cell, then RELEASES a cell
    only if its **noisy** count meets ``threshold``. The keep/drop decision is
    made on the DP-noised value, so it is valid post-processing of a DP release
    — unlike thresholding on the *true* count, which is data-dependent and leaks
    one bit (whether the true count cleared the floor).

    Returns ``(released_counts, suppressed_cell_keys)``. The suppressed keys are
    for internal accounting/testing only; callers MUST NOT publish them (emitting
    which cells fell below the floor is itself a disclosure — see ``segment.py``,
    which reports suppressed *counts* only).
    """
    if epsilon <= 0.0:
        raise ValueError("epsilon must be > 0 for a private release")
    if threshold < 1:
        raise ValueError("threshold must be >= 1")
    scale = float(sensitivity) / float(epsilon)
    released: Dict[str, int] = {}
    suppressed: List[str] = []
    for cell in sorted(true_counts):
        noisy = true_counts[cell] + laplace_noise(rng, scale)
        if noisy >= threshold:
            released[cell] = max(0, int(round(noisy)))
        else:
            suppressed.append(cell)
    return released, suppressed


def suppression_delta(threshold: int, sensitivity: int, epsilon: float) -> float:
    """Per-cell delta contributed by the noisy-count threshold.

    Upper-bounds the probability that a cell whose presence hinges on a single
    contributing actor is nonetheless released. For Laplace(sensitivity/epsilon)
    and threshold ``tau >= sensitivity``:

        delta <= 0.5 * exp(-epsilon * (tau/sensitivity - 1))

    Below ``sensitivity`` the threshold provides no stability guarantee, so we
    report the trivial bound of 0.5 (the release is effectively epsilon-DP only).
    """
    if epsilon <= 0.0 or threshold <= sensitivity:
        return 0.5
    return 0.5 * math.exp(-epsilon * (float(threshold) / float(sensitivity) - 1.0))


@dataclass
class PrivacyLedger:
    """An exhaustible, optionally-persistent epsilon budget (fail-closed).

    When ``path`` is set the ledger is loaded/saved as JSON so the budget is
    enforced *across* invocations — spend it down and further releases refuse.
    """

    total_budget: float
    spent: float = 0.0
    entries: List[Dict[str, object]] = field(default_factory=list)
    path: Optional[str] = None

    @property
    def remaining(self) -> float:
        return self.total_budget - self.spent

    def can_spend(self, epsilon: float) -> bool:
        return epsilon > 0.0 and (self.spent + epsilon) <= self.total_budget + 1e-12

    def spend(self, epsilon: float, label: str) -> None:
        if not self.can_spend(epsilon):
            raise BudgetExhausted(
                f"epsilon budget exhausted: requested {epsilon:.4f}, "
                f"remaining {self.remaining:.4f} of {self.total_budget:.4f}"
            )
        self.spent += epsilon
        self.entries.append({"label": label, "epsilon": epsilon, "ts": int(time.time())})
        if self.path:
            self.save()

    def to_dict(self) -> Dict[str, object]:
        return {
            "total_budget": self.total_budget,
            "spent": self.spent,
            "remaining": self.remaining,
            "entries": self.entries,
        }

    def save(self) -> None:
        if not self.path:
            return
        # Atomic write: ensure the directory exists, write to a temp file, then
        # os.replace. A crash/disk-full mid-write must not corrupt the ledger and
        # silently disable the fail-closed budget across runs.
        parent = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(parent, exist_ok=True)
        tmp = f"{self.path}.tmp.{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)

    @staticmethod
    def load_or_init(path: Optional[str], total_budget: float) -> "PrivacyLedger":
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            # The stored budget is authoritative once created.
            return PrivacyLedger(
                total_budget=float(obj.get("total_budget", total_budget)),
                spent=float(obj.get("spent", 0.0)),
                entries=list(obj.get("entries", []) or []),
                path=path,
            )
        return PrivacyLedger(total_budget=float(total_budget), spent=0.0, path=path)
