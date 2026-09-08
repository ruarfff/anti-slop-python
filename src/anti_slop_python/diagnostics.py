from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_ANNOTATION_GUIDANCE = (
    "Declare the actual parameter and return types.",
    "Preserve existing type information when moving or refactoring code.",
    "Do not use Any, broad object types, or casts merely to satisfy this check.",
)

_GUIDANCE: dict[str, tuple[str, ...]] = {
    "SPY001": (
        "Describe the actual data with concrete types, TypedDict, or a dataclass.",
        "Validate untrusted data at the boundary; narrow unknown values before use.",
        "Do not remove annotations or hide Any behind aliases, casts,"
        " or bare containers.",
    ),
    "SPY002": (
        "Use direct attribute access for a known interface.",
        "For runtime choices, use an explicit mapping of supported operations.",
        "Preserve missing-value behavior explicitly.",
        "Do not replace this call with __dict__, vars(), or a reflection wrapper.",
    ),
    "SPY003": (
        "Separate distinct responsibilities into cohesive modules"
        " with clear interfaces.",
        "Keep closely related code together and preserve public APIs and behavior.",
        "Preserve validation order, side effects, and type information"
        " when moving code.",
        "Verify package and standalone imports where supported, plus each entry point.",
        "Check that every supported import mode exposes the full public API.",
        "Do not compress code, remove useful comments, split at arbitrary line counts,",
        "or move unrelated code into a generic helpers module to satisfy this limit.",
    ),
    "C901": (
        "Simplify the decision model; extract cohesive operations"
        " with explicit inputs.",
        "Use a lookup table only when the branches represent a data mapping.",
        "Preserve edge cases; do not hide branches in lambdas or raise the limit.",
    ),
    "F401": (
        "Check whether this import is part of the public API before removing it.",
        "For public re-exports, keep named imports and declare them in __all__.",
        "Keep the full public API in every supported import mode.",
        "Do not remove public exports or replace named imports with wildcard imports.",
    ),
    "F403": (
        "Import each required name explicitly so dependencies remain visible.",
        "For public re-exports, keep named imports and declare them in __all__.",
        "Preserve the public API; do not use wildcard imports to hide other findings.",
    ),
    "PLR0915": (
        "Separate meaningful steps into focused functions"
        " with clear inputs and results.",
        "Keep related work together and preserve ordering, side effects, and behavior.",
        "Do not pack statements onto fewer lines or split into arbitrary helpers.",
    ),
    "TID251": (
        "Use an allowed API that meets the project's policy.",
        "When test isolation is needed, pass the dependency explicitly"
        " and test behavior.",
        "Do not hide the banned API behind aliases, wrappers, or dynamic imports.",
    ),
    "E722": (
        "Catch only the specific exceptions this operation can recover from.",
        "Keep the try block narrow; let unexpected failures and interrupts propagate.",
        "Do not replace bare except with Exception or BaseException just to pass.",
    ),
    "BLE001": (
        "Catch specific recoverable errors and keep the try block narrow.",
        "If recovery is impossible, let the error propagate.",
        "Do not add logging or return a default merely to silence the rule.",
    ),
}


@dataclass(frozen=True, order=True)
class Diagnostic:
    """A source location and the check that failed there."""

    path: Path
    line: int
    column: int
    code: str
    message: str
    guidance: tuple[str, ...] = ()

    def __str__(self) -> str:
        summary = f"{self.path}:{self.line}:{self.column} {self.code} {self.message}"
        guidance = self.guidance or _GUIDANCE.get(self.code, ())
        if not guidance and self.code.startswith("ANN"):
            guidance = _ANNOTATION_GUIDANCE
        return "\n  ".join((summary, *guidance))
