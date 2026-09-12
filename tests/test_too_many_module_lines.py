from __future__ import annotations

from pathlib import Path

import pytest

from anti_slop_python import check_source
from anti_slop_python.checker import check_file


@pytest.mark.parametrize("lines", [0, 1, 499, 500, 501, 1000])
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("final_newline", [False, True])
def test_module_line_limit(lines: int, newline: str, final_newline: bool) -> None:
    source = newline.join(["value = 1"] * lines)
    if lines and final_newline:
        source += newline

    diagnostics = check_source(source, "example.py")

    if lines <= 500:
        assert diagnostics == []
        return
    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert diagnostic.path == Path("example.py")
    assert (diagnostic.line, diagnostic.column, diagnostic.code) == (1, 1, "SPY003")
    assert diagnostic.message.splitlines()[0] == (
        f"Too many lines in module ({lines} > 500)"
    )


@pytest.mark.parametrize(
    "source",
    [
        "# comment\n" * 501,
        "\n" * 501,
        '"""\n' + "documentation\n" * 499 + '"""\n',
        "values = [\n" + "    1,\n" * 499 + "]\n",
    ],
)
def test_counts_all_physical_lines(source: str) -> None:
    diagnostics = check_source(source)

    assert [item.code for item in diagnostics] == ["SPY003"]
    assert diagnostics[0].message.splitlines()[0] == (
        "Too many lines in module (501 > 500)"
    )


@pytest.mark.parametrize("separator", ["\f", "\v", "\x85", "\u2028", "\u2029"])
def test_does_not_count_other_separators_as_lines(separator: str) -> None:
    assert check_source(f"# first{separator}second\n" * 500) == []


def test_reports_size_and_other_rules_in_source_order() -> None:
    diagnostics = check_source("\n" * 500 + 'getattr(value, "name")\n')

    assert [(item.code, item.line) for item in diagnostics] == [
        ("SPY003", 1),
        ("SPY002", 501),
    ]


def test_invalid_large_module_reports_syntax_error() -> None:
    diagnostics = check_source("\n" * 500 + "def broken(:\n")

    assert [item.code for item in diagnostics] == ["SyntaxError"]


def test_reads_encoded_file_with_windows_line_endings(tmp_path: Path) -> None:
    path = tmp_path / "example.py"
    path.write_bytes(b"# coding: latin-1\r\n" + b"# caf\xe9\r\n" * 500)

    diagnostics = check_file(path)

    assert [item.code for item in diagnostics] == ["SPY003"]
    assert diagnostics[0].message.splitlines()[0] == (
        "Too many lines in module (501 > 500)"
    )
