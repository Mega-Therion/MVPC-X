"""Security & integrity for MVPC-X.

Two layers of protection:

1. **System self-integrity** (primary — the "checksum" you meant):
   Fingerprint the installed `mvpc` package *before* any artifact is read.
   Re-verify mid-run (optional) and after processing. If a slick payload
   somehow mutated verifier code on disk, the seal breaks.

2. **Artifact integrity** (secondary):
   Hash the input bytes before and after the audit. If the file changes
   during the run, report ARTIFACT_MUTATION.

Also: intake guards (size, symlink policy, path resolution).
"""
from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Default max artifact size (50 MiB) — large enough for theories, small enough
# to blunt zip/bomb-style disk abuse when someone points us at nonsense.
DEFAULT_MAX_ARTIFACT_BYTES = 50 * 1024 * 1024

# Extensions we refuse to treat as primary audit targets (executables / archives
# that invite unpack-and-pwn patterns). Users can still hash via generic if we
# later add an override; by default we reject.
BLOCKED_EXTENSIONS = frozenset({
    ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a",
    ".bat", ".cmd", ".ps1", ".com", ".msi",
    ".scr", ".apk", ".dmg", ".iso",
})


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def package_root() -> Path:
    """Return the filesystem root of the installed `mvpc` package."""
    import mvpc

    return Path(mvpc.__file__).resolve().parent


def iter_system_files(root: Optional[Path] = None) -> List[Path]:
    """All .py files that constitute the verifier (sorted for stability)."""
    root = root or package_root()
    files = [p for p in root.rglob("*.py") if p.is_file() and "__pycache__" not in p.parts]
    return sorted(files, key=lambda p: str(p).replace("\\", "/"))


def compute_system_fingerprint(root: Optional[Path] = None) -> Dict[str, Any]:
    """Deterministic fingerprint of the MVPC-X installation.

    Hashes each package .py file and a merkle-style root over (relpath, file_hash).
    """
    root = (root or package_root()).resolve()
    entries: List[Dict[str, str]] = []
    for path in iter_system_files(root):
        rel = str(path.relative_to(root)).replace("\\", "/")
        entries.append({"path": rel, "sha256": hash_file(path)})
    # Root seal: hash of canonical "path:hash\n" lines
    lines = [f"{e['path']}:{e['sha256']}" for e in entries]
    root_hash = hash_bytes(("\n".join(lines) + ("\n" if lines else "")).encode("utf-8"))
    return {
        "algorithm": "sha256",
        "package_root": str(root),
        "file_count": len(entries),
        "files": entries,
        "system_fingerprint": root_hash,
        "timestamp": _utc(),
    }


@dataclass
class IntakeDecision:
    allowed: bool
    path: str
    reasons: List[str] = field(default_factory=list)
    resolved_path: Optional[str] = None
    size_bytes: Optional[int] = None
    is_symlink: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def validate_intake(
    path: str,
    *,
    max_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
    allow_symlinks: bool = False,
    allowed_root: Optional[str] = None,
) -> IntakeDecision:
    """Pre-ingest guards for untrusted paths."""
    reasons: List[str] = []
    p = Path(path)
    if not p.exists():
        return IntakeDecision(False, path, ["Path does not exist"])

    is_link = p.is_symlink()
    if is_link and not allow_symlinks:
        return IntakeDecision(
            False, path, ["Symlinks rejected (pass allow_symlinks=True to override)"], is_symlink=True
        )

    try:
        resolved = p.resolve(strict=True)
    except OSError as e:
        return IntakeDecision(False, path, [f"Cannot resolve path: {e}"], is_symlink=is_link)

    if allowed_root:
        root = Path(allowed_root).resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            return IntakeDecision(
                False,
                path,
                [f"Path escapes allowed_root: {root}"],
                resolved_path=str(resolved),
                is_symlink=is_link,
            )

    if resolved.is_dir():
        # Directory audits are allowed; per-file checks happen later.
        return IntakeDecision(
            True, path, ["Directory intake OK"], resolved_path=str(resolved), is_symlink=is_link
        )

    if not resolved.is_file():
        return IntakeDecision(
            False, path, ["Not a regular file"], resolved_path=str(resolved), is_symlink=is_link
        )

    ext = resolved.suffix.lower()
    if ext in BLOCKED_EXTENSIONS:
        reasons.append(f"Blocked extension for audit intake: {ext}")

    try:
        st = resolved.stat()
    except OSError as e:
        return IntakeDecision(False, path, [f"stat failed: {e}"], str(resolved), is_link)

    # World-writable weirdness is a smell on multi-user hosts
    if st.st_mode & stat.S_IWOTH:
        reasons.append("File is world-writable (suspicious on shared hosts)")

    size = int(st.st_size)
    if size > max_bytes:
        return IntakeDecision(
            False,
            path,
            [f"File exceeds max size ({size} > {max_bytes} bytes)"],
            str(resolved),
            size,
            is_link,
        )

    # Executable bit on a "document" is a smell — warn but allow text-like
    if st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        if ext not in {".py", ".sh", ""}:
            reasons.append("Executable bit set on non-script artifact")

    allowed = not any(r.startswith("Blocked extension") for r in reasons)
    if not allowed:
        return IntakeDecision(False, path, reasons, str(resolved), size, is_link)
    if reasons:
        # soft warnings — still allowed
        return IntakeDecision(True, path, reasons, str(resolved), size, is_link)
    return IntakeDecision(True, path, ["Intake OK"], str(resolved), size, is_link)


