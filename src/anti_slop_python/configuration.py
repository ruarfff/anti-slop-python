from __future__ import annotations

import fnmatch
import tomllib
from dataclasses import dataclass
from pathlib import Path

_TEST_NAMES = ("test_*.py", "*_test.py", "conftest.py")
_OPTIONS = {"max-module-lines", "max-test-module-lines", "test-file-patterns"}


class ConfigurationError(ValueError):
    """Raised when native rule configuration cannot be read or is invalid."""


@dataclass(frozen=True)
class ModuleSizeSettings:
    max_module_lines: int = 500
    max_test_module_lines: int = 1500
    test_file_patterns: tuple[str, ...] = ()
    root: Path = Path(".")

    def is_test_file(self, path: Path) -> bool:
        if any(fnmatch.fnmatchcase(path.name, pattern) for pattern in _TEST_NAMES):
            return True
        if not self.test_file_patterns:
            return False
        try:
            relative = path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return False
        return any(
            fnmatch.fnmatchcase(relative, pattern)
            for pattern in self.test_file_patterns
        )


def load_settings(
    path: Path, cache: dict[Path, ModuleSizeSettings] | None = None
) -> ModuleSizeSettings:
    """Find the nearest native settings table, relative to the source file."""

    return _settings_for_directory(
        path.resolve().parent, {} if cache is None else cache
    )


def _settings_for_directory(
    directory: Path, cache: dict[Path, ModuleSizeSettings]
) -> ModuleSizeSettings:
    if directory in cache:
        return cache[directory]
    settings = _read_settings(directory / "pyproject.toml")
    if settings is None:
        settings = (
            ModuleSizeSettings()
            if directory.parent == directory
            else _settings_for_directory(directory.parent, cache)
        )
    cache[directory] = settings
    return settings


def _read_settings(path: Path) -> ModuleSizeSettings | None:
    try:
        with path.open("rb") as stream:
            document = tomllib.load(stream)
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ConfigurationError(f"Cannot read {path}: {error}") from error
    tool = document.get("tool", {})
    if not isinstance(tool, dict) or "anti-slop-python" not in tool:
        return None
    options = tool["anti-slop-python"]
    if not isinstance(options, dict):
        raise ConfigurationError(f"{path}: tool.anti-slop-python must be a table")
    unknown = options.keys() - _OPTIONS
    if unknown:
        raise ConfigurationError(
            f"{path}: unknown native options: {', '.join(sorted(unknown))}"
        )
    return ModuleSizeSettings(
        max_module_lines=_positive_integer(options, "max-module-lines", 500, path),
        max_test_module_lines=_positive_integer(
            options, "max-test-module-lines", 1500, path
        ),
        test_file_patterns=_test_patterns(options.get("test-file-patterns", []), path),
        root=path.parent,
    )


def _positive_integer(
    options: dict[str, object], name: str, default: int, path: Path
) -> int:
    value = options.get(name, default)
    if type(value) is not int or value <= 0:
        raise ConfigurationError(f"{path}: {name} must be a positive integer")
    return value


def _test_patterns(value: object, path: Path) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(pattern, str)
        or not pattern.strip()
        or pattern.startswith("/")
        or "\\" in pattern
        or ".." in pattern.split("/")
        for pattern in value
    ):
        raise ConfigurationError(
            f"{path}: test-file-patterns must be a list of non-empty"
            " relative patterns using /"
        )
    return tuple(value)
