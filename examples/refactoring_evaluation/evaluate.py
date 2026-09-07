"""Replay withheld checks on an arbitrary saved refactor, without model calls."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
TEST_FILE = REPOSITORY / "tests/test_order_report_refactoring.py"
IMPORT_MODES = REPOSITORY / "tests/test_order_report_import_modes.py"


def module_metrics(candidate: Path) -> list[dict[str, str | int | list[str]]]:
    modules = []
    for path in sorted(candidate.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        parse_error = ""
        try:
            tree = ast.parse(source)
        except SyntaxError as error:
            tree = ast.Module(body=[], type_ignores=[])
            parse_error = str(error)
        modules.append(
            {
                "path": str(path.relative_to(candidate)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "lines": source.count("\n")
                + bool(source and not source.endswith("\n")),
                "parse_error": parse_error,
                "definitions": [
                    node.name
                    for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                ],
                "imports": [
                    ast.unparse(node)
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                ],
            }
        )
    return modules


def evaluate(
    candidate: Path,
    output: Path,
    tool_path: Path | None = None,
    *,
    include_import_modes: bool = False,
) -> int:
    output.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment["ANTI_SLOP_REFACTOR_CANDIDATE"] = str(candidate)
    if tool_path is not None:
        environment["PYTHONPATH"] = str(tool_path.resolve())
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(TEST_FILE),
            *([str(IMPORT_MODES)] if include_import_modes else []),
            "-q",
            f"--junitxml={output / 'tests.xml'}",
        ],
        cwd=candidate.parent,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    (output / "pytest.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    cases = []
    if (output / "tests.xml").exists():
        for case in ET.parse(output / "tests.xml").iter("testcase"):
            cases.append(
                {
                    "name": case.attrib["name"],
                    "status": "passed" if len(case) == 0 else case[0].tag,
                    "message": ""
                    if len(case) == 0
                    else case[0].attrib.get("message", ""),
                }
            )
    report = {
        "evaluator_sha256": hashlib.sha256(TEST_FILE.read_bytes()).hexdigest(),
        "import_modes_sha256": hashlib.sha256(IMPORT_MODES.read_bytes()).hexdigest()
        if include_import_modes
        else None,
        "pytest_exit_code": result.returncode,
        "tests": cases,
        "modules": module_metrics(candidate),
    }
    (output / "results.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "exit_code": result.returncode,
                "passed": sum(case["status"] == "passed" for case in cases),
                "failed": [
                    case["name"] for case in cases if case["status"] != "passed"
                ],
            },
            indent=2,
        )
    )
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--tool-path", type=Path)
    parser.add_argument("--include-import-modes", action="store_true")
    args = parser.parse_args()
    raise SystemExit(
        evaluate(
            args.candidate.resolve(),
            args.output.resolve(),
            args.tool_path,
            include_import_modes=args.include_import_modes,
        )
    )


if __name__ == "__main__":
    main()
