from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_ANNOTATION_GUIDANCE = (
    "Declare the actual parameter and return types.",
    "Preserve existing type information when moving or refactoring code.",
    "Do not use Any, broad object types, or casts merely to satisfy this check.",
)

_ASYNC_BLOCKING_IMPACT = (
    "This call can block the event-loop thread, stalling other requests and tasks."
)
_ASYNC_FRAMEWORK_GUIDANCE = (
    "Use APIs from the active async framework; the examples below are for asyncio."
)
_ASYNC_BLOCKING_SHORTCUT = (
    "Do not hide it in a helper or async wrapper; asyncio.create_task does not"
    " offload blocking work."
)
_ASYNC_HTTP_GUIDANCE = (
    _ASYNC_BLOCKING_IMPACT,
    _ASYNC_FRAMEWORK_GUIDANCE,
    "Use an async HTTP client and await the request.",
    "If the client must stay synchronous, await asyncio.to_thread(...) for the"
    " blocking operation; check client thread safety.",
    "Preserve timeouts, status checks, response handling, and client cleanup.",
    _ASYNC_BLOCKING_SHORTCUT,
)
_ASYNC_PROCESS_GUIDANCE = (
    _ASYNC_BLOCKING_IMPACT,
    _ASYNC_FRAMEWORK_GUIDANCE,
    "Use await asyncio.create_subprocess_exec(...) to start the process.",
    "Use asyncio.create_subprocess_shell only when shell semantics are required.",
    "Await communicate() or wait() when completion is required.",
    "Preserve arguments, exit checks, output handling, timeouts, and cleanup.",
    _ASYNC_BLOCKING_SHORTCUT,
)
_ASYNC_FILE_GUIDANCE = (
    _ASYNC_BLOCKING_IMPACT,
    _ASYNC_FRAMEWORK_GUIDANCE,
    "Use an async file API, or await asyncio.to_thread(...) for the complete"
    " file operation.",
    "Keep opening, reading or writing, and closing in the offloaded operation;"
    " offloading only open() leaves later I/O on the event loop.",
    "Preserve file modes, encoding, error behavior, and resource cleanup.",
    _ASYNC_BLOCKING_SHORTCUT,
)

_GUIDANCE: dict[str, tuple[str, ...]] = {
    "ASYNC210": _ASYNC_HTTP_GUIDANCE,
    "ASYNC212": _ASYNC_HTTP_GUIDANCE,
    "ASYNC220": _ASYNC_PROCESS_GUIDANCE,
    "ASYNC221": _ASYNC_PROCESS_GUIDANCE,
    "ASYNC222": (
        _ASYNC_BLOCKING_IMPACT,
        _ASYNC_FRAMEWORK_GUIDANCE,
        "Await wait() or communicate() on an existing asyncio subprocess.",
        "For a child managed by a synchronous API, await asyncio.to_thread(...)"
        " around the blocking wait; do not start a replacement process.",
        "Preserve child identity, exit status, error handling, and cleanup.",
        _ASYNC_BLOCKING_SHORTCUT,
    ),
    "ASYNC230": _ASYNC_FILE_GUIDANCE,
    "ASYNC240": _ASYNC_FILE_GUIDANCE,
    "ASYNC250": (
        _ASYNC_BLOCKING_IMPACT,
        _ASYNC_FRAMEWORK_GUIDANCE,
        "Read interactive input outside the event loop, or await"
        " asyncio.to_thread(input, ...) when a worker thread may wait for input.",
        "Cancelling the await does not stop an input call already running in a thread.",
        "Preserve prompt and EOF behavior.",
        _ASYNC_BLOCKING_SHORTCUT,
    ),
    "ASYNC251": (
        _ASYNC_BLOCKING_IMPACT,
        _ASYNC_FRAMEWORK_GUIDANCE,
        "Use await asyncio.sleep(delay) to yield during the delay.",
        "Keep the intended delay and let task cancellation propagate;"
        " do not busy-wait.",
        _ASYNC_BLOCKING_SHORTCUT,
    ),
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
