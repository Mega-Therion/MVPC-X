"""System self-fingerprinting: pre / mid / post audit snapshots."""

from __future__ import annotations

import hashlib
import os
import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Iterable

from mvpc.canonical import hash_canonical, sha256_hex


def _hash_path(path: Path, limit: int = 2_000_000) -> str | None:
    try:
        if not path.is_file():
            return None
        h = hashlib.sha256()
        with path.open("rb") as fh:
            remaining = limit
            while remaining > 0:
                chunk = fh.read(min(65536, remaining))
                if not chunk:
                    break
                h.update(chunk)
                remaining -= len(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _package_files_hash(package: str = "mvpc") -> str | None:
    try:
        dist = importlib_metadata.distribution(package)
    except importlib_metadata.PackageNotFoundError:
        root = Path(__file__).resolve().parents[1]
        if not root.is_dir():
            return None
        h = hashlib.sha256()
        for p in sorted(root.rglob("*.py")):
            try:
                h.update(p.read_bytes())
            except OSError:
                continue
        return h.hexdigest()
    h = hashlib.sha256()
    for file in sorted(dist.files or [], key=lambda f: str(f)):
        try:
            data = file.locate().read_bytes()
        except Exception:
            continue
        h.update(str(file).encode())
        h.update(data)
    return h.hexdigest()


@dataclass
class FingerprintSnapshot:
    phase: str
    created_at: str
    python_version: str
    platform: str
    mvpc_package_hash: str | None
    executable_hash: str | None
    env_selected: dict[str, str] = field(default_factory=dict)
    extra_paths: dict[str, str | None] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def digest(self) -> str:
        return hash_canonical(asdict(self))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["digest"] = self.digest()
        return d


class FingerprintSession:
    """Capture pre/mid/post fingerprints; divergence voids the run."""

    WATCH_ENV = ("MVPC_BIN", "LEAN_PATH", "PATH")

    def __init__(self, extra_binaries: Iterable[str | Path] | None = None) -> None:
        self.extra_binaries = [Path(p) for p in (extra_binaries or [])]
        self.pre: FingerprintSnapshot | None = None
        self.mid: FingerprintSnapshot | None = None
        self.post: FingerprintSnapshot | None = None
        self.voided: bool = False
        self.void_reason: str | None = None

    def _capture(self, phase: str) -> FingerprintSnapshot:
        env = {k: os.environ.get(k, "") for k in self.WATCH_ENV}
        extras = {str(p): _hash_path(p) for p in self.extra_binaries}
        return FingerprintSnapshot(
            phase=phase,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            mvpc_package_hash=_package_files_hash("mvpc"),
            executable_hash=_hash_path(Path(sys.executable)),
            env_selected=env,
            extra_paths=extras,
        )

    def capture_pre(self) -> FingerprintSnapshot:
        self.pre = self._capture("pre")
        return self.pre

    def capture_mid(self) -> FingerprintSnapshot:
        self.mid = self._capture("mid")
        self._check_divergence(self.pre, self.mid, "pre->mid")
        return self.mid

    def capture_post(self) -> FingerprintSnapshot:
        self.post = self._capture("post")
        self._check_divergence(self.pre, self.post, "pre->post")
        if self.mid is not None:
            self._check_divergence(self.mid, self.post, "mid->post")
        return self.post

    def _check_divergence(
        self,
        a: FingerprintSnapshot | None,
        b: FingerprintSnapshot | None,
        label: str,
    ) -> None:
        if a is None or b is None:
            return

        def core(s: FingerprintSnapshot) -> dict[str, Any]:
            return {
                "python_version": s.python_version,
                "mvpc_package_hash": s.mvpc_package_hash,
                "executable_hash": s.executable_hash,
                "env_selected": s.env_selected,
                "extra_paths": s.extra_paths,
            }

        if hash_canonical(core(a)) != hash_canonical(core(b)):
            self.voided = True
            self.void_reason = f"fingerprint divergence ({label})"

    def verify_twice(self) -> bool:
        self.capture_pre()
        self.capture_post()
        return not self.voided

    def report(self) -> dict[str, Any]:
        return {
            "voided": self.voided,
            "void_reason": self.void_reason,
            "pre": self.pre.to_dict() if self.pre else None,
            "mid": self.mid.to_dict() if self.mid else None,
            "post": self.post.to_dict() if self.post else None,
        }
