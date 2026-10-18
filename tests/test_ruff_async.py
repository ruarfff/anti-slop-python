from __future__ import annotations

from pathlib import Path

import pytest

from anti_slop_python.ruff_integration import check_with_ruff


@pytest.fixture(autouse=True)
def minimal_project_rules(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[tool.ruff.lint]\nselect = ["F"]\n')


@pytest.mark.parametrize(
    ("code", "imports", "body", "alternative"),
    [
        (
            "ASYNC210",
            "import requests",
            'requests.get("https://example.com")',
            "asyncio.to_thread",
        ),
        (
            "ASYNC210",
            "from requests import get as fetch",
            'fetch("https://example.com")',
            "asyncio.to_thread",
        ),
        (
            "ASYNC212",
            "import httpx",
            'client = httpx.Client()\n    client.get("https://example.com")',
            "asyncio.to_thread",
        ),
        (
            "ASYNC220",
            "import subprocess",
            'subprocess.Popen(["python", "--version"])',
            "asyncio.create_subprocess_exec",
        ),
        (
            "ASYNC221",
            "import subprocess",
            'subprocess.run(["python", "--version"], check=True)',
            "asyncio.create_subprocess_exec",
        ),
        (
            "ASYNC222",
            "import os",
            "os.waitpid(1, 0)",
            "asyncio.to_thread",
        ),
        (
            "ASYNC230",
            "",
            'with open("data.txt") as stream:\n        stream.read()',
            "asyncio.to_thread",
        ),
        (
            "ASYNC240",
            "from pathlib import Path",
            'path = Path("data.txt")\n    path.read_text()',
            "asyncio.to_thread",
        ),
        (
            "ASYNC250",
            "",
            'input("Name: ")',
            "asyncio.to_thread",
        ),
        (
            "ASYNC251",
            "from time import sleep as pause",
            "pause(1)",
            "asyncio.sleep",
        ),
    ],
)
def test_reports_blocking_calls_with_actionable_guidance(
    tmp_path: Path,
    code: str,
    imports: str,
    body: str,
    alternative: str,
) -> None:
    source = tmp_path / "example.py"
    content = f"{imports}\n\nasync def handle_request() -> None:\n    {body}\n"
    source.write_text(content)

    result = check_with_ruff([tmp_path], [source])

    assert [diagnostic.code for diagnostic in result.diagnostics] == [code]
    diagnostic = result.diagnostics[0]
    assert diagnostic.path == source
    assert "event-loop thread" in str(diagnostic)
    assert "active async framework" in str(diagnostic)
    assert "examples below are for asyncio" in str(diagnostic)
    assert alternative in str(diagnostic)
    assert result.notices == ()
    assert source.read_text() == content


def test_reports_blocking_in_a_scheduled_background_coroutine(tmp_path: Path) -> None:
    source = tmp_path / "consumer.py"
    source.write_text(
        "import asyncio\n"
        "import time\n\n"
        "async def consume_messages() -> None:\n"
        "    time.sleep(1)\n\n"
        "async def start() -> None:\n"
        "    task = asyncio.create_task(consume_messages())\n"
        "    await task\n"
    )

    result = check_with_ruff([tmp_path], [source])

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["ASYNC251"]
    assert result.diagnostics[0].line == 5
    assert "create_task" in str(result.diagnostics[0])


def test_sleep_guidance_preserves_other_async_frameworks(tmp_path: Path) -> None:
    source = tmp_path / "worker.py"
    source.write_text(
        "import time\n"
        "import trio\n\n"
        "async def worker() -> None:\n"
        "    time.sleep(1)\n\n"
        "trio.run(worker)\n"
    )

    result = check_with_ruff([tmp_path], [source])

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["ASYNC251"]
    guidance = str(result.diagnostics[0])
    assert "active async framework" in guidance
    assert "examples below are for asyncio" in guidance
    assert "await asyncio.sleep(delay)" in guidance


@pytest.mark.parametrize(
    "content",
    [
        "import asyncio\n\nasync def wait() -> None:\n    await asyncio.sleep(1)\n",
        "import httpx\n\n"
        "async def fetch() -> None:\n"
        "    async with httpx.AsyncClient() as client:\n"
        '        await client.get("https://example.com")\n',
        "import asyncio\n"
        "from pathlib import Path\n\n"
        "async def read() -> str:\n"
        '    return await asyncio.to_thread(Path("data.txt").read_text)\n',
        "import asyncio\n\n"
        "async def run() -> None:\n"
        '    process = await asyncio.create_subprocess_exec("python", "--version")\n'
        "    await process.wait()\n",
        "import time\n"
        "from fastapi import FastAPI\n\n"
        "app = FastAPI()\n\n"
        '@app.get("/")\n'
        "def endpoint() -> str:\n"
        "    time.sleep(1)\n"
        '    return "ready"\n',
    ],
)
def test_accepts_async_apis_offloaded_io_and_synchronous_endpoints(
    tmp_path: Path, content: str
) -> None:
    source = tmp_path / "example.py"
    source.write_text(content)

    result = check_with_ruff([tmp_path], [source])

    assert result.diagnostics == ()
    assert result.notices == ()


@pytest.mark.parametrize(
    ("selector", "expected_codes"),
    [("ASYNC251", ["ASYNC210"]), ("ASYNC2", [])],
)
def test_respects_individual_and_prefix_ignores_with_notices(
    tmp_path: Path, selector: str, expected_codes: list[str]
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        f'[tool.ruff.lint]\nselect = ["F"]\nignore = ["{selector}"]\n'
    )
    source = tmp_path / "example.py"
    source.write_text(
        "import requests\n"
        "import time\n\n"
        "async def fetch() -> None:\n"
        "    time.sleep(1)\n"
        '    requests.get("https://example.com")\n'
    )

    result = check_with_ruff([tmp_path], [source])

    assert [diagnostic.code for diagnostic in result.diagnostics] == expected_codes
    assert "ASYNC251 is disabled; recommended: enabled" in result.notices
    if selector == "ASYNC2":
        assert "ASYNC210 is disabled; recommended: enabled" in result.notices


def test_respects_per_file_ignore_with_a_notice(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ruff.lint]\nselect = ["F"]\n\n'
        '[tool.ruff.lint.per-file-ignores]\n"example.py" = ["ASYNC251"]\n'
    )
    source = tmp_path / "example.py"
    source.write_text("import time\n\nasync def wait() -> None:\n    time.sleep(1)\n")

    result = check_with_ruff([tmp_path], [source])

    assert result.diagnostics == ()
    assert result.notices == (
        "ASYNC251 is ignored for example.py; recommended for all checked files",
    )


@pytest.mark.parametrize("comment", ["# noqa: ASYNC251", "# noqa"])
def test_respects_noqa_with_a_notice(tmp_path: Path, comment: str) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        f"import time\n\nasync def wait() -> None:\n    time.sleep(1)  {comment}\n"
    )

    result = check_with_ruff([tmp_path], [source])

    assert result.diagnostics == ()
    assert result.notices == (
        f"ASYNC251 is suppressed by noqa at {source}:4; recommended for checked files",
    )


def test_does_not_enable_unrelated_async_rules(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "async def calculate(timeout: float) -> float:\n    return timeout\n"
    )

    result = check_with_ruff([tmp_path], [source])

    assert result.diagnostics == ()
    assert result.notices == ()


def test_documents_static_analysis_limits(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        "import time\n"
        "from confluent_kafka import Consumer\n\n"
        "def blocking_helper() -> None:\n"
        "    time.sleep(1)\n\n"
        "async def consume() -> int:\n"
        "    blocking_helper()\n"
        "    consumer = Consumer({})\n"
        "    consumer.poll(1.0)\n"
        "    return sum(range(100_000_000))\n"
    )

    result = check_with_ruff([tmp_path], [source])

    assert result.diagnostics == ()
    assert result.notices == ()
