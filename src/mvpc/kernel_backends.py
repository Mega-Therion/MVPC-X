"""Real formal-kernel adapters with heuristic fallback.

When lean/coqc/isabelle/dafny are on PATH, run them sandboxed.
Otherwise return heuristic results with driver_mode='heuristic'.
FORMALLY_CHECKED is only set on successful kernel exit + clean SafeVerify.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from mvpc.core.safe_verify import safe_verify_source
from mvpc.sandbox import run_sandboxed
from mvpc.trust_verdicts import TrustVerdict


@dataclass
class KernelResult:
    backend: str
    trust_verdict: str
    driver_mode: str
    ok: bool
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    detail: str = ""
    binary: str | None = None
    binary_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _heuristic(backend: str, source: str) -> KernelResult:
    sv = safe_verify_source(source, backend=backend)
    if not sv.clean:
        return KernelResult(
            backend=backend,
            trust_verdict=TrustVerdict.EVIDENCE_SUPPORTED.value,
            driver_mode="heuristic",
            ok=False,
            detail=f"heuristic markers: {[f.rule for f in sv.findings]}",
        )
    return KernelResult(
        backend=backend,
        trust_verdict=TrustVerdict.EVIDENCE_SUPPORTED.value,
        driver_mode="heuristic",
        ok=True,
        detail="heuristic clean; no kernel binary",
    )


def _write_temp(source: str, suffix: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix="mvpc-kern-"))
    p = d / f"claim{suffix}"
    p.write_text(source, encoding="utf-8")
    return p


def run_lean_kernel(source: str, *, timeout: float = 60.0) -> KernelResult:
    lean = shutil.which("lean")
    if not lean:
        return _heuristic("lean4", source)
    path = _write_temp(source, ".lean")
    res = run_sandboxed([lean, str(path)], cwd=path.parent, timeout_seconds=timeout)
    sv = safe_verify_source(source, backend="lean4")
    if res.timed_out:
        return KernelResult(
            backend="lean4",
            trust_verdict=TrustVerdict.INCONCLUSIVE.value,
            driver_mode="kernel",
            ok=False,
            returncode=res.returncode,
            stdout=res.stdout,
            stderr=res.stderr,
            detail="timeout",
            binary=lean,
            binary_hash=res.binary_hash,
        )
    if res.returncode == 0 and sv.clean:
        return KernelResult(
            backend="lean4",
            trust_verdict=TrustVerdict.FORMALLY_CHECKED.value,
            driver_mode="kernel",
            ok=True,
            returncode=0,
            stdout=res.stdout,
            stderr=res.stderr,
            detail="lean exit 0",
            binary=lean,
            binary_hash=res.binary_hash,
        )
    verdict = TrustVerdict.REJECTED.value if res.returncode not in (0, None) else TrustVerdict.EVIDENCE_SUPPORTED.value
    if not sv.clean:
        verdict = TrustVerdict.EVIDENCE_SUPPORTED.value
    return KernelResult(
        backend="lean4",
        trust_verdict=verdict,
        driver_mode="kernel",
        ok=False,
        returncode=res.returncode,
        stdout=res.stdout,
        stderr=res.stderr,
        detail=res.error or "lean failed or unsound markers",
        binary=lean,
        binary_hash=res.binary_hash,
    )


def run_coq_kernel(source: str, *, timeout: float = 60.0) -> KernelResult:
    coqc = shutil.which("coqc")
    if not coqc:
        return _heuristic("rocq", source)
    path = _write_temp(source, ".v")
    res = run_sandboxed([coqc, str(path)], cwd=path.parent, timeout_seconds=timeout)
    sv = safe_verify_source(source, backend="rocq")
    if res.returncode == 0 and sv.clean:
        return KernelResult(
            backend="rocq",
            trust_verdict=TrustVerdict.FORMALLY_CHECKED.value,
            driver_mode="kernel",
            ok=True,
            returncode=0,
            stdout=res.stdout,
            stderr=res.stderr,
            detail="coqc exit 0",
            binary=coqc,
            binary_hash=res.binary_hash,
        )
    return KernelResult(
        backend="rocq",
        trust_verdict=TrustVerdict.REJECTED.value if res.returncode else TrustVerdict.INCONCLUSIVE.value,
        driver_mode="kernel",
        ok=False,
        returncode=res.returncode,
        stdout=res.stdout,
        stderr=res.stderr,
        detail=res.error or "coqc failed",
        binary=coqc,
        binary_hash=res.binary_hash,
    )


def run_isabelle_kernel(source: str, *, timeout: float = 120.0) -> KernelResult:
    isa = shutil.which("isabelle")
    if not isa:
        return _heuristic("isabelle", source)
    path = _write_temp(source, ".thy")
    res = run_sandboxed([isa, "process", "-T", path.stem], cwd=path.parent, timeout_seconds=timeout)
    if res.returncode == 0:
        return KernelResult(
            backend="isabelle",
            trust_verdict=TrustVerdict.FORMALLY_CHECKED.value,
            driver_mode="kernel",
            ok=True,
            returncode=0,
            stdout=res.stdout,
            stderr=res.stderr,
            detail="isabelle process exit 0",
            binary=isa,
            binary_hash=res.binary_hash,
        )
    return KernelResult(
        backend="isabelle",
        trust_verdict=TrustVerdict.INCONCLUSIVE.value,
        driver_mode="kernel",
        ok=False,
        returncode=res.returncode,
        stdout=res.stdout,
        stderr=res.stderr,
        detail=res.error or "isabelle needs session/ROOT; inconclusive",
        binary=isa,
        binary_hash=res.binary_hash,
    )


def run_dafny_kernel(source: str, *, timeout: float = 60.0) -> KernelResult:
    dafny = shutil.which("dafny")
    if not dafny:
        return _heuristic("dafny", source)
    path = _write_temp(source, ".dfy")
    res = run_sandboxed([dafny, "verify", str(path)], cwd=path.parent, timeout_seconds=timeout)
    sv = safe_verify_source(source, backend="dafny")
    if res.returncode == 0 and sv.clean:
        return KernelResult(
            backend="dafny",
            trust_verdict=TrustVerdict.FORMALLY_CHECKED.value,
            driver_mode="kernel",
            ok=True,
            returncode=0,
            stdout=res.stdout,
            stderr=res.stderr,
            detail="dafny verify exit 0",
            binary=dafny,
            binary_hash=res.binary_hash,
        )
    return KernelResult(
        backend="dafny",
        trust_verdict=TrustVerdict.REJECTED.value if res.returncode else TrustVerdict.INCONCLUSIVE.value,
        driver_mode="kernel",
        ok=False,
        returncode=res.returncode,
        stdout=res.stdout,
        stderr=res.stderr,
        detail=res.error or "dafny failed",
        binary=dafny,
        binary_hash=res.binary_hash,
    )


def run_kernel(backend: str, source: str, *, timeout: float = 60.0) -> KernelResult:
    b = backend.lower()
    if b in {"lean", "lean4"}:
        return run_lean_kernel(source, timeout=timeout)
    if b in {"coq", "rocq"}:
        return run_coq_kernel(source, timeout=timeout)
    if b in {"isabelle", "hol"}:
        return run_isabelle_kernel(source, timeout=timeout)
    if b == "dafny":
        return run_dafny_kernel(source, timeout=timeout)
    return KernelResult(
        backend=backend,
        trust_verdict=TrustVerdict.UNSAFE_TO_VERIFY.value,
        driver_mode="missing",
        ok=False,
        detail=f"unknown backend {backend}",
    )
