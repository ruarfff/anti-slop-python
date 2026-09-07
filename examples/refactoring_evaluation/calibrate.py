"""Check the evaluator against a good refactor and deliberate defects."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from evaluate import REPOSITORY, evaluate

EXAMPLE = REPOSITORY / "examples/basic_project/src/example_project"
POLICY = "test_entire_refactored_directory_passes_policy"
CONTRACT = "test_public_api_parameters_and_demo_values_match"
DEMO = "test_demo_output_and_exports_match"


def calibrate(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    for name in ["good", "unchanged", "empty", "annotation", "tax"]:
        workspace = output / name
        candidate = workspace / "order_report_refactored"
        if name in {"good", "annotation", "tax"}:
            shutil.copytree(
                EXAMPLE / "order_report_refactored",
                candidate,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        else:
            candidate.mkdir(parents=True)
            content = (EXAMPLE / "order_report.py").read_bytes()
            (candidate / "order_report.py").write_bytes(
                content if name == "unchanged" else b""
            )
        (workspace / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
        if name == "annotation":
            path = candidate / "presentation.py"
            old = "def format_money(value: Decimal) -> str:"
            assert old in path.read_text()
            path.write_text(path.read_text().replace(old, "def format_money(value):"))
        if name == "tax":
            path = candidate / "pricing.py"
            old = 'TAX_RATE = Decimal("0.08")'
            assert old in path.read_text()
            path.write_text(path.read_text().replace(old, 'TAX_RATE = Decimal("0.09")'))
        evaluate(candidate, workspace / "evaluation")
        report = json.loads((workspace / "evaluation/results.json").read_text())
        results[name] = {
            "evaluator_sha256": report["evaluator_sha256"],
            "passed": sum(case["status"] == "passed" for case in report["tests"]),
            "failed": [
                case["name"] for case in report["tests"] if case["status"] != "passed"
            ],
        }
    assert results["good"]["failed"] == []
    assert results["unchanged"]["failed"] == [POLICY]
    assert DEMO in results["empty"]["failed"]
    assert POLICY not in results["empty"]["failed"]
    assert set(results["annotation"]["failed"]) == {POLICY, CONTRACT}
    assert DEMO in results["tax"]["failed"]
    assert POLICY not in results["tax"]["failed"]
    (output / "calibration.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    calibrate(args.output.resolve())


if __name__ == "__main__":
    main()
