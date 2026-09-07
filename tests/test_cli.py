from __future__ import annotations

from pathlib import Path

import pytest

from anti_slop_python.cli import main


@pytest.fixture(autouse=True)
def recommended_ruff_config(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """[tool.ruff]
exclude = ["examples"]

[tool.ruff.lint]
select = ["BLE001", "C901", "E722", "PLR0915", "TID251"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-statements = 40

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"mock.patch".msg = "Pass the dependency explicitly"
"unittest.mock.patch".msg = "Pass the dependency explicitly"
"""
    )


def test_returns_one_and_prints_conventional_diagnostic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "example.py"
    source.write_text('getattr(value, "name")\n')

    exit_code = main([str(source)])

    assert exit_code == 1
    assert capsys.readouterr().out == (
        f"{source}:1:1 SPY002 Avoid dynamic attribute access\n"
        "  Use direct attribute access for a known interface.\n"
        "  For runtime choices, use an explicit mapping of supported operations.\n"
        "  Preserve missing-value behavior explicitly.\n"
        "  Do not replace this call with __dict__, vars(), or a reflection wrapper.\n"
    )


def test_returns_zero_when_no_violations(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "example.py"
    source.write_text("value.name\n")

    assert main([str(source)]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("lines", [500, 501])
def test_module_size_controls_exit_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], lines: int
) -> None:
    source = tmp_path / "example.py"
    source.write_text("value = 1\n" * lines)

    exit_code = main([str(source)])

    assert exit_code == (1 if lines > 500 else 0)
    expected = (
        f"{source}:1:1 SPY003 Too many lines in module (501 > 500)\n"
        "  Separate distinct responsibilities into cohesive modules"
        " with clear interfaces.\n"
        "  Keep closely related code together and preserve public APIs and behavior.\n"
        "  Preserve validation order, side effects, and type information"
        " when moving code.\n"
        "  Verify package and standalone imports where supported,"
        " plus each entry point.\n"
        "  Check that every supported import mode exposes the full public API.\n"
        "  Do not compress code, remove useful comments,"
        " split at arbitrary line counts,\n"
        "  or move unrelated code into a generic helpers module"
        " to satisfy this limit.\n"
        if lines > 500
        else ""
    )
    assert capsys.readouterr().out == expected


def test_discovers_files_recursively_and_ignores_environments(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    checked = package / "checked.py"
    checked.write_text('setattr(value, "name", 1)\n')
    ignored_directory = tmp_path / ".venv"
    ignored_directory.mkdir()
    ignored = ignored_directory / "ignored.py"
    ignored.write_text('getattr(value, "name")\n')
    examples_directory = tmp_path / "examples"
    examples_directory.mkdir()
    example = examples_directory / "example.py"
    example.write_text('getattr(value, "name")\n')

    exit_code = main([str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert str(checked) in output
    assert str(example) in output
    assert str(ignored) not in output


def test_checks_excluded_directory_when_passed_explicitly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    examples_directory = tmp_path / "examples"
    examples_directory.mkdir()
    example = examples_directory / "violations.py"
    example.write_text('getattr(value, "name")\n')

    exit_code = main([str(examples_directory)])

    assert exit_code == 1
    assert str(example) in capsys.readouterr().out


def test_syntax_error_returns_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "broken.py"
    source.write_text("def broken(:\n")

    exit_code = main([str(source)])

    assert exit_code == 1
    assert "SyntaxError invalid syntax" in capsys.readouterr().out


def test_policy_notice_does_not_change_exit_code(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """[tool.ruff.lint]
extend-ignore = ["C901"]
"""
    )
    source = tmp_path / "example.py"
    source.write_text("value = 1\n")

    exit_code = main([str(source)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert "anti-slop-python policy notice: C901 is disabled" in captured.err
