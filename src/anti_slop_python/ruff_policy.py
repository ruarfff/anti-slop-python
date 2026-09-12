from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_RECOMMENDED_RULES = (
    "C901",
    "PLR0915",
    "TID251",
    "E722",
    "BLE001",
    "F403",
    "ANN001",
    "ANN002",
    "ANN003",
    "ANN201",
    "ANN202",
    "ANN204",
    "ANN205",
    "ANN206",
    "ANN401",
)
_RECOMMENDED_BANNED_APIS = {
    "mock.patch": "Avoid patching state. Pass the dependency explicitly instead.",
    "unittest.mock.patch": (
        "Avoid patching state. Pass the dependency explicitly instead."
    ),
}
_MAX_COMPLEXITY = 10
_MAX_STATEMENTS = 40
_RULE_CODE = re.compile(r"\(([A-Z][A-Z0-9]*\d+)\),?$")


class RuffFailure(RuntimeError):
    """Raised when Ruff cannot complete a check or expose its settings."""


@dataclass(frozen=True)
class RuffSettings:
    enabled_rules: frozenset[str]
    max_complexity: int
    max_statements: int
    banned_apis: frozenset[str]
    banned_api_messages: tuple[tuple[str, str], ...]
    per_file_ignores: tuple[tuple[str, frozenset[str]], ...]
    path: Path | None


def settings_scopes(
    files: Sequence[Path],
) -> tuple[tuple[Path | None, tuple[Path, ...]], ...]:
    scopes: dict[Path | None, list[Path]] = {}
    config_cache: dict[Path, Path | None] = {}
    for file in files:
        scopes.setdefault(ruff_config_for(file, config_cache), []).append(file)
    return tuple(
        (configuration, tuple(scope)) for configuration, scope in scopes.items()
    )


def configuration_arguments(path: Path | None) -> tuple[str, ...]:
    if path is None:
        return ("--isolated",)
    return ("--config", str(path))


def ruff_config_for(file: Path, cache: dict[Path, Path | None]) -> Path | None:
    return ruff_config_for_directory(file.resolve().parent, cache)


def ruff_config_for_directory(
    directory: Path, cache: dict[Path, Path | None]
) -> Path | None:
    if directory in cache:
        return cache[directory]

    for filename in (".ruff.toml", "ruff.toml"):
        candidate = directory / filename
        if candidate.is_file():
            cache[directory] = candidate
            return candidate

    pyproject = directory / "pyproject.toml"
    if pyproject.is_file():
        try:
            configuration = tomllib.loads(pyproject.read_text())
        except (OSError, tomllib.TOMLDecodeError):
            cache[directory] = pyproject
            return pyproject
        tool = configuration.get("tool")
        if isinstance(tool, dict) and isinstance(tool.get("ruff"), dict):
            cache[directory] = pyproject
            return pyproject
    parent = directory.parent
    resolved = None if parent == directory else ruff_config_for_directory(parent, cache)
    cache[directory] = resolved
    return resolved


def parse_settings(output: str) -> RuffSettings:
    enabled_rules = _rule_codes(
        _setting_block(output, "linter.rules.enabled", "[", "]")
    )
    banned_api_block = _setting_block(
        output, "linter.flake8_tidy_imports.banned_api", "{", "}"
    )
    banned_api_messages = _parse_banned_apis(banned_api_block)
    per_file_block = _setting_block(output, "linter.per_file_ignores", "{", "}")
    raw_path = _optional_setting_value(output, "Settings path:")
    return RuffSettings(
        enabled_rules=enabled_rules,
        max_complexity=int(_setting_value(output, "linter.mccabe.max_complexity")),
        max_statements=int(_setting_value(output, "linter.pylint.max_statements")),
        banned_apis=frozenset(api for api, _ in banned_api_messages),
        banned_api_messages=banned_api_messages,
        per_file_ignores=_parse_per_file_ignores(per_file_block),
        path=Path(_quoted_value(raw_path)) if raw_path is not None else None,
    )


