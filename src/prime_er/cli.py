from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator

from .congruence import NonceStream
from .er import resolve_entities
from .event import Event, load_event_ir
from .policy import load_policy
from .proofs import ProofArtifact, sha256_file
from .schedule import ScheduleConfig, exp_checkpoints, log_bucket
from .segment import segment_summary


def _load_schema_dict(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _event_validator(schema_dict: Dict[str, Any]) -> Draft202012Validator:
    # If schema is a container schema {events: [...]}, validate individual events against items schema.
    try:
        event_schema = schema_dict["properties"]["events"]["items"]
        return Draft202012Validator(event_schema)
    except Exception:
        return Draft202012Validator(schema_dict)


def _validate_events(events: List[Event], schema_path: Path) -> List[str]:
    """Validate events against schema. Returns error strings."""
    schema_dict = _load_schema_dict(schema_path)
    v = _event_validator(schema_dict)
    errs: List[str] = []
    for i, ev in enumerate(events):
        obj = {
            "ts": ev.ts,
            "actor": ev.actor,
            "scope": {"device": ev.scope.device, "app": ev.scope.app, "realm": ev.scope.realm, "jurisdiction": ev.scope.jurisdiction},
            "action": ev.action,
            "primes": ev.primes,
            "attrs": ev.attrs,
            "evidence": ev.evidence,
        }
        for e in sorted(v.iter_errors(obj), key=lambda e: e.path):
            errs.append(f"event[{i}] {list(e.path)}: {e.message}")
    return errs


def analyze(in_path: str, policy_path: Optional[str], out_path: str, validate: bool = False, max_steps: int = 1000) -> None:
    t0 = time.time()

    ir = load_event_ir(in_path)
    events = ir.events
    policy = load_policy(policy_path)

    # Optional schema validation
    if validate:
        schema_path = Path(__file__).resolve().parents[2] / "schemas" / "event_ir.schema.json"
        errors = _validate_events(events, schema_path)
        if errors:
            raise SystemExit("Schema validation failed:\n" + "\n".join(errors))

    # 1) Entity resolution (with policy-veto on merges)
    entity_ids, reasons = resolve_entities(events, policy=policy)

    # 2) Policy violations per event
    violations: List[Dict[str, Any]] = []
    for i, ev in enumerate(events):
        for v in policy.event_violations(ev):
            violations.append({"event_index": i, "ts": ev.ts, "action": ev.action, "scope": ev.scope.realm, **v})

    # 3) Congruence-based leak check (toy)
    # Convention: if we see an event with evidence {"nonce_stream": {base, delta, m}}, we treat it as HSM stream init.
    stream: Optional[NonceStream] = None
    for i, ev in enumerate(events):
        ns = (ev.evidence or {}).get("nonce_stream")
        if isinstance(ns, dict) and all(k in ns for k in ("base", "delta", "m")):
            stream = NonceStream(
                base=int(ns["base"]),
                delta=int(ns["delta"]),
                m=int(ns["m"]),
                max_steps=int(ns.get("max_steps", max_steps)),
            )
        observed = (ev.evidence or {}).get("nonce_observed")
        if stream is not None and observed is not None:
            x = int(observed)
            k = stream.steps_to(x)
            if k is not None:
                # If observed outside fog/hsm realms, treat as potential leak.
                if ev.scope.realm.lower() in ("adtech", "institution", "cloud") or policy.is_ad_realm(ev.scope.realm):
                    violations.append({
                        "event_index": i,
                        "ts": ev.ts,
                        "action": ev.action,
                        "scope": ev.scope.realm,
                        "kind": "NONCE_STREAM_LEAK",
                        "details": {"steps": k, "bucket": log_bucket(max(1, k)), "observed": x},
                    })

    # Minimal counterexample trace: first violation + previous 2 events (toy)
    counterexample: List[Dict[str, Any]] = []
    if violations:
        first = min(v["event_index"] for v in violations)
        start = max(0, first - 2)
        end = min(len(events), first + 1)
        for idx in range(start, end):
            ev = events[idx]
            counterexample.append({
                "event_index": idx,
                "ts": ev.ts,
                "actor": ev.actor,
                "action": ev.action,
                "scope": {"device": ev.scope.device, "app": ev.scope.app, "realm": ev.scope.realm, "jurisdiction": ev.scope.jurisdiction},
                "primes": ev.primes,
                "attrs_keys": sorted(list((ev.attrs or {}).keys())),
                "evidence_keys": sorted(list((ev.evidence or {}).keys())),
            })

    cfg = ScheduleConfig()
    checkpoints = exp_checkpoints(cfg)

    status = "PROVED" if not violations else "VIOLATION"
    artifact = ProofArtifact(
        claim="identity_is_prime_demo",
        status=status,
        inputs={
            "events_path": str(in_path),
            "events_sha256": sha256_file(in_path),
            "policy_path": str(policy_path) if policy_path else "<default>",
            "policy_sha256": sha256_file(policy_path) if policy_path else "",
            "event_count": len(events),
        },
        domains=["ER(boost+principles)", "POLICY(prime_veto)", "CONGRUENCE(mod_stream)"],
        violations=violations,
        counterexample=counterexample,
        witnesses={
            "entity_ids": entity_ids,
            "edge_reasons_sample": {
                f"{a}->{b}": {"kind": r.kind, "score": r.score, "match_key": r.match_key}
                for (a,b), r in list(reasons.items())[:10]
            },
        },
        precision={"mode": "Toy", "note": "For production: record Exact/Approx{δ} and widening deltas."},
        schedule={"base": cfg.base, "checkpoints": checkpoints[:10], "note": "base-e packing (first 10 checkpoints)"},
    )
    artifact.diagnostics.iter_count = len(events)
    artifact.diagnostics.duration_ms = int(round((time.time() - t0) * 1000))

    Path(out_path).write_text(artifact.to_json(), encoding="utf-8")


def segment(in_path: str, policy_path: Optional[str], out_path: str, epsilon: Optional[float], seed: int) -> None:
    ir = load_event_ir(in_path)
    policy = load_policy(policy_path)
    out = segment_summary(ir.events, policy=policy, epsilon=epsilon, seed=seed)
    Path(out_path).write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(prog="prime-er", description="Identity Is Prime — toy analyzer")
    sp = ap.add_subparsers(dest="cmd", required=True)

    ap_an = sp.add_parser("analyze", help="Run ER + policy + congruence checks and emit a proof artifact")
    ap_an.add_argument("--in", dest="in_path", required=True, help="Input Event-IR (.json or .jsonl)")
    ap_an.add_argument("--policy", dest="policy_path", default=None, help="Policy JSON (optional)")
    ap_an.add_argument("--out", dest="out_path", required=True, help="Output artifact JSON")
    ap_an.add_argument("--validate", action="store_true", help="Validate events against schema")
    ap_an.add_argument("--max-steps", type=int, default=1000, help="Bounded congruence max steps")

    ap_seg = sp.add_parser("segment", help="Emit marketer-safe aggregates (no actor IDs)")
    ap_seg.add_argument("--in", dest="in_path", required=True)
    ap_seg.add_argument("--policy", dest="policy_path", default=None)
    ap_seg.add_argument("--out", dest="out_path", required=True)
    ap_seg.add_argument("--epsilon", type=float, default=None, help="Optional toy noise strength")
    ap_seg.add_argument("--seed", type=int, default=0)

    args = ap.parse_args()
    if args.cmd == "analyze":
        analyze(args.in_path, args.policy_path, args.out_path, validate=args.validate, max_steps=args.max_steps)
    elif args.cmd == "segment":
        segment(args.in_path, args.policy_path, args.out_path, epsilon=args.epsilon, seed=args.seed)
    else:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
