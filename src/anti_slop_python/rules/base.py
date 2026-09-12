from __future__ import annotations

import ast
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from anti_slop_python.configuration import ModuleSizeSettings
from anti_slop_python.diagnostics import Diagnostic


@dataclass(frozen=True)
class Rule:
    """Metadata and checker function for one rule."""

    code: str
    name: str
    message: str
    check: Callable[[RuleContext], Iterable[Diagnostic]]


@dataclass
class RuleContext:
    """Parsed source and the shared import analysis used by rules."""

    path: Path
    tree: ast.AST
    source: str
    settings: ModuleSizeSettings = field(default_factory=ModuleSizeSettings)
    imports: dict[str, str] = field(init=False)

    def __post_init__(self) -> None:
        self.imports = _collect_imports(self.tree)

    def qualified_name(self, node: ast.AST) -> str | None:
        """Resolve a simple imported name without full semantic analysis."""

        name = _dotted_name(node)
        if name is None:
            return None

        first, separator, remainder = name.partition(".")
        resolved = self.imports.get(first, first)
        if separator:
            return f"{resolved}.{remainder}"
        return resolved

    def diagnostic(self, rule: Rule, node: ast.AST) -> Diagnostic:
        return Diagnostic(
            path=self.path,
            line=node.lineno,
            column=node.col_offset + 1,
            code=rule.code,
            message=rule.message,
        )


def _collect_imports(tree: ast.AST) -> dict[str, str]:
    imports: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".", 1)[0]
                target = alias.name if alias.asname else local_name
                imports[local_name] = target
        elif isinstance(node, ast.ImportFrom):
            dots = "." * (node.level or 0)
            if node.module:
                module_prefix = f"{dots}{node.module}."
            elif dots:
                module_prefix = f"{dots}"
            else:
                module_prefix = ""
            for alias in node.names:
                if alias.name == "*":
                    continue
                local_name = alias.asname or alias.name
                imports[local_name] = f"{module_prefix}{alias.name}"
    return imports


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        if parent is not None:
            return f"{parent}.{node.attr}"
    return None
