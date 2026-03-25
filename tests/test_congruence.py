from __future__ import annotations

import sys
from pathlib import Path

# Tests run against the "src" layout without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prime_er.congruence import NonceStream


def test_nonce_stream_compatibility_unbounded_solution_within_bound():
    # Stream: 5, 11, 17, 23, ... (mod 256)
    s = NonceStream(base=5, delta=6, m=256, max_steps=1000)
    assert s.compatible(5)
    assert s.compatible(11)
    assert s.compatible(23)


def test_nonce_stream_compatibility_reject_outside_congruence_class():
    # Values that are not in the same gcd-residue class are impossible.
    # Here gcd(6,256)=2, so x-base must be even.
    s = NonceStream(base=5, delta=6, m=256, max_steps=1000)
    assert not s.compatible(8)


def test_nonce_stream_bounded_solution_rejected_when_k_too_large():
    # Stream: 0,1,2,... (mod 2**64). x=50 is reachable, but not within <=10 steps.
    s = NonceStream(base=0, delta=1, m=2**64, max_steps=10)
    assert not s.compatible(50)


def test_nonce_stream_delta_zero_is_constant_stream():
    s = NonceStream(base=42, delta=0, m=2**64, max_steps=1000)
    assert s.compatible(42)
    assert not s.compatible(43)
