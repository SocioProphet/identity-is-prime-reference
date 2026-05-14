from __future__ import annotations

from dataclasses import dataclass
from math import gcd
from secrets import randbelow


@dataclass(frozen=True)
class SchnorrTranscript:
    """Toy Schnorr transcript over an additive cyclic group modulo q."""

    public_key: int
    commitment: int
    challenge: int
    response: int
    simulated: bool = False


class ToySchnorrPoK:
    """Lecture-to-code Schnorr proof-of-knowledge harness.

    This is intentionally a toy cyclic-group model. It preserves the algebra used
    in the lecture proof: commit, challenge, response, verification, two-transcript
    extraction, and honest-verifier zero-knowledge simulation. It is not production
    elliptic-curve cryptography.
    """

    def __init__(self, witness: int, q: int = 1019, generator: int = 5) -> None:
        if q <= 2:
            raise ValueError("q must be an odd modulus for the toy group")
        self.q = q
        self.generator = generator % q
        self.witness = witness % q
        self.public_key = (self.witness * self.generator) % q

    def commit(self, nonce: int | None = None) -> tuple[int, int]:
        r = randbelow(self.q - 1) + 1 if nonce is None else nonce % self.q
        commitment = (r * self.generator) % self.q
        return r, commitment

    def prove(self, challenge: int, nonce: int | None = None) -> SchnorrTranscript:
        r, commitment = self.commit(nonce)
        c = challenge % self.q
        response = (r + c * self.witness) % self.q
        return SchnorrTranscript(
            public_key=self.public_key,
            commitment=commitment,
            challenge=c,
            response=response,
            simulated=False,
        )

    def verify(self, transcript: SchnorrTranscript) -> bool:
        lhs = (transcript.response * self.generator) % self.q
        rhs = (
            transcript.commitment
            + transcript.challenge * transcript.public_key
        ) % self.q
        return lhs == rhs

    def extract(self, first: SchnorrTranscript, second: SchnorrTranscript) -> int:
        if first.commitment != second.commitment:
            raise ValueError("special soundness extraction requires same commitment")
        if first.challenge == second.challenge:
            raise ValueError("special soundness extraction requires different challenges")
        numerator = (first.response - second.response) % self.q
        denominator = (first.challenge - second.challenge) % self.q
        return (numerator * pow(denominator, -1, self.q)) % self.q

    def simulate(
        self,
        challenge: int | None = None,
        response: int | None = None,
    ) -> SchnorrTranscript:
        c = randbelow(self.q) if challenge is None else challenge % self.q
        s = randbelow(self.q - 1) + 1 if response is None else response % self.q
        commitment = (
            s * self.generator
            - c * self.public_key
        ) % self.q
        return SchnorrTranscript(
            public_key=self.public_key,
            commitment=commitment,
            challenge=c,
            response=s,
            simulated=True,
        )


@dataclass(frozen=True)
class RSATranscript:
    """Toy RSA identification transcript."""

    modulus: int
    exponent: int
    public_value: int
    commitment: int
    challenge: int
    response: int
    simulated: bool = False


class ToyRSAPoK:
    """Lecture-to-code RSA proof-of-knowledge harness.

    The public value is v = s^e mod N. The prover shows knowledge of s without
    revealing it. The challenge space is {0, 1}, matching the lecture-style
    special soundness extractor. This harness is for tests and teaching only.
    """

    def __init__(self, witness: int, modulus: int = 3233, exponent: int = 17) -> None:
        if modulus <= 2:
            raise ValueError("modulus must be composite-sized for the toy RSA harness")
        if gcd(witness, modulus) != 1:
            raise ValueError("witness must be invertible modulo N")
        self.modulus = modulus
        self.exponent = exponent
        self.witness = witness % modulus
        self.public_value = pow(self.witness, self.exponent, self.modulus)

    def commit(self, nonce: int | None = None) -> tuple[int, int]:
        r = self._random_unit() if nonce is None else nonce % self.modulus
        if gcd(r, self.modulus) != 1:
            raise ValueError("nonce must be invertible modulo N")
        commitment = pow(r, self.exponent, self.modulus)
        return r, commitment

    def prove(self, challenge: int, nonce: int | None = None) -> RSATranscript:
        c = self._normalize_bit_challenge(challenge)
        r, commitment = self.commit(nonce)
        response = (r * pow(self.witness, c, self.modulus)) % self.modulus
        return RSATranscript(
            modulus=self.modulus,
            exponent=self.exponent,
            public_value=self.public_value,
            commitment=commitment,
            challenge=c,
            response=response,
            simulated=False,
        )

    def verify(self, transcript: RSATranscript) -> bool:
        if transcript.challenge not in (0, 1):
            return False
        lhs = pow(transcript.response, transcript.exponent, transcript.modulus)
        rhs = (
            transcript.commitment
            * pow(transcript.public_value, transcript.challenge, transcript.modulus)
        ) % transcript.modulus
        return lhs == rhs

    def extract(self, first: RSATranscript, second: RSATranscript) -> int:
        if first.commitment != second.commitment:
            raise ValueError("special soundness extraction requires same commitment")
        if {first.challenge, second.challenge} != {0, 1}:
            raise ValueError("RSA extraction requires one c=0 transcript and one c=1 transcript")
        one = first if first.challenge == 1 else second
        zero = first if first.challenge == 0 else second
        return (one.response * pow(zero.response, -1, self.modulus)) % self.modulus

    def simulate(
        self,
        challenge: int,
        response: int | None = None,
    ) -> RSATranscript:
        c = self._normalize_bit_challenge(challenge)
        z = self._random_unit() if response is None else response % self.modulus
        if gcd(z, self.modulus) != 1:
            raise ValueError("simulated response must be invertible modulo N")
        if c == 0:
            commitment = pow(z, self.exponent, self.modulus)
        else:
            commitment = (
                pow(z, self.exponent, self.modulus)
                * pow(self.public_value, -1, self.modulus)
            ) % self.modulus
        return RSATranscript(
            modulus=self.modulus,
            exponent=self.exponent,
            public_value=self.public_value,
            commitment=commitment,
            challenge=c,
            response=z,
            simulated=True,
        )

    def _normalize_bit_challenge(self, challenge: int) -> int:
        if challenge not in (0, 1):
            raise ValueError("toy RSA challenge must be 0 or 1")
        return challenge

    def _random_unit(self) -> int:
        while True:
            candidate = randbelow(self.modulus - 2) + 2
            if gcd(candidate, self.modulus) == 1:
                return candidate
