"""Save a completed candidate once, before giving its agent any review feedback."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path


def archive(workspace: Path, destination: Path) -> None:
    manifest = json.loads((workspace / "manifest.json").read_text())
    changed = [
        name
        for name, digest in manifest["immutable_sha256"].items()
        if not (workspace / name).is_file()
        or hashlib.sha256((workspace / name).read_bytes()).hexdigest() != digest
    ]
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copytree(
        workspace / "candidate",
        destination / "candidate",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".ruff_cache"),
    )
    for name in ["prompt.txt", "manifest.json", "pyproject.toml", "lint.jsonl"]:
        if (workspace / name).is_file():
            shutil.copyfile(workspace / name, destination / name)
    capture = {
        "captured_at": datetime.now(UTC).isoformat(),
        "changed_immutable_files": changed,
        "candidate_sha256": {
            str(path.relative_to(destination / "candidate")): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted((destination / "candidate").rglob("*"))
            if path.is_file()
        },
    }
    (destination / "capture.json").write_text(
        json.dumps(capture, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(capture, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    archive(args.workspace.resolve(), args.destination.resolve())


if __name__ == "__main__":
    main()
