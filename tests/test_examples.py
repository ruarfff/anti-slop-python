from __future__ import annotations

from pathlib import Path

import pytest

from anti_slop_python.cli import main

REPOSITORY_ROOT = Path(__file__).parents[1]
EXAMPLE_ROOT = REPOSITORY_ROOT / "examples" / "basic_project"


def test_basic_example_demonstrates_every_policy_rule(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([str(EXAMPLE_ROOT)])
    captured = capsys.readouterr()

    diagnostics = [
        line for line in captured.out.splitlines() if not line.startswith("  ")
    ]
    codes = {line.split()[1] for line in diagnostics}

    assert exit_code == 1
    assert len(diagnostics) == 18
    assert codes == {
        "SPY001",
        "SPY002",
        "SPY003",
        "BLE001",
        "C901",
        "E722",
        "PLR0915",
        "TID251",
        "ANN001",
        "ANN002",
        "ANN003",
        "ANN201",
        "ANN202",
        "ANN204",
        "ANN205",
        "ANN206",
        "ANN401",
        "F403",
    }
    expected_guidance = {
        "SPY001": "Do not remove annotations or hide Any behind aliases",
        "SPY002": "Do not replace this call with __dict__, vars()",
        "SPY003": "Separate distinct responsibilities into cohesive modules",
        "C901": "Preserve edge cases; do not hide branches in lambdas",
        "PLR0915": "Do not pack statements onto fewer lines",
        "TID251": "Do not hide the banned API behind aliases",
        "E722": "Do not replace bare except with Exception or BaseException",
        "BLE001": "Do not add logging or return a default merely to silence the rule",
        "F403": "Import each required name explicitly",
    }
    for block in captured.out.split(str(EXAMPLE_ROOT))[1:]:
        code = block.splitlines()[0].split()[1]
        guidance = (
            "Preserve existing type information"
            if code.startswith("ANN")
            else expected_guidance[code]
        )
        assert guidance in block
    assert captured.err == ""


def test_basic_example_preferred_design_passes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    preferred = EXAMPLE_ROOT / "src" / "example_project" / "preferred.py"

    exit_code = main([str(preferred)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
