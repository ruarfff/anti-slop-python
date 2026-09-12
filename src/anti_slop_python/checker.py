from __future__ import annotations

import ast
import tokenize
from pathlib import Path

from anti_slop_python.configuration import ModuleSizeSettings, load_settings
from anti_slop_python.diagnostics import Diagnostic
from anti_slop_python.rules import RULES
from anti_slop_python.rules.base import RuleContext


def check_source(
    source: str,
    path: str | Path = "<unknown>",
    *,
    settings: ModuleSizeSettings | None = None,
) -> list[Diagnostic]:
    """Check source text with explicit settings or defaults, without config I/O."""

    source_path = Path(path)
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError as error:
        return [_syntax_error(source_path, error)]

    context = RuleContext(
        path=source_path,
        tree=tree,
        source=source,
        settings=settings if settings is not None else ModuleSizeSettings(),
    )
    diagnostics = [diagnostic for rule in RULES for diagnostic in rule.check(context)]
    return sorted(diagnostics)


def check_file(
    path: str | Path, *, settings: ModuleSizeSettings | None = None
) -> list[Diagnostic]:
    """Read and check one file, discovering configuration unless settings are given."""

    source_path = Path(path)
    try:
        with tokenize.open(source_path) as source_file:
            source = source_file.read()
    except (OSError, SyntaxError) as error:
        return [
            Diagnostic(
                path=source_path,
                line=1,
                column=1,
                code="IOError",
                message=str(error),
            )
        ]
    resolved = settings if settings is not None else load_settings(source_path)
    return check_source(source, source_path, settings=resolved)


def _syntax_error(path: Path, error: SyntaxError) -> Diagnostic:
    return Diagnostic(
        path=path,
        line=error.lineno or 1,
        column=error.offset or 1,
        code="SyntaxError",
        message=error.msg,
    )
