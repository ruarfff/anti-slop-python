from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from anti_slop_python.diagnostics import Diagnostic
from anti_slop_python.ruff_policy import (
    _RECOMMENDED_RULES,
    RuffFailure,
    RuffSettings,
    configuration_arguments,
    default_arguments,
    parse_settings,
    policy_notices_for_scopes,
    settings_scopes,
)


@dataclass(frozen=True)
class RuffCheckResult:
    """Ruff diagnostics and advisory policy output for one invocation."""

    diagnostics: tuple[Diagnostic, ...]
    notices: tuple[str, ...]
    warnings: tuple[str, ...]


def check_with_ruff(
    _paths: Sequence[Path], python_files: Sequence[Path]
) -> RuffCheckResult:
    """Run Ruff with anti-slop-python defaults and project-configured overrides."""

    diagnostics: list[Diagnostic] = []
    warnings: list[str] = []
    noqa_notices: list[str] = []
    scopes = settings_scopes(python_files)
    effective_settings: list[RuffSettings] = []
    for configuration, files in scopes:
        project_root = configuration.parent if configuration is not None else None
        config_arguments = configuration_arguments(configuration)
        included_files = _included_files(files, config_arguments, cwd=project_root)
        if not included_files:
            continue
        baseline = _resolved_settings(
            included_files[0], config_arguments, cwd=project_root
        )
        arguments = (*config_arguments, *default_arguments(baseline))
        for targets in _path_batches(included_files):
            normal = _ruff_diagnostics(
                targets, arguments, python_files, cwd=project_root
            )
            diagnostics.extend(normal.diagnostics)
            warnings.extend(normal.warnings)
            audit = _ruff_diagnostics(
                targets, ("--ignore-noqa", *arguments), python_files, cwd=project_root
            )
            noqa_notices.extend(_noqa_notices(normal.diagnostics, audit.diagnostics))
        effective_settings.append(
            _resolved_settings(included_files[0], arguments, cwd=project_root)
        )

    notices = (*policy_notices_for_scopes(effective_settings), *noqa_notices)
    return RuffCheckResult(
        tuple(sorted(set(diagnostics))),
        notices,
        tuple(dict.fromkeys(warnings)),
    )


@dataclass(frozen=True)
class _RuffDiagnostics:
    diagnostics: tuple[Diagnostic, ...]
    warnings: tuple[str, ...]


def _ruff_diagnostics(
    targets: Sequence[Path],
    arguments: Sequence[str],
    python_files: Sequence[Path],
    *,
    cwd: Path | None = None,
) -> _RuffDiagnostics:
    completed = _run_ruff(
        "check",
        "--output-format",
        "json",
        "--no-fix",
        "--no-fix-only",
        "--exit-zero",
        "--force-exclude",
        *arguments,
        "--",
        *(str(path.resolve()) for path in targets),
        cwd=cwd,
    )
    return _RuffDiagnostics(
        diagnostics=_parse_diagnostics(completed.stdout, python_files),
        warnings=tuple(line for line in completed.stderr.splitlines() if line),
    )


def _noqa_notices(
    normal: Sequence[Diagnostic], audit: Sequence[Diagnostic]
) -> tuple[str, ...]:
    normal_keys = {(item.path, item.line, item.column, item.code) for item in normal}
    return tuple(
        f"{item.code} is suppressed by noqa at {item.path}:{item.line}; "
        "recommended for checked files"
        for item in audit
        if item.code in _RECOMMENDED_RULES
        and (item.path, item.line, item.column, item.code) not in normal_keys
    )


def _run_ruff(
    *arguments: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    for name in ("RUFF_FIX", "RUFF_FIX_ONLY", "RUFF_OUTPUT_FILE", "RUFF_OUTPUT_FORMAT"):
        environment.pop(name, None)

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "ruff", *arguments],
            capture_output=True,
            check=False,
            env=environment,
            cwd=cwd,
            text=True,
        )
    except OSError as error:
        raise RuffFailure(f"Ruff failed: {error}") from error

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuffFailure(f"Ruff failed: {detail or 'unknown error'}")
    return completed


def _parse_diagnostics(
    output: str, python_files: Sequence[Path]
) -> tuple[Diagnostic, ...]:
    try:
        items = json.loads(output)
    except json.JSONDecodeError as error:
        raise RuffFailure(f"Ruff returned invalid JSON: {error.msg}") from error
    if not isinstance(items, list):
        raise RuffFailure("Ruff returned invalid JSON: expected a diagnostic list")

    display_paths = {path.resolve(): path for path in python_files}
    diagnostics: list[Diagnostic] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        filename = Path(str(item.get("filename", "<unknown>")))
        if item.get("code") == "invalid-syntax" and filename.resolve() in display_paths:
            continue
        location = item.get("location")
        if not isinstance(location, dict):
            raise RuffFailure("Ruff returned a diagnostic without a source location")
        path = display_paths.get(filename.resolve(), _display_path(filename))
        diagnostics.append(
            Diagnostic(
                path=path,
                line=int(location["row"]),
                column=int(location["column"]),
                code=str(item.get("code") or "Ruff"),
                message=str(item.get("message") or "Ruff violation"),
            )
        )
    return tuple(sorted(diagnostics))


def _display_path(path: Path) -> Path:
    try:
        return path.relative_to(Path.cwd())
    except ValueError:
        return path


def _included_files(
    files: Sequence[Path],
    configuration_arguments: Sequence[str],
    *,
    cwd: Path | None = None,
) -> tuple[Path, ...]:
    included_paths: set[Path] = set()
    for targets in _path_batches(files):
        completed = _run_ruff(
            "check",
            "--show-files",
            "--force-exclude",
            *configuration_arguments,
            "--",
            *(str(path.resolve()) for path in targets),
            cwd=cwd,
        )
        included_paths.update(
            Path(line).resolve() for line in completed.stdout.splitlines()
        )
    return tuple(path for path in files if path.resolve() in included_paths)


def _path_batches(
    files: Sequence[Path], batch_size: int = 500
) -> tuple[tuple[Path, ...], ...]:
    return tuple(
        tuple(files[index : index + batch_size])
        for index in range(0, len(files), batch_size)
    )


def _resolved_settings(
    file: Path, extra_arguments: Sequence[str] = (), *, cwd: Path | None = None
) -> RuffSettings:
    completed = _run_ruff(
        "check", "--show-settings", *extra_arguments, "--", str(file.resolve()), cwd=cwd
    )
    return parse_settings(completed.stdout)
