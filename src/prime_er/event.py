from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union


@dataclass(frozen=True)
class Scope:
    """Where an event occurs (fog-first: device/app realms matter)."""
    device: str
    app: str
    realm: str  # e.g., "citizen_fog", "citizen_cloud", "institution", "adtech"
    jurisdiction: str = ""

    @staticmethod
    def from_obj(obj: Dict[str, Any]) -> "Scope":
        return Scope(
            device=str(obj.get("device", "")),
            app=str(obj.get("app", "")),
            realm=str(obj.get("realm", "")),
            jurisdiction=str(obj.get("jurisdiction", "")),
        )


@dataclass(frozen=True)
class Event:
    ts: str
    actor: str
    scope: Scope
    action: str
    primes: List[str]
    attrs: Dict[str, Any]
    evidence: Dict[str, Any]

    @staticmethod
    def from_obj(obj: Dict[str, Any]) -> "Event":
        scope_obj = obj.get("scope", {}) or {}
        return Event(
            ts=str(obj.get("ts", "")),
            actor=str(obj.get("actor", "")),
            scope=Scope.from_obj(scope_obj),
            action=str(obj.get("action", "")),
            primes=list(obj.get("primes", []) or []),
            attrs=dict(obj.get("attrs", {}) or {}),
            evidence=dict(obj.get("evidence", {}) or {}),
        )


@dataclass(frozen=True)
class EventIR:
    events: List[Event]


def _load_json(path: Union[str, Path]) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_event_ir(path: Union[str, Path]) -> EventIR:
    """Load Event-IR from:
    * JSON object: {"events": [...]} (preferred)
    * JSON array: [...]
    * JSONL: one event object per line
    """
    path = Path(path)
    if path.suffix.lower() == ".jsonl":
        events: List[Event] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                events.append(Event.from_obj(obj))
        return EventIR(events=events)

    obj = _load_json(path)
    if isinstance(obj, dict) and "events" in obj:
        raw_events = obj["events"]
    elif isinstance(obj, list):
        raw_events = obj
    else:
        raise ValueError(f"Unsupported Event-IR JSON format in {path}")
    events = [Event.from_obj(e) for e in raw_events]
    return EventIR(events=events)


def iter_events(path: Union[str, Path]) -> Iterator[Event]:
    """Streaming-friendly iterator."""
    ir = load_event_ir(path)
    yield from ir.events
