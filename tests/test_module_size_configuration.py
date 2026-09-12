from pathlib import Path

import pytest

from anti_slop_python.checker import check_file, check_source
from anti_slop_python.cli import main
from anti_slop_python.configuration import ConfigurationError, ModuleSizeSettings


@pytest.mark.parametrize("name", ["test_report.py", "report_test.py", "conftest.py"])
@pytest.mark.parametrize("lines", [501, 1500, 1501])
def test_default_test_budget(name: str, lines: int) -> None:
    diagnostics = check_source("value = 1\n" * lines, Path("package") / name)

    if lines <= 1500:
        assert diagnostics == []
        return
    assert len(diagnostics) == 1
    assert diagnostics[0].message == "Too many lines in test module (1501 > 1500)"
    assert str(diagnostics[0]).splitlines()[1:] == [
        "  Group tests by the behavior or component they verify.",
        "  Keep each scenario readable and preserve assertions and edge cases.",
        "  Do not remove coverage, compress cases, or hide setup in shared fixtures",
        "  merely to satisfy this limit.",
    ]


@pytest.mark.parametrize(
    "name", ["service.py", "test.py", "contest.py", "tests/helpers.py"]
)
def test_other_names_keep_production_budget(name: str) -> None:
    diagnostics = check_source("import pytest\n" + "# line\n" * 500, name)

    assert [item.message for item in diagnostics] == [
        "Too many lines in module (501 > 500)"
    ]


def test_programmatic_settings_do_not_require_files(tmp_path: Path) -> None:
    settings = ModuleSizeSettings(
        max_module_lines=2,
        max_test_module_lines=4,
        test_file_patterns=("specs/*",),
        root=tmp_path,
    )
    source = "value = 1\n" * 3

    assert check_source(source, tmp_path / "specs/helper.py", settings=settings) == []
    assert check_source(source, "test_example.py", settings=settings) == []
    assert check_source(source, "service.py", settings=settings)[0].message == (
        "Too many lines in module (3 > 2)"
    )


def test_nearest_table_applies_independent_of_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        "[tool.anti-slop-python]\nmax-module-lines = 2\nmax-test-module-lines = 4\n"
        'test-file-patterns = ["specs/*"]\n'
    )
    nested = project / "specs" / "nested"
    nested.mkdir(parents=True)
    (nested / "pyproject.toml").write_text("[tool.ruff]\n")
    path = nested / "helpers.py"
    path.write_text("value = 1\n" * 4)
    monkeypatch.chdir(tmp_path)

    assert check_file(path) == []
    # A closer native table replaces the parent table; missing keys use defaults.
    (nested / "pyproject.toml").write_text(
        "[tool.anti-slop-python]\nmax-module-lines = 3\n"
    )
    assert check_file(path)[0].message == "Too many lines in module (4 > 3)"


def test_custom_patterns_do_not_match_outside_settings_root(tmp_path: Path) -> None:
    settings = ModuleSizeSettings(test_file_patterns=("*",), root=tmp_path / "project")
    source = "value = 1\n" * 501

    assert check_source(source, tmp_path / "project/helper.py", settings=settings) == []
    assert check_source(source, tmp_path / "elsewhere/helper.py", settings=settings)


@pytest.mark.parametrize(
    ("option", "value", "error"),
    [
        ("max-module-lines", "0", "must be a positive integer"),
        ("max-module-lines", "-1", "must be a positive integer"),
        ("max-test-module-lines", "true", "must be a positive integer"),
        ("max-test-module-lines", '"1500"', "must be a positive integer"),
        ("max-module-lines", "500.0", "must be a positive integer"),
        ("max-lines", "500", "unknown native options"),
        ("test-file-patterns", '"tests/*"', "must be a list"),
        ("test-file-patterns", "[1]", "must be a list"),
        ("test-file-patterns", '[""]', "must be a list"),
        ("test-file-patterns", '["/tests/*"]', "relative patterns"),
        ("test-file-patterns", '["../tests/*"]', "relative patterns"),
        ("test-file-patterns", "['tests\\*']", "relative patterns"),
    ],
)
def test_rejects_invalid_options(
    tmp_path: Path, option: str, value: str, error: str
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        f"[tool.anti-slop-python]\n{option} = {value}\n"
    )
    path = tmp_path / "example.py"
    path.write_text("value = 1\n")

    with pytest.raises(ConfigurationError, match=error):
        check_file(path)


@pytest.mark.parametrize(
    "config",
    [b"[tool.anti-slop-python\n", b"\xff", b'[tool]\nanti-slop-python = "invalid"\n'],
)
def test_invalid_configuration_has_clear_cli_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], config: bytes
) -> None:
    (tmp_path / "pyproject.toml").write_bytes(config)
    path = tmp_path / "example.py"
    path.write_text("value = 1\n")

    assert main([str(path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "anti-slop-python:" in captured.err
    assert "pyproject.toml" in captured.err
    assert "Traceback" not in captured.err


def test_cli_reloads_settings_between_runs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config = tmp_path / "pyproject.toml"
    config.write_text("[tool.anti-slop-python]\nmax-test-module-lines = 2\n")
    path = tmp_path / "test_report.py"
    path.write_text("value = 1\n" * 3)

    assert main([str(path)]) == 1
    assert "Too many lines in test module (3 > 2)" in capsys.readouterr().out
    config.write_text("[tool.anti-slop-python]\nmax-test-module-lines = 3\n")
    assert main([str(tmp_path)]) == 0
    assert capsys.readouterr().out == ""


def test_cli_uses_each_files_settings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    accepted = tmp_path / "accepted"
    accepted.mkdir()
    (accepted / "pyproject.toml").write_text(
        "[tool.anti-slop-python]\nmax-module-lines = 3\n"
    )
    (accepted / "service.py").write_text("value = 1\n" * 3)
    rejected = tmp_path / "rejected"
    rejected.mkdir()
    (rejected / "pyproject.toml").write_text(
        "[tool.anti-slop-python]\nmax-module-lines = 2\n"
    )
    path = rejected / "service.py"
    path.write_text("value = 1\n" * 3)

    assert main([str(tmp_path)]) == 1
    output = capsys.readouterr().out
    assert str(path) in output
    assert str(accepted / "service.py") not in output


def test_test_budget_does_not_disable_other_native_rules(tmp_path: Path) -> None:
    diagnostics = check_source('getattr(value, "name")\n', tmp_path / "test_report.py")
    assert [item.code for item in diagnostics] == ["SPY002"]
