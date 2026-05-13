from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Sequence

State = Any
Event = Any
Reducer = Callable[[State, Event], State]


def canonical_state_hash(state: Any) -> str:
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def replay(initial_state: State, events: Sequence[Event], reducer: Reducer) -> State:
    state = initial_state
    for event in events:
        state = reducer(state, event)
    return state


def neutrality_replay_certificate(
    initial_state: State,
    canonical_events: Sequence[Event],
    reordered_events: Sequence[Event],
    reducer: Reducer,
    *,
    tolerance: float = 0.0,
    distance: Callable[[State, State], float] | None = None,
) -> dict[str, Any]:
    """Replay two admissible orders and report confluence evidence.

    The reducer supplies semantics; this helper records deterministic replay
    evidence. If no distance function is supplied, equality of canonical JSON
    hashes is required.
    """
    left = replay(initial_state, canonical_events, reducer)
    right = replay(initial_state, reordered_events, reducer)

    if distance is None:
        dist = 0.0 if canonical_state_hash(left) == canonical_state_hash(right) else 1.0
    else:
        dist = float(distance(left, right))

    return {
        "artifact_type": "NeutralityReplayRun",
        "canonical_event_count": len(canonical_events),
        "reordered_event_count": len(reordered_events),
        "canonical_state_hash": canonical_state_hash(left),
        "reordered_state_hash": canonical_state_hash(right),
        "distance": dist,
        "tolerance": tolerance,
        "result": "VERIFIED" if dist <= tolerance else "REFUTED",
    }
