"""Prevent the wildcard-import shortcut observed in the paired agent trial."""

from pathlib import Path

import pytest

from anti_slop_python.ruff_integration import check_with_ruff


def test_wildcard_exports_are_rejected_even_with_all(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff.lint]\nselect = []\n")
    path = tmp_path / "facade.py"
    path.write_text('from math import *\n\n__all__ = ["pi"]\n')

    result = check_with_ruff([path], [path])

    assert [item.code for item in result.diagnostics] == ["F403"]
    assert "Import each required name explicitly" in str(result.diagnostics[0])
    assert "public re-exports" in str(result.diagnostics[0])
    assert result.notices == ()


def test_explicit_public_exports_pass(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
    path = tmp_path / "facade.py"
    path.write_text('from math import pi\n\n__all__ = ["pi"]\n')

    result = check_with_ruff([path], [path])

    assert result.diagnostics == ()
    assert result.notices == ()


def test_unused_import_guidance_preserves_public_exports(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[tool.ruff.lint]\nselect = ["F401"]\n')
    path = tmp_path / "facade.py"
    source = "from math import pi\n"
    path.write_text(source)

    result = check_with_ruff([path], [path])

    assert [item.code for item in result.diagnostics] == ["F401"]
    output = str(result.diagnostics[0])
    assert "__all__" in output
    assert (
        "Do not remove public exports or replace named imports with wildcard imports"
        in output
    )
    assert path.read_text() == source


@pytest.mark.parametrize(
    ("config", "comment", "notice"),
    [
        ('[tool.ruff.lint]\nignore = ["F403"]\n', "", "F403 is disabled"),
        (
            '[tool.ruff.lint.per-file-ignores]\n"facade.py" = ["F403"]\n',
            "",
            "F403 is ignored for facade.py",
        ),
        ("[tool.ruff]\n", "  # noqa: F403", "F403 is suppressed by noqa"),
    ],
)
def test_wildcard_overrides_remain_available(
    tmp_path: Path, config: str, comment: str, notice: str
) -> None:
    (tmp_path / "pyproject.toml").write_text(config)
    path = tmp_path / "facade.py"
    path.write_text(f'from math import *{comment}\n\n__all__ = ["pi"]\n')

    result = check_with_ruff([path], [path])

    assert result.diagnostics == ()
    assert any(item.startswith(notice) for item in result.notices)
