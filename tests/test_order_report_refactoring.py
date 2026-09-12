"""Compare the agent's refactor with the preserved before-fix example."""

from __future__ import annotations

import ast
import csv
import hashlib
import importlib
import inspect
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from anti_slop_python.cli import main

EXAMPLE_SOURCE = Path(__file__).parents[1] / "examples" / "basic_project" / "src"
ORIGINAL = EXAMPLE_SOURCE / "example_project" / "order_report.py"
REFACTORED = ORIGINAL.parent / "order_report_refactored"
BEFORE_SHA256 = "29d3ce2a3d1263a2976222833704050da85b22a2e66b733c35ee5f8d8f8ac223"
EXPORT_NAMES = {"report.txt", "invoices.csv", "stock.csv", "summary.json"}


def _run(script: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(script), *arguments],
        capture_output=True,
        check=False,
    )


def _compare_exports(before: Path, after: Path) -> None:
    assert {path.name for path in before.iterdir()} == EXPORT_NAMES
    assert {path.name for path in after.iterdir()} == EXPORT_NAMES
    for name in EXPORT_NAMES:
        assert (after / name).read_bytes() == (before / name).read_bytes(), name


def test_preserves_original_example() -> None:
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == BEFORE_SHA256


def test_entire_refactored_directory_passes_policy(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([str(REFACTORED)]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_demo_output_and_exports_match(tmp_path: Path) -> None:
    before = tmp_path / "before"
    after = tmp_path / "after"
    baseline = _run(ORIGINAL, "--demo", "--output", str(before))
    candidate = _run(REFACTORED / "order_report.py", "--demo", "--output", str(after))

    assert baseline.returncode == candidate.returncode == 0
    assert baseline.stderr == candidate.stderr == b""
    assert baseline.stdout == candidate.stdout
    assert b"Grand total: USD 63.97" in candidate.stdout
    _compare_exports(before, after)


@pytest.mark.parametrize("arguments", [(), ("--help",), ("--unknown",)])
def test_cli_help_and_argument_errors_match(arguments: tuple[str, ...]) -> None:
    baseline = _run(ORIGINAL, *arguments)
    candidate = _run(REFACTORED / "order_report.py", *arguments)

    assert candidate.returncode == baseline.returncode
    assert candidate.stdout == baseline.stdout
    assert candidate.stderr == baseline.stderr


def test_public_api_parameters_and_demo_values_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(EXAMPLE_SOURCE))
    original = importlib.import_module("example_project.order_report")
    refactored = importlib.import_module(
        "example_project.order_report_refactored.order_report"
    )
    before = vars(original)
    after = vars(refactored)
    tree = ast.parse(ORIGINAL.read_text())
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            assert node.name in after, node.name
            assert inspect.get_annotations(after[node.name]).keys() == (
                inspect.get_annotations(before[node.name]).keys()
            ), node.name
            expected = inspect.signature(before[node.name])
            actual = inspect.signature(after[node.name])
            assert list(actual.parameters) == list(expected.parameters), node.name
            for name, parameter in expected.parameters.items():
                assert actual.parameters[name].replace(
                    annotation=inspect.Parameter.empty
                ) == parameter.replace(annotation=inspect.Parameter.empty), node.name
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    assert after[target.id] == before[target.id], target.id
    assert asdict(refactored.demo_report()) == asdict(original.demo_report())


def _input_tables() -> dict[str, list[list[str]]]:
    return {
        "customers": [
            ["customer_id", "name", "email", "city", "country"],
            ["C1", "Example, Buyer", "buyer@example.invalid", "Austin", "US"],
            ["C2", "Second Buyer", "second@example.invalid", "Dublin", "IE"],
        ],
        "products": [
            ["sku", "name", "category", "unit_price", "stock"],
            ["A", "Notebook", "stationery", "25.00", "1"],
            ["B", "Pen", "stationery", "2.345", "9"],
        ],
        "orders": [
            ["order_id", "customer_id", "placed_on", "shipping", "discount_percent"],
            ["O2", "C1", "2026-01-02", "express", "10"],
            ["O1", "C2", "2026-01-01", "standard", "0"],
            ["O3", "C1", "2026-01-02", "pickup", "100"],
            ["O4", "C2", "2026-01-02", "standard", "0"],
            ["O5", "C1", "2026-01-02", "standard", "10"],
        ],
        "order_lines": [
            ["order_id", "sku", "quantity"],
            ["O2", "A", "1"],
            ["O2", "B", "3"],
            ["O1", "A", "4"],
            ["O3", "B", "1"],
            ["O4", "A", "1"],
            ["O5", "A", "4"],
        ],
    }


def _write_inputs(directory: Path, tables: dict[str, list[list[str]]]) -> None:
    directory.mkdir()
    for name, rows in tables.items():
        with (directory / f"{name}.csv").open(
            "w", encoding="utf-8", newline=""
        ) as stream:
            csv.writer(stream).writerows(rows)


@pytest.mark.parametrize("empty", [False, True])
def test_csv_workflow_and_exports_match(tmp_path: Path, empty: bool) -> None:
    tables = _input_tables()
    if empty:
        tables["orders"] = tables["orders"][:1]
        tables["order_lines"] = tables["order_lines"][:1]
    inputs = tmp_path / "input"
    _write_inputs(inputs, tables)
    before = tmp_path / "before"
    after = tmp_path / "after"

    baseline = _run(ORIGINAL, "--input", str(inputs), "--output", str(before))
    candidate = _run(
        REFACTORED / "order_report.py", "--input", str(inputs), "--output", str(after)
    )

    assert baseline.returncode == candidate.returncode == 0
    assert baseline.stderr == candidate.stderr == b""
    assert candidate.stdout == baseline.stdout
    _compare_exports(before, after)


@pytest.mark.parametrize(
    ("table", "row", "column", "value"),
    [
        ("order_lines", 1, 2, "0"),
        ("order_lines", 1, 2, "-1"),
        ("order_lines", 1, 2, "invalid"),
        ("order_lines", 1, 1, "UNKNOWN"),
        ("order_lines", 1, 0, "UNKNOWN"),
        ("orders", 1, 1, "UNKNOWN"),
        ("orders", 1, 2, "not-a-date"),
        ("orders", 1, 3, "unknown"),
        ("orders", 1, 4, "101"),
        ("orders", 1, 4, "NaN"),
        ("orders", 1, 4, "-1"),
        ("products", 1, 3, "Infinity"),
        ("products", 1, 3, "invalid"),
        ("products", 1, 4, "-1"),
        ("customers", 1, 1, " "),
    ],
)
def test_invalid_values_preserve_failure(
    tmp_path: Path, table: str, row: int, column: int, value: str
) -> None:
    tables = _input_tables()
    tables[table][row][column] = value
    inputs = tmp_path / "input"
    _write_inputs(inputs, tables)

    baseline = _run(ORIGINAL, "--input", str(inputs))
    candidate = _run(REFACTORED / "order_report.py", "--input", str(inputs))

    assert baseline.returncode == candidate.returncode == 1
    assert baseline.stdout == candidate.stdout == b""
    # Traceback paths change as code moves; exception type and message must not.
    assert candidate.stderr.splitlines()[-1] == baseline.stderr.splitlines()[-1]


@pytest.mark.parametrize("table", ["customers", "products", "orders"])
def test_duplicate_records_preserve_failure(tmp_path: Path, table: str) -> None:
    tables = _input_tables()
    tables[table].append(tables[table][1].copy())
    inputs = tmp_path / "input"
    _write_inputs(inputs, tables)

    baseline = _run(ORIGINAL, "--input", str(inputs))
    candidate = _run(REFACTORED / "order_report.py", "--input", str(inputs))

    assert baseline.returncode == candidate.returncode == 1
    assert baseline.stdout == candidate.stdout == b""
    assert candidate.stderr.splitlines()[-1] == baseline.stderr.splitlines()[-1]


def test_validation_order_preserves_first_failure(tmp_path: Path) -> None:
    tables = _input_tables()
    tables["customers"][1][1] = ""
    tables["orders"][1][4] = "101"
    inputs = tmp_path / "input"
    _write_inputs(inputs, tables)

    baseline = _run(ORIGINAL, "--input", str(inputs))
    candidate = _run(REFACTORED / "order_report.py", "--input", str(inputs))

    assert baseline.returncode == candidate.returncode == 1
    assert baseline.stdout == candidate.stdout == b""
    assert candidate.stderr.splitlines()[-1] == baseline.stderr.splitlines()[-1]
