"""Dafny weakest-precondition / Z3 backend scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mvpc.sandbox import run_sandboxed
from mvpc.trust_verdicts import TrustVerdict


class DafnyBackend:
    name = "dafny"

    def __init__(self, binary: str = "dafny", timeout: float = 60.0) -> None:
        self.binary = binary
        self.timeout = timeout

    def prepare(self, source_path: str | Path) -> dict[str, Any]:
        path = Path(source_path)
        text = path.read_text(encoding="utf-8")
        return {"path": str(path), "source": text}

    def execute(self, prepared: dict[str, Any]) -> dict[str, Any]:
        path = prepared["path"]
        result = run_sandboxed(
            [self.binary, "verify", path],
            timeout_seconds=self.timeout,
            cwd=str(Path(path).parent),
        )
        return result.to_dict()

    def validate(self, raw: dict[str, Any]) -> dict[str, Any]:
        if raw.get("timed_out"):
            return {"verdict": TrustVerdict.INCONCLUSIVE.value, "reason": "timeout"}
        if raw.get("error"):
            return {"verdict": TrustVerdict.UNSAFE_TO_VERIFY.value, "reason": raw["error"]}
        rc = raw.get("returncode")
        if rc == 0:
            return {"verdict": TrustVerdict.FORMALLY_CHECKED.value, "reason": "dafny verify exit 0"}
        return {"verdict": TrustVerdict.REJECTED.value, "reason": raw.get("stderr") or "dafny verify failed"}
