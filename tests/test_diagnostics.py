from pathlib import Path

import pytest

from anti_slop_python.diagnostics import Diagnostic


@pytest.mark.parametrize("code", ["F821", "SyntaxError", "IOError", "Ruff"])
def test_unrelated_diagnostics_keep_their_original_output(code: str) -> None:
    diagnostic = Diagnostic(Path("example.py"), 3, 7, code, "Original message")

    assert str(diagnostic) == f"example.py:3:7 {code} Original message"


def test_guidance_preserves_ruff_message_and_location() -> None:
    message = "`calculate` is too complex (15 > 12)"
    diagnostic = Diagnostic(Path("example.py"), 8, 5, "C901", message)

    lines = str(diagnostic).splitlines()

    assert diagnostic.message == message
    assert lines[0] == f"example.py:8:5 C901 {message}"
    assert lines[1:] == [
        "  Simplify the decision model; extract cohesive operations"
        " with explicit inputs.",
        "  Use a lookup table only when the branches represent a data mapping.",
        "  Preserve edge cases; do not hide branches in lambdas or raise the limit.",
    ]


def test_custom_banned_api_keeps_its_policy_without_patching_advice() -> None:
    message = "`custom.api` is banned: Use custom.replacement for this operation."
    diagnostic = Diagnostic(Path("example.py"), 1, 1, "TID251", message)

    rendered = str(diagnostic)

    assert diagnostic.message == message
    assert rendered.startswith(f"example.py:1:1 TID251 {message}\n")
    assert "Use an allowed API that meets the project's policy." in rendered
    assert "aliases, wrappers, or dynamic imports" in rendered
    assert "patch" not in rendered
