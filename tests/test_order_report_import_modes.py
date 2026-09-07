"""Check public exports in fresh processes for each supported import mode."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ORIGINAL = (
    Path(__file__).parents[1]
    / "examples/basic_project/src/example_project/order_report.py"
)
REFACTORED = Path(
    os.environ.get(
        "ANTI_SLOP_REFACTOR_CANDIDATE", ORIGINAL.parent / "order_report_refactored"
    )
).resolve()


@pytest.mark.parametrize("mode", ["package", "standalone"])
def test_preserves_exports_in_each_import_mode(tmp_path: Path, mode: str) -> None:
    names = []
    for node in ast.parse(ORIGINAL.read_text()).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            names.extend(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name) and target.id.isupper()
            )
    for script in [ORIGINAL, REFACTORED / "order_report.py"]:
        root = script.parent if mode == "standalone" else script.parent.parent
        module = (
            "order_report"
            if mode == "standalone"
            else f"{script.parent.name}.order_report"
        )
        probe = (
            "import importlib, json, sys\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "namespace = vars(importlib.import_module(sys.argv[2]))\n"
            "names = json.loads(sys.argv[3])\n"
            "print(json.dumps([name for name in names if name not in namespace]))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe, str(root), module, json.dumps(names)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == [], f"{mode}: {result.stdout}"
