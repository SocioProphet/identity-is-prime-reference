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
* **Mechanism.** Pure epsilon-DP (delta = 0) via the Laplace mechanism, scale =
  sensitivity / epsilon, applied per surviving cell.
* **k-anonymity suppression** runs on TRUE counts *before* release: any cell
  describing fewer than ``k_anonymity`` actors is withheld entirely — it is
  never noised-and-released. Small cells are refused, not leaked.
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
    k_anonymity: int,
    rng: random.Random,
) -> Tuple[Dict[str, int], List[str]]:
    """k-anonymity-suppress then Laplace-privatise a per-cell count histogram.

    Returns ``(released_counts, suppressed_cell_keys)``. Cells with a TRUE count
    below ``k_anonymity`` are suppressed (never released). Surviving cells get
    Laplace(sensitivity/epsilon) noise, clamped to >= 0 and rounded to int.
    """
    if epsilon <= 0.0:
        raise ValueError("epsilon must be > 0 for a private release")
    scale = float(sensitivity) / float(epsilon)
    released: Dict[str, int] = {}
    suppressed: List[str] = []
    for cell in sorted(true_counts):
        true_c = true_counts[cell]
        if true_c < k_anonymity:
            suppressed.append(cell)
            continue
        noisy = true_c + laplace_noise(rng, scale)
        released[cell] = max(0, int(round(noisy)))
    return released, suppressed


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
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)

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