def default_arguments(settings: RuffSettings) -> tuple[str, ...]:
    ignored_selectors = _configured_ignore_selectors(settings.path)
    default_rules = [
        code
        for code in _RECOMMENDED_RULES
        if not any(_selector_matches(code, selector) for selector in ignored_selectors)
    ]
    arguments: list[str] = []
    if default_rules:
        arguments.extend(["--extend-select", ",".join(default_rules)])
    if not _configuration_defines_any(
        settings.path,
        (("lint", "mccabe", "max-complexity"), ("mccabe", "max-complexity")),
    ):
        arguments.extend(
            ["--config", f"lint.mccabe.max-complexity = {_MAX_COMPLEXITY}"]
        )
    if not _configuration_defines_any(
        settings.path,
        (("lint", "pylint", "max-statements"), ("pylint", "max-statements")),
    ):
        arguments.extend(
            ["--config", f"lint.pylint.max-statements = {_MAX_STATEMENTS}"]
        )

    if not _configuration_defines_any(
        settings.path,
        (
            ("lint", "flake8-tidy-imports", "banned-api"),
            ("flake8-tidy-imports", "banned-api"),
        ),
    ):
        entries = ", ".join(
            f"{json.dumps(api)} = {{ msg = {json.dumps(message)} }}"
            for api, message in sorted(_RECOMMENDED_BANNED_APIS.items())
        )
        arguments.extend(
            ["--config", f"lint.flake8-tidy-imports.banned-api = {{{entries}}}"]
        )
    return tuple(arguments)


def policy_notices_for_scopes(
    settings: Sequence[RuffSettings],
) -> tuple[str, ...]:
    multiple_scopes = len(settings) > 1
    notices: list[str] = []
    for resolved in settings:
        suffix = ""
        if multiple_scopes and resolved.path is not None:
            suffix = f" [Ruff settings: {resolved.path}]"
        notices.extend(f"{notice}{suffix}" for notice in _policy_notices(resolved))
    return tuple(notices)


def _configured_ignore_selectors(path: Path | None) -> tuple[str, ...]:
    selectors: list[str] = []
    for configuration in _configuration_chain(path):
        replacement = _lint_setting(configuration, "ignore")
        if isinstance(replacement, list):
            selectors = [str(value) for value in replacement]
        additions = _lint_setting(configuration, "extend-ignore")
        if isinstance(additions, list):
            selectors.extend(str(value) for value in additions)
    return tuple(selectors)


def _selector_matches(code: str, selector: str) -> bool:
    return selector == "ALL" or code.startswith(selector)


def _lint_setting(configuration: dict[str, object], name: str) -> object:
    lint = configuration.get("lint")
    hyphenated = name.replace("_", "-")
    underscored = name.replace("-", "_")
    if isinstance(lint, dict):
        if hyphenated in lint:
            return lint[hyphenated]
        if underscored in lint:
            return lint[underscored]
    if hyphenated in configuration:
        return configuration[hyphenated]
    if underscored in configuration:
        return configuration[underscored]
    return None


