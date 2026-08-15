"""Preflight readiness checks — classify input, probe tools, never crash."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from shutil import which
from typing import Any, Dict, List, Optional

from mvpc.backends.registry import get_default_registry
from mvpc.newton_architect import scan_artifact_text
from mvpc.security import (
    DEFAULT_MAX_ARTIFACT_BYTES,
    compute_system_fingerprint,
    validate_intake,
)


class Readiness(str, Enum):
    READY_DEEP = "ready_for_deep_audit"
    NEEDS_PROJECT_CONTEXT = "needs_project_context"
    TEMPLATE_SUGGESTED = "template_suggested"
    GENERIC_ONLY = "generic_only"
    BLOCKED = "blocked"


@dataclass
class PreflightReport:
    path: str
    readiness: Readiness
    backend_name: str
    intake_allowed: bool
    intake_reasons: List[str]
    tools: Dict[str, bool]
    structure_score: int  # 0-100
    structure_notes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    system_fingerprint: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["readiness"] = self.readiness.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def _probe_tools() -> Dict[str, bool]:
    return {
        "lean": which("lean") is not None,
        "lake": which("lake") is not None,
        "coqc": which("coqc") is not None,
        "coqtop": which("coqtop") is not None,
        "isabelle": which("isabelle") is not None,
        "python3": which("python3") is not None or which("python") is not None,
        "sympy": _can_import("sympy"),
        "z3": _can_import("z3"),
        "numpy": _can_import("numpy"),
    }


def _can_import(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def _score_lean(path: Path, text: str) -> tuple[int, List[str], List[str]]:
    notes: List[str] = []
    recs: List[str] = []
    score = 40
    if re.search(r"(?m)^(?:theorem|lemma)\s+", text):
        score += 20
        notes.append("Has theorem/lemma declarations")
    else:
        notes.append("No theorem/lemma found")
        recs.append("Use `mvpc scaffold lean` or add a real theorem/lemma")
    if re.search(r"\b(sorry|admit)\b", text):
        score -= 25
        notes.append("Contains sorry/admit")
    if re.search(r"(?m)^\s*axiom\s+", text):
        score -= 20
        notes.append("Bare axiom present")
    parent = path.parent
    has_lake = (parent / "lakefile.lean").exists() or (
        parent / "lakefile.toml"
    ).exists()
    if not has_lake:
        # search one up
        has_lake = (parent.parent / "lakefile.lean").exists() or (
            parent.parent / "lakefile.toml"
        ).exists()
    if has_lake:
        score += 25
        notes.append("Lake project context detected")
    else:
        notes.append("No lakefile nearby")
        recs.append("Open/run inside a Lake project if this file imports Mathlib")
    if "import" in text or "Mathlib" in text:
        notes.append("Has imports (may need lake env)")
        if not has_lake:
            score -= 10

    # Newton Architect gates readiness too. Without this, a file of
    # `theorem X : True := trivial` scored 40 + 20 (has theorem) + 25 (lake)
    # = 85 -> READY_DEEP, because nothing here looked for vacuous proofs.
    # That is the exact pattern the Res-Nova vacuity audit found in the wild.
    #
    # A vacuous placeholder is worse than `sorry` (-25): `sorry` is honest
    # about being a hole, `: True := trivial` masquerades as a finished proof.
    # Delegate the detection to scan_artifact_text so the rules live in one
    # place, and clamp hard so no such file can reach READY_DEEP (>= 60).
    newton_findings = scan_artifact_text(text)
    if newton_findings:
        score -= 40 * len(newton_findings)
        score = min(score, 35)
        for f in newton_findings:
            notes.append(f"Newton Architect violation: {f.code} — {f.message}")
            if f.remediation:
                recs.append(f.remediation)

    return max(0, min(100, score)), notes, recs


# No Newton scan below: the protocol's syntactic rules are Lean-flavoured
# (`: True := trivial`, `#print axioms`). The semantic rules it also carries —
# the a0 and Omega_Lambda epoch checks — are prose-level and already enforced
# at verification time by nexus_pipeline and mvpc.policy, which see every
# backend. This asymmetry is deliberate, not an oversight.
def _score_coq(path: Path, text: str) -> tuple[int, List[str], List[str]]:
    notes, recs = [], []
    score = 45
    if re.search(r"(?m)^(?:Theorem|Lemma)\s+", text):
        score += 25
        notes.append("Has Theorem/Lemma")
    else:
        recs.append("Add Theorem/Lemma or `mvpc scaffold coq`")
    if re.search(r"\b(Admitted|admit)\b", text):
        score -= 25
        notes.append("Admitted/admit present")
    if re.search(r"(?m)^\s*Axiom\s+", text):
        score -= 15
        notes.append("Axiom declaration present")
    if "Qed." in text:
        score += 15
        notes.append("Contains Qed")
    return max(0, min(100, score)), notes, recs


def _score_isabelle(text: str) -> tuple[int, List[str], List[str]]:
    notes, recs = [], []
    score = 45
    if "theory " in text or text.strip().startswith("theory"):
        score += 15
        notes.append("Theory header present")
    if re.search(r"\b(lemma|theorem)\b", text):
        score += 20
    if re.search(r"\b(sorry|oops)\b", text):
        score -= 25
        notes.append("sorry/oops present")
    if re.search(r"\baxiomatization\b", text):
        score -= 20
    return max(0, min(100, score)), notes, recs


def _score_python(text: str) -> tuple[int, List[str], List[str]]:
    notes, recs = [], []
    score = 35
    if re.search(r"(?:MVPC-CLAIM|BIOMECH-CLAIM)", text):
        score += 40
        notes.append("Embedded MVPC-CLAIM / BIOMECH-CLAIM blocks found")
    else:
        notes.append("No MVPC-CLAIM blocks")
        recs.append("Add `# MVPC-CLAIM identity: ...` or `mvpc scaffold python-math`")
    if re.search(r"\b(eval|exec)\s*\(", text):
        score -= 30
        notes.append("eval/exec present — will be flagged")
    if "def " in text:
        score += 10
    return max(0, min(100, score)), notes, recs


def run_preflight(
    path: str,
    *,
    max_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
    allow_symlinks: bool = False,
) -> PreflightReport:
    path = os.path.abspath(path)
    intake = validate_intake(path, max_bytes=max_bytes, allow_symlinks=allow_symlinks)
    tools = _probe_tools()
    try:
        fp = compute_system_fingerprint()["system_fingerprint"]
    except Exception:
        fp = None

    if not intake.allowed:
        return PreflightReport(
            path=path,
            readiness=Readiness.BLOCKED,
            backend_name="none",
            intake_allowed=False,
            intake_reasons=intake.reasons,
            tools=tools,
            structure_score=0,
            recommendations=[
                "Fix intake issues before audit",
                "See docs/INPUT_CONTRACT.md",
            ],
            system_fingerprint=fp,
            details=intake.to_dict(),
        )

    registry = get_default_registry()
    backend = registry.get_backend(path)
    bname = backend.name()

    structure_score = 20
    notes: List[str] = []
    recs: List[str] = list(intake.reasons) if intake.reasons != ["Intake OK"] else []

    p = Path(path)
    text = ""
    if p.is_file():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")[:2_000_000]
        except OSError as e:
            notes.append(f"Could not read file: {e}")

    readiness = Readiness.GENERIC_ONLY

    if bname.startswith("Lean"):
        structure_score, n2, r2 = _score_lean(p, text)
        notes.extend(n2)
        recs.extend(r2)
        if tools["lean"] or tools["lake"]:
            readiness = (
                Readiness.READY_DEEP
                if structure_score >= 60
                else Readiness.NEEDS_PROJECT_CONTEXT
            )
        else:
            readiness = Readiness.NEEDS_PROJECT_CONTEXT
            recs.append("Install Lean 4 (elan) for native kernel audit")
        if structure_score < 40:
            readiness = Readiness.TEMPLATE_SUGGESTED
    elif bname.startswith("Coq"):
        structure_score, n2, r2 = _score_coq(p, text)
        notes.extend(n2)
        recs.extend(r2)
        readiness = (
            Readiness.READY_DEEP
            if (tools["coqc"] and structure_score >= 50)
            else Readiness.NEEDS_PROJECT_CONTEXT
        )
        if not tools["coqc"]:
            recs.append("Install coqc for native verification")
    elif bname.startswith("Isabelle"):
        structure_score, n2, r2 = _score_isabelle(text)
        notes.extend(n2)
        recs.extend(r2)
        readiness = (
            Readiness.READY_DEEP
            if tools["isabelle"] and structure_score >= 50
            else Readiness.NEEDS_PROJECT_CONTEXT
        )
    elif "Python" in bname:
        structure_score, n2, r2 = _score_python(text)
        notes.extend(n2)
        recs.extend(r2)
        if structure_score >= 60:
            readiness = Readiness.READY_DEEP
        elif structure_score >= 35:
            readiness = Readiness.TEMPLATE_SUGGESTED
        else:
            readiness = Readiness.TEMPLATE_SUGGESTED
        if not tools["sympy"]:
            recs.append("pip install sympy  # for identity claims")
        if not tools["z3"]:
            recs.append("pip install z3-solver  # for constraint claims")
    else:
        notes.append("No specialized backend — generic hash path only")
        recs.append(
            "Use `mvpc scaffold claim` or a supported extension (.lean/.v/.thy/.py)"
        )
        readiness = Readiness.GENERIC_ONLY
        structure_score = 15

    # de-dupe recs
    seen = set()
    uniq_recs = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            uniq_recs.append(r)

    return PreflightReport(
        path=path,
        readiness=readiness,
        backend_name=bname,
        intake_allowed=True,
        intake_reasons=intake.reasons,
        tools=tools,
        structure_score=structure_score,
        structure_notes=notes,
        recommendations=uniq_recs,
        system_fingerprint=fp,
        details={
            "resolved_path": intake.resolved_path,
            "size_bytes": intake.size_bytes,
            "is_symlink": intake.is_symlink,
        },
    )


def format_preflight_terminal(report: PreflightReport) -> str:
    lines = [
        "=" * 70,
        " MVPC-X PREFLIGHT",
        "=" * 70,
        f" Path       : {report.path}",
        f" Backend    : {report.backend_name}",
        f" Readiness  : {report.readiness.value}",
        f" Structure  : {report.structure_score}/100",
        f" Intake     : {'ALLOW' if report.intake_allowed else 'BLOCK'}",
    ]
    if report.system_fingerprint:
        lines.append(f" System FP  : {report.system_fingerprint[:24]}…")
    lines.append("\n Tools:")
    for k, v in sorted(report.tools.items()):
        lines.append(f"  {'✓' if v else '·'} {k}")
    if report.structure_notes:
        lines.append("\n Structure notes:")
        for n in report.structure_notes:
            lines.append(f"  - {n}")
    if report.recommendations:
        lines.append("\n Recommendations:")
        for r in report.recommendations:
            lines.append(f"  → {r}")
    if report.intake_reasons:
        lines.append("\n Intake detail:")
        for r in report.intake_reasons:
            lines.append(f"  - {r}")
    lines.append("=" * 70)
    lines.append(" Ingest is open. Assurance is proportional to structure + tools.")
    lines.append("=" * 70)
    return "\n".join(lines)
