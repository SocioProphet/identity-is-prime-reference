# Publishing checklist

This repo is intentionally **small** and **didactic**. If we want to publish it
as a paper + reference implementation (or teach it as a course), these are the
minimum upgrades that keep the work rigorous and reproducible.

## Soundness and scope

1. **State the claims precisely.**
   - What do we prove? (e.g., "no identity-prime tagged as HEALTH may cross into
     any ADTECH realm")
   - What do we *not* prove? (e.g., side-channels, compromised kernel)

2. **Explicit threat model.**
   - Attacker controls: apps? JS? network? logs?
   - Trusted computing base: kernel? enclave? HSM? schema gate?

3. **Define the semantics of Event-IR.**
   - What does each event *mean*?
   - What evidence is required for a claim to be sound?

## Reproducibility

1. **Pinned versions + deterministic runs.**
   - Lock dependencies.
   - Version schemas and artifacts.

2. **Golden traces + acceptance bands.**
   - Include realistic benign + violation traces.
   - Make CI refuse regressions.

## Privacy & human factors

1. **Local-first stance.**
   - Demonstrate that raw events never have to leave the device/fog to compute
     proofs.

2. **Explainability.**
   - Artifacts must be readable by non-mathematicians.
   - Every "VIOLATION" should include a minimal witness trace.

## Legal and operational

1. **License + attribution.**
   - Pick a license consistent with the publishing goal.
   - Add citation metadata (see `CITATION.cff`).

2. **Safety disclaimer.**
   - Make clear this is a reference and not a substitute for a full security
     review.
