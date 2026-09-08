from __future__ import annotations

from collections.abc import Iterable
from io import StringIO

from anti_slop_python.diagnostics import Diagnostic
from anti_slop_python.rules.base import Rule, RuleContext

_TEST_GUIDANCE = (
    "Group tests by the behavior or component they verify.",
    "Keep each scenario readable and preserve assertions and edge cases.",
    "Do not remove coverage, compress cases, or hide setup in shared fixtures",
    "merely to satisfy this limit.",
)


def _check(context: RuleContext) -> Iterable[Diagnostic]:
    lines = sum(1 for _ in StringIO(context.source, newline=None))
    is_test = context.settings.is_test_file(context.path)
    limit = (
        context.settings.max_test_module_lines
        if is_test
        else context.settings.max_module_lines
    )
    if lines > limit:
        kind = "test module" if is_test else "module"
        yield Diagnostic(
            path=context.path,
            line=1,
            column=1,
            code=RULE.code,
            message=f"Too many lines in {kind} ({lines} > {limit})",
            guidance=_TEST_GUIDANCE if is_test else (),
        )


RULE = Rule(
    code="SPY003",
    name="too-many-module-lines",
    message="Too many lines in module",
    check=_check,
)
