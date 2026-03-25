from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cmd(args: list[str], *, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, env=env)


def test_cli_analyze_emits_artifact(tmp_path: Path):
    repo = Path(__file__).resolve().parents[1]
    src = repo / "src"
    examples = repo / "examples"
    policy = examples / "policies" / "default_policy.json"
    trace = examples / "michael_identity_prime_trace.jsonl"

    out = tmp_path / "artifact.json"
    cp = run_cmd(
        [sys.executable, "-m", "prime_er.cli", "analyze", "--in", str(trace), "--policy", str(policy), "--out", str(out)],
        extra_env={"PYTHONPATH": str(src)},
    )
    assert cp.returncode == 0, cp.stderr

    obj = json.loads(out.read_text(encoding="utf-8"))
    assert obj["claim"] == "identity_is_prime_demo"
    assert obj["status"] in ("PROVED", "VIOLATION")
    assert "inputs" in obj and "events_sha256" in obj["inputs"]
    assert "diagnostics" in obj and obj["diagnostics"]["iter_count"] >= 1

    # Our example trace includes an adtech pixel on a patient event, so it should violate.
    assert obj["status"] == "VIOLATION"
    assert len(obj.get("violations", [])) >= 1


def test_cli_segment_emits_marketer_safe_summary(tmp_path: Path):
    repo = Path(__file__).resolve().parents[1]
    src = repo / "src"
    examples = repo / "examples"
    policy = examples / "policies" / "default_policy.json"
    trace = examples / "michael_identity_prime_trace.jsonl"

    out = tmp_path / "segment.json"
    cp = run_cmd(
        [sys.executable, "-m", "prime_er.cli", "segment", "--in", str(trace), "--policy", str(policy), "--out", str(out), "--epsilon", "2.0", "--seed", "7"],
        extra_env={"PYTHONPATH": str(src)},
    )
    assert cp.returncode == 0, cp.stderr

    obj = json.loads(out.read_text(encoding="utf-8"))
    assert "counts_by_prime" in obj
    assert "cohorts" in obj

    # Ensure we did not export raw identifiers
    out_text = out.read_text(encoding="utf-8").lower()
    assert "michael@example.com" not in out_text
    assert "third_party_cookie" not in out_text
