from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from anti_slop_python.checker import check_file
from anti_slop_python.configuration import (
    ConfigurationError,
    ModuleSizeSettings,
    load_settings,
)
from anti_slop_python.ruff_integration import RuffFailure, check_with_ruff

_IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "venv",
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)

    try:
        files = list(_python_files(arguments.paths))
    except ValueError as error:
        parser.error(str(error))

    try:
        settings_cache: dict[Path, ModuleSizeSettings] = {}
        diagnostics = [
            diagnostic
            for path in files
            for diagnostic in check_file(
                path, settings=load_settings(path, settings_cache)
            )
        ]
        ruff_result = check_with_ruff(arguments.paths, files)
    except (ConfigurationError, RuffFailure) as error:
        print(f"anti-slop-python: {error}", file=sys.stderr)
        return 2

    for warning in ruff_result.warnings:
        print(warning, file=sys.stderr)
    for notice in ruff_result.notices:
        print(f"anti-slop-python policy notice: {notice}", file=sys.stderr)

    diagnostics.extend(ruff_result.diagnostics)
    for diagnostic in sorted(diagnostics):
        print(diagnostic)
    return 1 if diagnostics else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anti-slop-python",
        description="Reject Python patterns that weaken architectural evidence.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path(".")],
        help="Python files or directories to check (default: current directory)",
    )
    return parser


def _python_files(paths: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for path in paths:
        if not path.exists():
            raise ValueError(f"path does not exist: {path}")
        candidates = [path] if path.is_file() else _walk_python_files(path)
        for candidate in candidates:
            if candidate.suffix != ".py":
                continue
            identity = candidate.resolve()
            if identity not in seen:
                seen.add(identity)
                yield candidate


def _walk_python_files(root: Path) -> Iterable[Path]:
    for directory, subdirectories, filenames in os.walk(root):
        subdirectories[:] = sorted(
            name for name in subdirectories if name not in _IGNORED_DIRECTORIES
        )
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield Path(directory, filename)
