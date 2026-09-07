"""Project-relative Ruff settings must not depend on the caller's directory."""

from pathlib import Path

import pytest

from anti_slop_python.ruff_integration import check_with_ruff


@pytest.mark.parametrize("caller", ["project", "parent", "nested"])
def test_resolves_source_roots_relative_to_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caller: str
) -> None:
    project = tmp_path / "project"
    library = project / "lib"
    library.mkdir(parents=True)
    (library / "local_api.py").write_text("VALUE = 1\n")
    (project / "pyproject.toml").write_text(
        '[tool.ruff]\nsrc = ["lib"]\n[tool.ruff.lint]\nselect = ["I"]\n'
    )
    path = project / "entry.py"
    path.write_text(
        "import external_api\n\nimport local_api\n\n"
        '__all__ = ["external_api", "local_api"]\n'
    )
    directories = {"project": project, "parent": tmp_path, "nested": library}
    monkeypatch.chdir(directories[caller])
    target = Path("../entry.py") if caller == "nested" else path.relative_to(Path.cwd())

    result = check_with_ruff([target], [target])

    assert result.diagnostics == ()
    assert result.notices == ()


def test_resolves_path_exclusions_in_each_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = []
    for name in ["one", "two"]:
        project = tmp_path / name
        (project / "generated").mkdir(parents=True)
        (project / "pyproject.toml").write_text(
            '[tool.ruff]\nexclude = ["generated/*.py"]\n'
        )
        path = project / "generated/client.py"
        path.write_text("def missing_annotations(value):\n    return value\n")
        files.append(path.relative_to(tmp_path))
    monkeypatch.chdir(tmp_path)

    result = check_with_ruff(files, files)

    assert result.diagnostics == ()
