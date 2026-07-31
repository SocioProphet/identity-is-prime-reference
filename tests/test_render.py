from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from prime_er.event import load_event_ir  # noqa: E402
from prime_er.policy import default_policy  # noqa: E402
from prime_er.render import render_warrant_card  # noqa: E402
from prime_er.segment import release_to_proof_artifact, segment_summary  # noqa: E402

_REPO = Path(__file__).resolve().parents[1]


def _released_artifact():
    ev = load_event_ir(_REPO / "examples" / "synthetic_population_trace.jsonl").events
    rel = segment_summary(ev, default_policy(), epsilon=2.0, seed=3)
    return json.loads(release_to_proof_artifact(rel, inputs={"events_path": "x"}).to_json())


def test_warrant_card_shows_claim_level_and_warrant():
    html = render_warrant_card(_released_artifact())
    assert "<!doctype html>" in html.lower()
    assert "marketer_safe_segment" in html
    # epistemicLevel surfaced with its Stardust colour.
    assert "empirical" in html
    assert "#B79CF0" in html  # empirical palette colour
    # The warrant (DP params) is on the surface.
    assert "laplace+noisy_threshold" in html
    # Self-contained: no external network references.
    assert "http://" not in html and "https://" not in html.replace('lang="en"', "")
    assert "cdn" not in html.lower()


def test_warrant_card_escapes_untrusted_strings():
    artifact = {"claim": "<script>alert(1)</script>", "status": "PROVED",
                "epistemicLevel": "empirical", "precision": {}, "witnesses": {}, "inputs": {}}
    html = render_warrant_card(artifact)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_warrant_card_renders_refusal():
    artifact = {"claim": "marketer_safe_segment", "status": "INCONCLUSIVE",
                "violations": [{"kind": "PRIVACY_REFUSAL", "details": {"reason": "insufficient_actors"}}],
                "precision": {}, "witnesses": {}, "inputs": {}}
    html = render_warrant_card(artifact)
    assert "INCONCLUSIVE" in html
    assert "PRIVACY_REFUSAL" in html