@dataclass
class IntegritySession:
    """Captures system (+ optional artifact) seals across an audit lifetime."""

    system_before: Dict[str, Any]
    artifact_path: Optional[str] = None
    artifact_hash_before: Optional[str] = None
    system_mid: Optional[Dict[str, Any]] = None
    system_after: Optional[Dict[str, Any]] = None
    artifact_hash_after: Optional[str] = None
    system_ok_mid: Optional[bool] = None
    system_ok_after: Optional[bool] = None
    artifact_ok: Optional[bool] = None
    events: List[str] = field(default_factory=list)

    @classmethod
    def begin(cls, artifact_path: Optional[str] = None) -> "IntegritySession":
        before = compute_system_fingerprint()
        art_hash = None
        if artifact_path and os.path.isfile(artifact_path):
            art_hash = hash_file(artifact_path)
        sess = cls(
            system_before=before,
            artifact_path=os.path.abspath(artifact_path) if artifact_path else None,
            artifact_hash_before=art_hash,
        )
        sess.events.append(
            f"system seal captured @ {before['timestamp']} fp={before['system_fingerprint'][:16]}…"
        )
        if art_hash:
            sess.events.append(f"artifact pre-hash={art_hash[:16]}…")
        return sess

    def check_mid(self) -> bool:
        mid = compute_system_fingerprint()
        self.system_mid = mid
        ok = mid["system_fingerprint"] == self.system_before["system_fingerprint"]
        self.system_ok_mid = ok
        self.events.append(
            f"mid-run system check {'OK' if ok else 'FAILED'} @ {mid['timestamp']}"
        )
        return ok

    def finalize(self) -> bool:
        after = compute_system_fingerprint()
        self.system_after = after
        self.system_ok_after = (
            after["system_fingerprint"] == self.system_before["system_fingerprint"]
        )
        self.events.append(
            f"post-run system check {'OK' if self.system_ok_after else 'FAILED'} "
            f"@ {after['timestamp']}"
        )
        if self.artifact_path and os.path.isfile(self.artifact_path):
            self.artifact_hash_after = hash_file(self.artifact_path)
            self.artifact_ok = self.artifact_hash_after == self.artifact_hash_before
            self.events.append(
                f"artifact post-hash check {'OK' if self.artifact_ok else 'FAILED'}"
            )
        elif self.artifact_hash_before:
            self.artifact_ok = False
            self.events.append("artifact missing after run")
        return bool(self.system_ok_after) and (self.artifact_ok is not False)

    @property
    def system_intact(self) -> bool:
        if self.system_ok_after is None:
            return True
        return bool(self.system_ok_after) and (
            self.system_ok_mid is None or bool(self.system_ok_mid)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_fingerprint_before": self.system_before.get("system_fingerprint"),
            "system_fingerprint_mid": (self.system_mid or {}).get("system_fingerprint"),
            "system_fingerprint_after": (self.system_after or {}).get("system_fingerprint"),
            "system_file_count": self.system_before.get("file_count"),
            "system_ok_mid": self.system_ok_mid,
            "system_ok_after": self.system_ok_after,
            "system_intact": self.system_intact,
            "artifact_path": self.artifact_path,
            "artifact_hash_before": self.artifact_hash_before,
            "artifact_hash_after": self.artifact_hash_after,
            "artifact_ok": self.artifact_ok,
            "events": list(self.events),
            "package_root": self.system_before.get("package_root"),
        }


def diff_system_fingerprints(before: Dict[str, Any], after: Dict[str, Any]) -> List[str]:
    """Human-readable list of which package files changed."""
    b = {e["path"]: e["sha256"] for e in before.get("files", [])}
    a = {e["path"]: e["sha256"] for e in after.get("files", [])}
    msgs: List[str] = []
    for p in sorted(set(b) | set(a)):
        if p not in b:
            msgs.append(f"ADDED {p}")
        elif p not in a:
            msgs.append(f"REMOVED {p}")
        elif b[p] != a[p]:
            msgs.append(f"MODIFIED {p}")
    return msgs
