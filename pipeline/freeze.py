from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

from pipeline.contracts import ContractError
from pipeline.io import atomic_write_json, sha256_file


def _git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args], cwd=root, check=True, text=True, capture_output=True
    )
    return process.stdout.strip()


def build_freeze_manifest(
    root: Path, bundle: Path, *, run_id: str, require_clean: bool
) -> dict[str, Any]:
    commit = _git(root, "rev-parse", "HEAD")
    dirty = bool(_git(root, "status", "--porcelain"))
    if require_clean and dirty:
        raise ContractError("Freeze requires a clean Git worktree")
    files = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in sorted(bundle.rglob("*.json"))
    ]
    lock = root / "requirements.lock"
    return {
        "freeze_version": "freeze-v1",
        "run_id": run_id,
        "repo_commit": commit,
        "dirty": dirty,
        "dependency_lock_sha256": sha256_file(lock) if lock.exists() else None,
        "files": files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a tamper-evident run freeze manifest")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--check-clean", action="store_true")
    args = parser.parse_args()
    manifest = build_freeze_manifest(
        args.repo.resolve(), args.bundle.resolve(), run_id=args.run_id, require_clean=args.check_clean
    )
    atomic_write_json(args.output, manifest)
    print(f"Freeze manifest written to {args.output}")


if __name__ == "__main__":
    main()
