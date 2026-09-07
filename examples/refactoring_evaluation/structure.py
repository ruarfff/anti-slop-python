"""Report module dependencies and changes to the reference's definitions."""

from __future__ import annotations

import argparse
import ast
import graphlib
import json
from pathlib import Path

REFERENCE = (
    Path(__file__).resolve().parents[2]
    / "examples/basic_project/src/example_project/order_report.py"
)


def definitions(path: Path) -> dict[str, str]:
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in ast.parse(path.read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }


def inspect_structure(candidate: Path) -> dict:
    """Audit the flat layouts in this study; source review remains necessary."""
    before = definitions(REFERENCE)
    files = sorted(candidate.glob("*.py"))
    dependencies: dict[str, set[str]] = {path.stem: set() for path in files}
    after = {}
    wildcards = []
    for path in files:
        after.update(definitions(path))
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module in dependencies:
                dependencies[path.stem].add(node.module)
                if any(alias.name == "*" for alias in node.names):
                    wildcards.append(f"{path.name}:{node.lineno}")
    graph = {name: sorted(targets) for name, targets in dependencies.items()}
    try:
        order = list(graphlib.TopologicalSorter(graph).static_order())
        cycle = False
    except graphlib.CycleError:
        order = []
        cycle = True
    return {
        "graph": graph,
        "cycle": cycle,
        "topological_order": order,
        "wildcard_imports": wildcards,
        "original_definition_count": len(before),
        "changed_definitions": [
            name for name in before if name in after and before[name] != after[name]
        ],
        "missing_definitions": sorted(before.keys() - after.keys()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect_structure(args.candidate), indent=2))


if __name__ == "__main__":
    main()
