"""Replay the saved successes and failures without calling a coding model."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

EVALUATION = Path(__file__).parents[1] / "examples/refactoring_evaluation"
RUNS = (
    "pair1-control",
    "pair1-linter",
    "pair2-control",
    "pair2-linter",
    "pair3-control",
    "pair3-linter",
    "confirmation1-linter",
    "confirmation2-linter",
    "final-linter",
)
POLICY_CASE = "test_entire_refactored_directory_passes_policy"


@pytest.mark.parametrize("run_name", RUNS)
def test_saved_candidate_reproduces_behavior_outcomes(
    tmp_path: Path, run_name: str
) -> None:
    run = EVALUATION / "runs" / run_name
    capture = json.loads((run / "capture.json").read_text())
    candidate = run / "candidate"
    actual_hashes = {
        str(path.relative_to(candidate)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(candidate.rglob("*.py"))
    }
    assert actual_hashes == capture["candidate_sha256"]
    output = tmp_path / "evaluation"
    result = subprocess.run(
        [
            sys.executable,
            str(EVALUATION / "evaluate.py"),
            str(candidate),
            str(output),
            "--include-import-modes",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert result.returncode in {0, 1}, result.stdout + result.stderr
    actual = json.loads((output / "results.json").read_text())
    expected = json.loads((run / "extended_results.json").read_text())
    # The current policy has deliberately changed since the initial runs. Compare
    # behavior and API outcomes; policy defaults have their own regression tests.
    assert {
        case["name"]: case["status"]
        for case in actual["tests"]
        if case["name"] != POLICY_CASE
    } == {
        case["name"]: case["status"]
        for case in expected["tests"]
        if case["name"] != POLICY_CASE
    }, result.stdout
