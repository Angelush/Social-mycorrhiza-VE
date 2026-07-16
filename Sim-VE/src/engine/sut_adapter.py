from __future__ import annotations

import abc
import dataclasses
import hashlib
import subprocess
from collections.abc import Sequence
from pathlib import Path


class SUTIntegrityError(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class SutPin:
    content_hash: str
    source_paths: tuple[str, ...]
    # Optional supplementary metadata only: the enclosing repository's HEAD (git
    # discovers it upward from repo_dir; None outside any repo). A commit id alone
    # would miss uncommitted edits (the harness's own negative-control tests run
    # against deliberately modified SUT copies), so content_hash is the real,
    # load-bearing pin.
    git_commit: str | None


def compute_pin(source_paths: Sequence[str | Path], repo_dir: str | Path | None = None) -> SutPin:
    original_paths = tuple(str(p) for p in source_paths)
    hasher = hashlib.sha256()
    for path in sorted(original_paths):
        with open(path, "rb") as f:
            file_bytes = f.read()
        hasher.update(path.encode("utf-8") + b"\x00" + file_bytes + b"\x00")

    git_commit: str | None = None
    if repo_dir is not None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                git_commit = result.stdout.strip()
        except Exception:
            git_commit = None

    return SutPin(
        content_hash=hasher.hexdigest(),
        source_paths=original_paths,
        git_commit=git_commit,
    )


class SUTAdapter(abc.ABC):
    def __init__(self, source_paths: Sequence[str | Path], repo_dir: str | Path | None = None) -> None:
        self.source_paths = tuple(str(p) for p in source_paths)
        self.repo_dir = str(repo_dir) if repo_dir is not None else None
        self._pin = compute_pin(self.source_paths, self.repo_dir)

    @property
    def pin(self) -> SutPin:
        return self._pin

    def assert_pinned(self) -> None:
        current = compute_pin(self.source_paths, self.repo_dir)
        if current.content_hash != self._pin.content_hash:
            raise SUTIntegrityError(
                f"SUT source changed since the campaign-start pin for "
                f"{self.source_paths}; the campaign must abort."
            )
