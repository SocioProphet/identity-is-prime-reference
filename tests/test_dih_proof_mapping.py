from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prime_er.dih_proofs import ToyRSAPoK, ToySchnorrPoK


class SchnorrMappingTests(unittest.TestCase):
    def test_real_transcript_verifies(self) -> None:
        protocol = ToySchnorrPoK(witness=123, q=1019, generator=5)
        transcript = protocol.prove(challenge=77, nonce=456)
        self.assertTrue(protocol.verify(transcript))

    def test_extractor_recovers_witness_from_two_challenges(self) -> None:
        protocol = ToySchnorrPoK(witness=123, q=1019, generator=5)
        first = protocol.prove(challenge=10, nonce=456)
        second = protocol.prove(challenge=22, nonce=456)
        self.assertEqual(protocol.extract(first, second), 123)

    def test_simulator_generates_verifying_transcript(self) -> None:
        protocol = ToySchnorrPoK(witness=123, q=1019, generator=5)
        transcript = protocol.simulate(challenge=37, response=222)
        self.assertTrue(transcript.simulated)
        self.assertTrue(protocol.verify(transcript))


class RSAMappingTests(unittest.TestCase):
    def test_real_transcripts_verify(self) -> None:
        protocol = ToyRSAPoK(witness=7, modulus=3233, exponent=17)
        self.assertTrue(protocol.verify(protocol.prove(challenge=0, nonce=11)))
        self.assertTrue(protocol.verify(protocol.prove(challenge=1, nonce=11)))

    def test_extractor_recovers_witness_from_bit_challenges(self) -> None:
        protocol = ToyRSAPoK(witness=7, modulus=3233, exponent=17)
        zero = protocol.prove(challenge=0, nonce=11)
        one = protocol.prove(challenge=1, nonce=11)
        self.assertEqual(protocol.extract(zero, one), 7)

    def test_simulator_generates_verifying_transcript(self) -> None:
        protocol = ToyRSAPoK(witness=7, modulus=3233, exponent=17)
        transcript = protocol.simulate(challenge=1, response=19)
        self.assertTrue(transcript.simulated)
        self.assertTrue(protocol.verify(transcript))

    def test_invalid_response_rejects(self) -> None:
        protocol = ToyRSAPoK(witness=7, modulus=3233, exponent=17)
        transcript = protocol.prove(challenge=1, nonce=11)
        tampered = type(transcript)(
            modulus=transcript.modulus,
            exponent=transcript.exponent,
            public_value=transcript.public_value,
            commitment=transcript.commitment,
            challenge=transcript.challenge,
            response=(transcript.response + 1) % transcript.modulus,
            simulated=False,
        )
        self.assertFalse(protocol.verify(tampered))


if __name__ == "__main__":
    unittest.main()
