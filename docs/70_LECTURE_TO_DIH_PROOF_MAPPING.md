# Lecture-to-DIH Proof Mapping v0.1

Status: toy executable proof-harness mapping  
Scope: Schnorr-style and RSA-style identification protocols for DIH teaching and regression tests  
Boundary: not production cryptography

## Purpose

This document maps lecture-style interactive proof steps into the DIH Python harness. The goal is to make each proof move explicit:

- commitment;
- challenge;
- response;
- verification;
- two-transcript extraction;
- honest-verifier zero-knowledge simulation.

The implementation lives in:

```text
src/prime_er/dih_proofs.py
```

The tests live in:

```text
tests/test_dih_proof_mapping.py
```

Run the tests with:

```bash
python -m unittest tests.test_dih_proof_mapping
```

## Boundary

The Schnorr lane is a toy cyclic-group model using additive arithmetic modulo `q`. It preserves the algebra of the lecture proof, but it is not elliptic-curve point arithmetic.

The RSA lane is a toy identification harness over small integers. It preserves the proof equations, extractor equation, and simulator equation, but it is not production RSA, not a signature scheme, and not a deployment-ready authentication system.

This tranche is for DIH reasoning, proof artifacts, education, and regression tests.

---

## 1. Schnorr-style proof of knowledge

The toy Schnorr harness models the lecture proof over an additive cyclic group modulo `q`.

| Lecture step | Concept | Python operation | Harness location |
| --- | --- | --- | --- |
| Commit `R = rG` | prover chooses random scalar `r` | `commitment = (r * generator) % q` | `ToySchnorrPoK.commit` |
| Challenge `c` | verifier selects a field challenge | `c = challenge % q` | `ToySchnorrPoK.prove` |
| Response `s = r + cx mod q` | prover binds nonce to witness | `response = (r + c * witness) % q` | `ToySchnorrPoK.prove` |
| Verify `sG = R + cP` | verifier checks algebraic consistency | `lhs == rhs` where `lhs=(s*G)%q`, `rhs=(R+cP)%q` | `ToySchnorrPoK.verify` |
| Extract `x = (s1-s2)/(c1-c2) mod q` | recover witness from same commitment under different challenges | `pow(denominator, -1, q)` then multiply numerator | `ToySchnorrPoK.extract` |
| Simulate transcript | generate valid transcript without witness-use in the transcript path | `R = sG - cP mod q` | `ToySchnorrPoK.simulate` |

### Preservation properties

Correctness is checked by `verify`.  
Special soundness is checked by extracting from two transcripts with the same commitment and different challenges.  
HVZK shape is checked by constructing a simulated transcript that verifies without calling the commit-response path.

---

## 2. RSA-style identification proof

The toy RSA harness models the lecture proof with public value `v = s^e mod N` and witness `s`.

| Lecture step | Concept | Python operation | Harness location |
| --- | --- | --- | --- |
| Commit `a = r^e mod N` | prover chooses random invertible `r` | `commitment = pow(r, exponent, modulus)` | `ToyRSAPoK.commit` |
| Challenge `c in {0,1}` | verifier sends bit challenge | `_normalize_bit_challenge(challenge)` | `ToyRSAPoK.prove` |
| Response `z = r s^c mod N` | prover binds nonce and witness | `response = (r * pow(witness, c, modulus)) % modulus` | `ToyRSAPoK.prove` |
| Verify `z^e = a v^c mod N` | verifier checks algebraic consistency | `lhs == rhs` with modular exponentiation | `ToyRSAPoK.verify` |
| Extract `s = z1 z0^-1 mod N` | recover witness from `c=1` and `c=0` transcripts | `one.response * pow(zero.response, -1, modulus)` | `ToyRSAPoK.extract` |
| Simulate transcript | invert verification equation | `a = z^e * v^-c mod N` | `ToyRSAPoK.simulate` |

### Preservation properties

Correctness is checked by both bit challenges.  
Special soundness is checked by extracting from two transcripts with the same commitment and challenges `{0,1}`.  
HVZK shape is checked by constructing simulator transcripts that satisfy the verifier equation.

---

## 3. DIH interpretation

DIH uses these lanes as proof-harness specimens:

1. A lecture proof becomes a small executable state machine.
2. The commitment, challenge, response, and verification equations remain visible.
3. Extractor logic is tested directly, not described only in prose.
4. Simulator logic is tested directly, not treated as an informal claim.
5. The harness remains toy-scoped so the repository stays teachable and audit-friendly.

## 4. Regression contract

The test suite must prove:

- real Schnorr transcripts verify;
- Schnorr extraction recovers the witness from two challenges;
- Schnorr simulator transcripts verify;
- real RSA transcripts verify for both bit challenges;
- RSA extraction recovers the witness from the two bit challenges;
- RSA simulator transcripts verify;
- tampered RSA responses reject.

These tests make the lecture-to-code mapping executable without promoting the toy harness to production cryptography.
