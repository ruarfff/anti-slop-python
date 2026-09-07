"""Prepare one fresh agent workspace; this does not call a model."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
ORIGINAL = REPOSITORY / "examples/basic_project/src/example_project/order_report.py"

SMOKE = '''"""Visible CLI smoke checks shared by both conditions."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
for arguments in [("--demo",), ("--help",), (), ("--unknown",)]:
    results = [
        subprocess.run(
            [sys.executable, str(root / folder / "order_report.py"), *arguments],
            capture_output=True, timeout=15, check=False,
        )
        for folder in ["before", "candidate"]
    ]
    assert results[0].returncode == results[1].returncode, arguments
    assert results[0].stdout == results[1].stdout, arguments
    assert results[0].stderr == results[1].stderr, arguments
print("4 CLI smoke comparisons passed")
'''

LINT = '''"""Run the frozen tool and record only its public diagnostics."""
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

root = Path(__file__).resolve().parent
environment = os.environ.copy()
environment["PYTHONPATH"] = str(root / "tool")
started = time.monotonic()
timestamp = datetime.now(UTC).isoformat()
result = subprocess.run(
    [sys.executable, "-m", "anti_slop_python", *sys.argv[1:]],
    env=environment, capture_output=True, text=True, check=False, timeout=60,
)
with (root / "lint.jsonl").open("a", encoding="utf-8") as stream:
    stream.write(json.dumps({
        "started_at": timestamp, "elapsed_seconds": time.monotonic() - started,
        "arguments": sys.argv[1:], "exit_code": result.returncode,
        "stdout": result.stdout, "stderr": result.stderr,
    }) + "\\n")
print(result.stdout, end="")
print(result.stderr, end="", file=sys.stderr)
raise SystemExit(result.returncode)
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(workspace: Path, condition: str) -> None:
    workspace.mkdir(parents=True, exist_ok=False)
    for name in ["before", "candidate"]:
        (workspace / name).mkdir()
        shutil.copyfile(ORIGINAL, workspace / name / "order_report.py")
    shutil.copytree(
        REPOSITORY / "src/anti_slop_python",
        workspace / "tool/anti_slop_python",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (workspace / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    (workspace / "smoke.py").write_text(SMOKE, encoding="utf-8")
    (workspace / "lint.py").write_text(LINT, encoding="utf-8")
    prompt = (
        HERE.joinpath("prompt.md").read_text()
        + f"\nWorkspace: {workspace}\nPython executable: {sys.executable}\n\n"
        + HERE.joinpath(f"{condition}.md").read_text()
    )
    (workspace / "prompt.txt").write_text(prompt, encoding="utf-8")
    immutable = [
        workspace / "before/order_report.py",
        workspace / "pyproject.toml",
        workspace / "smoke.py",
        workspace / "lint.py",
        workspace / "prompt.txt",
        *sorted((workspace / "tool").rglob("*.py")),
    ]
    manifest = {
        "condition": condition,
        "prepared_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "evaluator_sha256": digest(
            REPOSITORY / "tests/test_order_report_refactoring.py"
        ),
        "immutable_sha256": {
            str(path.relative_to(workspace)): digest(path) for path in immutable
        },
    }
    (workspace / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(prompt)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("condition", choices=["control", "linter"])
    args = parser.parse_args()
    prepare(args.workspace.resolve(), args.condition)


if __name__ == "__main__":
    main()
