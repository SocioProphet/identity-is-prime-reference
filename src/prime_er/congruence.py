from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from typing import Optional, Tuple


@dataclass(frozen=True)
class ModClass:
    """Congruence class: x ≡ r (mod m)."""
    m: int
    r: int

    def __post_init__(self) -> None:
        if self.m <= 0:
            raise ValueError("m must be positive")
        object.__setattr__(self, "r", self.r % self.m)

    def holds(self, x: int) -> bool:
        return (x - self.r) % self.m == 0


def _egcd(a: int, b: int) -> Tuple[int, int, int]:
    """Extended gcd: returns (g, x, y) with ax + by = g."""
    if b == 0:
        return (abs(a), 1 if a >= 0 else -1, 0)
    g, x1, y1 = _egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)


def _inv_mod(a: int, m: int) -> Optional[int]:
    """Multiplicative inverse of a mod m, if gcd(a,m)=1."""
    g, x, _ = _egcd(a, m)
    if g != 1:
        return None
    return x % m


def solve_linear_congruence(delta: int, rhs: int, m: int) -> Optional[int]:
    """Solve delta * k ≡ rhs (mod m). Return smallest nonnegative k if solvable.

    Special case:
      * if delta ≡ 0 (mod m), then solvable iff rhs ≡ 0 (mod m), and k=0 is a valid witness.
    """
    if m <= 0:
        raise ValueError("m must be positive")
    delta = delta % m
    rhs = rhs % m
    if delta == 0:
        return 0 if rhs == 0 else None

    g = gcd(delta, m)
    if rhs % g != 0:
        return None
    delta_p = delta // g
    rhs_p = rhs // g
    m_p = m // g
    inv = _inv_mod(delta_p, m_p)
    if inv is None:
        return None
    return (inv * rhs_p) % m_p


@dataclass(frozen=True)
class NonceStream:
    """A modular arithmetic stream: n_{i+1} = n_i + delta (mod m)."""
    base: int
    delta: int
    m: int
    max_steps: int = 1000  # bound avoids pathological long-range false positives

    def steps_to(self, x: int) -> Optional[int]:
        """Return minimal steps k s.t. x ≡ base + k*delta (mod m), if k<=max_steps."""
        rhs = (x - self.base) % self.m
        k0 = solve_linear_congruence(self.delta, rhs, self.m)
        if k0 is None:
            return None
        if k0 <= self.max_steps:
            return k0
        return None

    def reachable(self, x: int) -> bool:
        return self.steps_to(x) is not None

    # Back-compat helpers used in early drafts/tests
    def compatible(self, x: int) -> bool:
        return self.reachable(x)

    def distance(self, x: int) -> Optional[int]:
        return self.steps_to(x)
