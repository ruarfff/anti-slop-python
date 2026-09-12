from pathlib import Path

import pytest

from anti_slop_python.ruff_integration import check_with_ruff


@pytest.mark.parametrize(
    ("source", "code"),
    [
        ("def identity(value) -> int:\n    return value\n", "ANN001"),
        ("def count(*values) -> int:\n    return len(values)\n", "ANN002"),
        ("def count(**values) -> int:\n    return len(values)\n", "ANN003"),
        ("def identity(value: int):\n    return value\n", "ANN201"),
        ("def _identity(value: int):\n    return value\n", "ANN202"),
        ("class Item:\n    def __init__(self):\n        self.value = 1\n", "ANN204"),
        (
            "class Item:\n    @staticmethod\n"
            "    def identity(value: int):\n        return value\n",
            "ANN205",
        ),
        (
            "class Item:\n    @classmethod\n"
            "    def create(cls):\n        return cls()\n",
            "ANN206",
        ),
        (
            "from typing import Any\n\n\n"
            "def identity(value: Any) -> str:\n    return str(value)\n",
            "ANN401",
        ),
    ],
)
def test_enforces_annotations_and_explains_the_fix(
    tmp_path: Path, source: str, code: str
) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
    path = tmp_path / "example.py"
    path.write_text(source)

    result = check_with_ruff([path], [path])

    assert [diagnostic.code for diagnostic in result.diagnostics] == [code]
    assert result.notices == ()
    assert "Declare the actual parameter and return types." in str(
        result.diagnostics[0]
    )
    assert "Preserve existing type information" in str(result.diagnostics[0])


def test_allows_local_inference(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n")
    path = tmp_path / "example.py"
    path.write_text(
        "def double(value: int) -> int:\n    result = value * 2\n    return result\n"
    )

    result = check_with_ruff([path], [path])

    assert result.diagnostics == ()
    assert result.notices == ()


@pytest.mark.parametrize(
    ("config", "comment", "notice"),
    [
        ('[tool.ruff.lint]\nignore = ["ANN201"]\n', "", "ANN201 is disabled"),
        (
            '[tool.ruff.lint.per-file-ignores]\n"example.py" = ["ANN201"]\n',
            "",
            "ANN201 is ignored for example.py",
        ),
        ("[tool.ruff]\n", "  # noqa: ANN201", "ANN201 is suppressed by noqa"),
    ],
)
def test_respects_annotation_overrides_with_notice(
    tmp_path: Path, config: str, comment: str, notice: str
) -> None:
    (tmp_path / "pyproject.toml").write_text(config)
    path = tmp_path / "example.py"
    path.write_text(f"def identity(value: int):{comment}\n    return value\n")

    result = check_with_ruff([path], [path])

    assert result.diagnostics == ()
    assert any(item.startswith(notice) for item in result.notices)
