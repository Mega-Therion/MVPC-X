"""Nexus-specific intake and environment-parity gates.

The verifier may run standalone without ``MVPC_BIN``. When a consumer supplies
that variable, this module validates it as an explicit external dependency and
never treats a PATH lookup, symlink, writable executable, or unpinned digest as
trusted in strict mode.
"""

from __future__ import annotations

import hashlib
import os
import stat
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BinaryTrustReport:
    configured: bool
    allowed: bool
    path: str | None
    resolved_path: str | None
    sha256: str | None
    hash_pinned: bool
    ownership_safe: bool
    permissions_safe: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DependencyParityReport:
    repository_root: str
    files: dict[str, str | None]
    digest: str
    expected_digest: str | None
    matched: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _default_trusted_roots() -> tuple[Path, ...]:
    roots = [Path(sys.prefix) / "bin", Path("/usr/local/bin"), Path("/usr/bin")]
    raw = os.environ.get("MVPC_BIN_TRUSTED_ROOTS", "")
    for part in raw.split(os.pathsep):
        if part.strip():
            roots.append(Path(part.strip()))
    unique: list[Path] = []
    for root in roots:
        try:
            resolved = root.resolve(strict=True)
        except OSError:
            continue
        if resolved not in unique:
            unique.append(resolved)
    return tuple(unique)


def _is_under(path: Path, roots: Iterable[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def validate_mvpc_bin(
    value: str | None = None,
    *,
    strict: bool = False,
    expected_sha256: str | None = None,
    trusted_roots: Iterable[str | Path] | None = None,
) -> BinaryTrustReport:
    """Validate an explicitly configured external MVPC executable.

    ``strict`` requires a SHA-256 pin only when an external binary is actually
    configured. Standalone use remains valid and is reported as unconfigured.
    This is intentional: MVPC-X must not silently rely on a consumer-owned
    executable merely because the environment contains a PATH entry.
    """
    raw_value = value if value is not None else os.environ.get("MVPC_BIN")
    if not raw_value:
        return BinaryTrustReport(
            configured=False,
            allowed=True,
            path=None,
            resolved_path=None,
            sha256=None,
            hash_pinned=False,
            ownership_safe=True,
            permissions_safe=True,
            reasons=("MVPC_BIN is not configured; standalone local runtime selected.",),
        )

    reasons: list[str] = []
    candidate = Path(raw_value)
    if not candidate.is_absolute():
        return BinaryTrustReport(
            configured=True,
            allowed=False,
            path=raw_value,
            resolved_path=None,
            sha256=None,
            hash_pinned=False,
            ownership_safe=False,
            permissions_safe=False,
            reasons=(
                "MVPC_BIN must be an absolute path; PATH lookup is not a trusted binary identity.",
            ),
        )
    try:
        lstat = candidate.lstat()
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        return BinaryTrustReport(
            configured=True,
            allowed=False,
            path=raw_value,
            resolved_path=None,
            sha256=None,
            hash_pinned=False,
            ownership_safe=False,
            permissions_safe=False,
            reasons=(f"MVPC_BIN cannot be resolved: {exc}",),
        )

    if stat.S_ISLNK(lstat.st_mode):
        reasons.append("MVPC_BIN must not be a symlink.")
    if not resolved.is_file():
        reasons.append("MVPC_BIN must resolve to a regular file.")
    mode = resolved.stat().st_mode
    if not mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        reasons.append("MVPC_BIN is not executable.")
    permissions_safe = not bool(mode & (stat.S_IWGRP | stat.S_IWOTH))
    if not permissions_safe:
        reasons.append("MVPC_BIN is group- or world-writable.")
    owner_safe = True
    if hasattr(os, "getuid"):
        owner_safe = resolved.stat().st_uid in {0, os.getuid()}
        if not owner_safe:
            reasons.append("MVPC_BIN owner is neither root nor the current user.")

    roots = (
        tuple(Path(root).resolve() for root in trusted_roots)
        if trusted_roots
        else _default_trusted_roots()
    )
    if not _is_under(resolved, roots):
        reasons.append("MVPC_BIN escapes the approved protected namespace.")

    digest = _sha256_file(resolved) if resolved.is_file() else None
    pin = expected_sha256 or os.environ.get("MVPC_BIN_SHA256")
    hash_pinned = bool(pin and digest and pin.lower() == digest.lower())
    if pin and not hash_pinned:
        reasons.append("MVPC_BIN SHA-256 does not match the configured pin.")
    if strict and not pin:
        reasons.append("Strict external-binary mode requires MVPC_BIN_SHA256.")

    return BinaryTrustReport(
        configured=True,
        allowed=not reasons,
        path=raw_value,
        resolved_path=str(resolved),
        sha256=digest,
        hash_pinned=hash_pinned,
        ownership_safe=owner_safe,
        permissions_safe=permissions_safe,
        reasons=tuple(
            reasons
            or [
                "MVPC_BIN passes path, namespace, ownership, permission, and pin checks."
            ]
        ),
    )


def repository_root(start: str | Path | None = None) -> Path:
    """Locate a source checkout containing the declared Nexus lock manifests."""
    current = Path(start).resolve() if start else Path(__file__).resolve()
    candidates = (current, *current.parents)
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "DEPENDENCIES.md"
        ).is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate MVPC-X pyproject.toml and DEPENDENCIES.md"
    )


def dependency_parity(
    root: str | Path | None = None,
    *,
    expected_digest: str | None = None,
) -> DependencyParityReport:
    """Hash declared repository manifests and optionally enforce a pinned digest."""
    repo = repository_root(root)
    files: dict[str, str | None] = {}
    reasons: list[str] = []
    for filename in ("pyproject.toml", "DEPENDENCIES.md"):
        path = repo / filename
        files[filename] = _sha256_file(path) if path.is_file() else None
        if files[filename] is None:
            reasons.append(f"Required dependency manifest is missing: {filename}")
    material = (
        "\n".join(f"{name}:{files[name] or 'MISSING'}" for name in sorted(files)) + "\n"
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    configured = expected_digest or os.environ.get("MVPC_DEPENDENCY_LOCK_SHA256")
    matched = configured is None or configured.lower() == digest.lower()
    if configured and not matched:
        reasons.append(
            "Dependency-manifest digest does not match the configured lock pin."
        )
    if not configured:
        reasons.append(
            "No dependency-manifest digest pin configured; observed digest recorded only."
        )
    return DependencyParityReport(
        repository_root=str(repo),
        files=files,
        digest=digest,
        expected_digest=configured,
        matched=matched and not any(value is None for value in files.values()),
        reasons=tuple(reasons),
    )
