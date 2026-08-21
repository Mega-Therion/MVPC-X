"""LAVA: a truthful language-agnostic verification array for MVPC-X.

The array delegates to existing local MVPC-X backends. It unifies their results
into an explicit receipt and refuses to infer native success from static scans.
No network provider or remote theorem service is contacted.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from shutil import which
from typing import Any

from mvpc.backends.dafny import DafnyBackend
from mvpc.backends.registry import get_default_registry
from mvpc.evidence import EvidenceType
from mvpc.trust import Severity

from .ast_normalizer import NormalizedAst, SourceLanguage


@dataclass(frozen=True)
class BackendReceipt:
    backend: str
    language: str
    native_available: bool
    native_completed: bool
    static_completed: bool
    blockers: tuple[str, ...]
    findings: tuple[dict[str, Any], ...]
    coverage: dict[str, list[str]]
    evidence_types: tuple[str, ...]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _serialize_finding(finding: Any) -> dict[str, Any]:
    severity = getattr(finding, "severity", None)
    return {
        "code": str(getattr(finding, "code", "UNKNOWN")),
        "severity": getattr(severity, "value", str(severity or "UNKNOWN")),
        "message": str(getattr(finding, "message", "")),
        "system": str(getattr(finding, "system", "")),
        "line": getattr(finding, "line", None),
        "remediation": getattr(finding, "remediation", None),
    }


class LanguageAgnosticVerificationArray:
    """Run registered local backends and report their actual coverage."""

    def inspect(self, ast: NormalizedAst) -> BackendReceipt:
        """Describe the candidate backend without reading or executing an artifact."""
        names = {
            SourceLanguage.LEAN: "Lean 4",
            SourceLanguage.ROCQ: "Rocq/Coq",
            SourceLanguage.ISABELLE: "Isabelle/HOL",
            SourceLanguage.DAFNY: "Dafny/Z3",
        }
        if not ast.is_formal_source:
            return BackendReceipt(
                backend="none",
                language=ast.language.value,
                native_available=False,
                native_completed=False,
                static_completed=False,
                blockers=(),
                findings=(),
                coverage={
                    "checks_performed": ["Structural normalization"],
                    "checks_unavailable": ["Formal backend requires a formal artifact"],
                    "assumptions": [],
                    "trust_boundaries": [
                        "No native backend was executed during inspect"
                    ],
                },
                evidence_types=(),
                notes=("Inspection does not execute a formal backend.",),
            )
        availability = {
            SourceLanguage.LEAN: which("lean") is not None or which("lake") is not None,
            SourceLanguage.ROCQ: which("coqc") is not None,
            SourceLanguage.ISABELLE: which("isabelle") is not None,
            SourceLanguage.DAFNY: which("dafny") is not None,
        }.get(ast.language, False)
        return BackendReceipt(
            backend=names[ast.language],
            language=ast.language.value,
            native_available=availability,
            native_completed=False,
            static_completed=False,
            blockers=(),
            findings=(),
            coverage={
                "checks_performed": ["Structural normalization"],
                "checks_unavailable": [
                    "Native verification was intentionally not run during inspect"
                ],
                "assumptions": [],
                "trust_boundaries": ["Inspection mode is non-executing"],
            },
            evidence_types=(),
            notes=(
                "Inspection identifies the applicable local backend but never launches it.",
            ),
        )

    def audit(self, path: str | Path, ast: NormalizedAst) -> BackendReceipt:
        source_path = str(Path(path).resolve(strict=True))
        if not ast.is_formal_source:
            return BackendReceipt(
                backend="none",
                language=ast.language.value,
                native_available=False,
                native_completed=False,
                static_completed=False,
                blockers=(),
                findings=(),
                coverage={
                    "checks_performed": [],
                    "checks_unavailable": [],
                    "assumptions": [],
                    "trust_boundaries": ["Formal artifact required"],
                },
                evidence_types=(),
                notes=("Informal source is not sent to a formal backend.",),
            )
        if ast.language is SourceLanguage.DAFNY:
            return self._audit_dafny(source_path, ast)
        backend = get_default_registry().get_backend(source_path)
        if not backend.supports(source_path):
            return BackendReceipt(
                backend="unsupported",
                language=ast.language.value,
                native_available=False,
                native_completed=False,
                static_completed=False,
                blockers=(
                    f"No registered backend supports {Path(source_path).suffix}.",
                ),
                findings=(),
                coverage={
                    "checks_performed": [],
                    "checks_unavailable": ["No formal backend"],
                    "assumptions": [],
                    "trust_boundaries": ["Unsupported source extension"],
                },
                evidence_types=(),
                notes=("A source extension alone is not a verification backend.",),
            )
        findings, evidence, coverage = backend.audit(source_path)
        serialized = tuple(_serialize_finding(item) for item in findings)
        blockers = tuple(
            item["code"]
            for item in serialized
            if item["severity"] == Severity.VIOLATION.value
        )
        evidence_types = tuple(sorted({item.evidence_type.name for item in evidence}))
        native_available = bool(backend.check_native_available())
        native_evidence = any(
            item.evidence_type is EvidenceType.NATIVE_VERIFICATION for item in evidence
        )
        native_completed = native_available and native_evidence and not blockers
        return BackendReceipt(
            backend=backend.name(),
            language=ast.language.value,
            native_available=native_available,
            native_completed=native_completed,
            static_completed=any(
                item.evidence_type is EvidenceType.STATIC_ANALYSIS for item in evidence
            ),
            blockers=blockers,
            findings=serialized,
            coverage={
                "checks_performed": list(coverage.checks_performed),
                "checks_unavailable": list(coverage.checks_unavailable),
                "assumptions": list(coverage.assumptions),
                "trust_boundaries": list(coverage.trust_boundaries),
            },
            evidence_types=evidence_types,
            notes=(
                "Native completion requires an actual native evidence record; static analysis alone remains conditional.",
            ),
        )

    def _audit_dafny(self, source_path: str, ast: NormalizedAst) -> BackendReceipt:
        backend = DafnyBackend()
        available = which(backend.binary) is not None
        if not available:
            return BackendReceipt(
                backend="Dafny/Z3",
                language=ast.language.value,
                native_available=False,
                native_completed=False,
                static_completed=True,
                blockers=(),
                findings=(),
                coverage={
                    "checks_performed": ["Structural normalization"],
                    "checks_unavailable": [
                        "Dafny native verification (dafny binary missing)"
                    ],
                    "assumptions": [],
                    "trust_boundaries": ["No Dafny executable available"],
                },
                evidence_types=("STATIC_ANALYSIS",),
                notes=(
                    "Dafny source remains conditional until `dafny verify` completes.",
                ),
            )
        raw = backend.execute(backend.prepare(source_path))
        verdict = backend.validate(raw)
        passed = verdict.get("verdict") == "FORMALLY_CHECKED"
        blocker = (
            () if passed else (str(verdict.get("reason", "dafny verification failed")),)
        )
        return BackendReceipt(
            backend="Dafny/Z3",
            language=ast.language.value,
            native_available=True,
            native_completed=passed,
            static_completed=True,
            blockers=blocker,
            findings=(),
            coverage={
                "checks_performed": [
                    "Structural normalization",
                    "Dafny native verification",
                ],
                "checks_unavailable": [],
                "assumptions": [],
                "trust_boundaries": [],
            },
            evidence_types=("STATIC_ANALYSIS", "NATIVE_VERIFICATION"),
            notes=(str(verdict.get("reason", "")),),
        )
