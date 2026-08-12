"""Sandboxed subprocess runner for backend tools."""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from mvpc.canonical import sha256_hex

_DROP_ENV_PREFIXES = ("AWS_", "GITHUB_", "OPENAI_", "ANTHROPIC_", "SSH_", "TOKEN", "SECRET", "PASSWORD")


@dataclass
class SandboxResult:
    argv: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int
    binary_hash: str | None
    cwd: str
    signal: int | None = None
    error: str | None = None
    env_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sanitize_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    base = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", tempfile.gettempdir()),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "TMPDIR": tempfile.gettempdir(),
    }
    for k in ("LEAN_PATH", "LAKE_HOME", "COQLIB", "ISABELLE_HOME"):
        if k in os.environ:
            base[k] = os.environ[k]
    if extra:
        for k, v in extra.items():
            ku = k.upper()
            if any(p in ku for p in _DROP_ENV_PREFIXES):
                continue
            base[k] = v
    return base


def run_sandboxed(
    argv: Sequence[str],
    *,
    cwd: str | Path | None = None,
    timeout_seconds: float = 60.0,
    env: Mapping[str, str] | None = None,
    input_text: str | None = None,
    allow_network: bool = False,
) -> SandboxResult:
    if not argv:
        raise ValueError("argv must be non-empty")
    if isinstance(argv, str):
        raise TypeError("argv must be a sequence of strings, not a shell string")

    argv_list = [str(a) for a in argv]
    work = Path(cwd) if cwd else Path(tempfile.mkdtemp(prefix="mvpc-sbx-"))
    work.mkdir(parents=True, exist_ok=True)

    binary = Path(argv_list[0])
    binary_hash = None
    if binary.is_file():
        try:
            binary_hash = sha256_hex(binary.read_bytes()[:2_000_000])
        except OSError:
            binary_hash = None
    else:
        from shutil import which

        resolved = which(argv_list[0])
        if resolved:
            try:
                binary_hash = sha256_hex(Path(resolved).read_bytes()[:2_000_000])
            except OSError:
                pass

    clean_env = _sanitize_env(env)
    if not allow_network:
        clean_env.setdefault("MVPC_SANDBOX_NETWORK", "deny")

    start = time.monotonic()
    timed_out = False
    error = None
    stdout = ""
    stderr = ""
    rc: int | None = None
    sig = None
    try:
        proc = subprocess.run(
            argv_list,
            cwd=str(work),
            env=clean_env,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
        rc = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if rc is not None and rc < 0:
            sig = -rc
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        error = f"timeout after {timeout_seconds}s"
    except OSError as exc:
        error = str(exc)

    duration_ms = int((time.monotonic() - start) * 1000)
    return SandboxResult(
        argv=argv_list,
        returncode=rc,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        duration_ms=duration_ms,
        binary_hash=binary_hash,
        cwd=str(work),
        signal=sig,
        error=error,
        env_keys=sorted(clean_env.keys()),
    )
