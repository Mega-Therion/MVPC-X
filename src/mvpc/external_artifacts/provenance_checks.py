"""Shared provenance-shape checks used by both adapters."""

from __future__ import annotations

import re
from typing import Any

_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def is_valid_commit_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA_RE.match(value))


def extract_repo_commit_path(node: dict[str, Any] | None) -> tuple[Any, Any, Any]:
    node = node or {}
    repo = node.get("repo", node.get("repository"))
    commit = node.get("commit", node.get("commit_sha"))
    path = node.get("path")
    return repo, commit, path