def _configuration_chain(
    path: Path | None, seen: frozenset[Path] = frozenset()
) -> tuple[dict[str, object], ...]:
    if path is None:
        return ()
    resolved_path = path.resolve()
    if resolved_path in seen:
        return ()
    try:
        document = tomllib.loads(resolved_path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return ()

    configuration: object = document
    if resolved_path.name == "pyproject.toml":
        configuration = document.get("tool", {}).get("ruff", {})
    if not isinstance(configuration, dict):
        return ()

    base: tuple[dict[str, object], ...] = ()
    extended = configuration.get("extend")
    if isinstance(extended, str):
        extended_path = Path(extended)
        if not extended_path.is_absolute():
            extended_path = resolved_path.parent / extended_path
        base = _configuration_chain(extended_path, seen | {resolved_path})
    return (*base, configuration)


def _configuration_defines_any(
    path: Path | None, setting_paths: Sequence[tuple[str, ...]]
) -> bool:
    return any(
        _configuration_defines(path, setting_path) for setting_path in setting_paths
    )


def _configuration_defines(
    path: Path | None,
    setting_path: tuple[str, ...],
) -> bool:
    return any(
        _mapping_has_path(configuration, setting_path)
        for configuration in _configuration_chain(path)
    )


def _mapping_has_path(mapping: dict[str, object], path: tuple[str, ...]) -> bool:
    current: object = mapping
    for part in path:
        if not isinstance(current, dict):
            return False
        hyphenated = part.replace("_", "-")
        underscored = part.replace("-", "_")
        if hyphenated in current:
            current = current[hyphenated]
        elif underscored in current:
            current = current[underscored]
        else:
            return False
    return True


def _setting_block(output: str, name: str, opener: str, closer: str) -> str:
    lines = output.splitlines()
    marker = f"{name} = {opener}"
    empty_marker = f"{marker}{closer}"
    for index, line in enumerate(lines):
        if line.strip() == empty_marker:
            return ""
        if line.strip() != marker:
            continue
        block: list[str] = []
        for candidate in lines[index + 1 :]:
            if candidate.strip() == closer:
                return "\n".join(block)
            block.append(candidate)
    raise RuffFailure("Ruff returned an unsupported resolved-settings format")


def _setting_value(output: str, name: str) -> str:
    value = _optional_setting_value(output, f"{name} =")
    if value is None:
        raise RuffFailure("Ruff returned an unsupported resolved-settings format")
    return value


def _optional_setting_value(output: str, marker: str) -> str | None:
    for line in output.splitlines():
        if line.strip().startswith(marker):
            return line.strip().removeprefix(marker).strip()
    return None


def _rule_codes(block: str) -> frozenset[str]:
    rules: set[str] = set()
    for line in block.splitlines():
        _add_rule_code(line.strip(), rules)
    return frozenset(rules)


def _parse_banned_apis(block: str) -> tuple[tuple[str, str], ...]:
    banned_apis: list[tuple[str, str]] = []
    for line in block.splitlines():
        api, separator, message = line.strip().removesuffix(",").partition(" = ")
        if separator:
            banned_apis.append((api, message))
    return tuple(banned_apis)


def _parse_per_file_ignores(
    block: str,
) -> tuple[tuple[str, frozenset[str]], ...]:
    ignores: list[tuple[str, frozenset[str]]] = []
    current_pattern: str | None = None
    current_rules: set[str] = set()
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("basename_matcher = "):
            if current_pattern is not None:
                ignores.append((current_pattern, frozenset(current_rules)))
            current_pattern = _quoted_value(stripped.partition(" = ")[2])
            current_rules = set()
        else:
            _add_rule_code(stripped, current_rules)
    if current_pattern is not None:
        ignores.append((current_pattern, frozenset(current_rules)))
    return tuple(ignores)


def _quoted_value(value: str) -> str:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    return str(parsed)


def _add_rule_code(line: str, destination: set[str]) -> None:
    match = _RULE_CODE.search(line)
    if match is not None:
        destination.add(match.group(1))


def _policy_notices(settings: RuffSettings) -> tuple[str, ...]:
    notices = _disabled_rule_notices(settings)
    notices.extend(_limit_notices(settings))
    notices.extend(_banned_api_notices(settings))
    notices.extend(_per_file_ignore_notices(settings))
    return tuple(notices)


def _disabled_rule_notices(settings: RuffSettings) -> list[str]:
    return [
        f"{code} is disabled; recommended: enabled"
        for code in _RECOMMENDED_RULES
        if code not in settings.enabled_rules
    ]


def _limit_notices(settings: RuffSettings) -> list[str]:
    notices: list[str] = []
    if "C901" in settings.enabled_rules and settings.max_complexity > _MAX_COMPLEXITY:
        notices.append(
            f"C901 allows complexity {settings.max_complexity}; "
            f"recommended maximum: {_MAX_COMPLEXITY}"
        )
    if (
        "PLR0915" in settings.enabled_rules
        and settings.max_statements > _MAX_STATEMENTS
    ):
        notices.append(
            f"PLR0915 allows {settings.max_statements} statements; "
            f"recommended maximum: {_MAX_STATEMENTS}"
        )
    return notices


def _banned_api_notices(settings: RuffSettings) -> list[str]:
    if "TID251" not in settings.enabled_rules:
        return []
    return [
        f"TID251 does not ban {api}; recommended: ban this API"
        for api in _RECOMMENDED_BANNED_APIS
        if not _api_is_banned(api, settings.banned_apis)
    ]


def _api_is_banned(api: str, banned_apis: frozenset[str]) -> bool:
    return any(api == banned or api.startswith(f"{banned}.") for banned in banned_apis)


def _per_file_ignore_notices(settings: RuffSettings) -> list[str]:
    notices: list[str] = []
    enabled_recommendations = settings.enabled_rules.intersection(_RECOMMENDED_RULES)
    for pattern, ignored_rules in settings.per_file_ignores:
        for code in _RECOMMENDED_RULES:
            if code in enabled_recommendations and code in ignored_rules:
                notices.append(
                    f"{code} is ignored for {pattern}; "
                    "recommended for all checked files"
                )
    return notices
