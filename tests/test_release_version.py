"""Exercise the workflow's version selection against real local Git tags."""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "publish.yml"


def _git(directory: Path, *arguments: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Release Test",
            "-c",
            "user.email=release-test@example.invalid",
            *arguments,
        ],
        cwd=directory,
        capture_output=True,
        check=True,
    )


@pytest.mark.parametrize(
    ("previous_tag", "tag_at_head", "expected_tag", "is_new"),
    [
        (None, False, "v0.2.0", "true"),
        ("v0.1.1", False, "v0.2.0", "true"),
        ("v0.1.99", False, "v0.2.0", "true"),
        ("v0.2.0", False, "v0.2.1", "true"),
        ("v0.3.5", False, "v0.3.6", "true"),
        ("v1.0.0", False, "v1.0.1", "true"),
        ("v0.2.0", True, "v0.2.0", "false"),
    ],
)
def test_workflow_selects_next_release(
    tmp_path: Path,
    previous_tag: str | None,
    tag_at_head: bool,
    expected_tag: str,
    is_new: str,
) -> None:
    _git(tmp_path, "init", "--quiet")
    _git(tmp_path, "commit", "--allow-empty", "-m", "Initial fixture")
    if previous_tag:
        _git(tmp_path, "tag", previous_tag)
    if not tag_at_head:
        _git(tmp_path, "commit", "--allow-empty", "-m", "Next fixture")
    workflow = WORKFLOW.read_text()
    block = workflow.split("python3 - << 'EOF' >> \"$GITHUB_OUTPUT\"\n", 1)[1]
    script = textwrap.dedent(block.split("\n          EOF", 1)[0])

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.splitlines() == [
        f"tag={expected_tag}",
        f"version={expected_tag.removeprefix('v')}",
        f"is_new_tag={is_new}",
    ]
