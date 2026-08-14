"""Hardcoded NEWTON ARCHITECT system directive for MVPC-X."""

from __future__ import annotations

import re
from typing import Iterable, List

from mvpc.trust import Finding, Severity

AUTHORITY = "NEWTON ARCHITECT Protocol"
REFERENCE = "BobsDirections.md"
STATUS = "In Progress (Audit Complete)"

CLAIM_LABELS = ("P", "C", "O")

AREA_OPERATOR_REQUIRED = "A_hat = 8 * pi * gamma * l_P**2 * sum(sqrt(j*(j+1)))"
ENTROPY_REQUIRED = "S_hat = A_hat / (4 * l_P**2)"
FORBIDDEN_AREA_OPERATOR = "L_A = (1 / (4 * G_N)) * sum(C_2(rho))"

OMEGA_LAMBDA_Z0 = "ln(2)"
A0_HORIZON_RELATION = "a0 = c * H0 / (2 * pi)"
EPOCH_DEPENDENT_RELATIONS = (
    "Omega_Lambda(z=0) = ln(2)",
    "a0 = c * H0 / (2 * pi)",
)

LEAN_FORBIDDEN_PLACEHOLDERS = (": True := trivial",)
LEAN_MANDATORY_CHECK = "#print axioms"

PLANCK_FORCE_N = 4.815454e42
A0_PLANCK_2018 = 1.042198e-10
A0_SHOES_2022 = 1.129409e-10
SPARC_A0 = 1.20e-10
OMEGA_LAMBDA_LN2 = 0.693147
OMEGA_LAMBDA_PLANCK_2018 = 0.6889

_PCO_RE = re.compile(r"\[(P|C|O|P/O)\]")
_VACUOUS_RE = re.compile(r":\s*True\s*:=\s*trivial")
_FORBIDDEN_AREA_RE = re.compile(
    r"(?<!sqrt\()(?<!\\sqrt\{)\\?sum\s*C_2|sum\s*\(\s*C_2"
)
_OMEGA_LN2_RE = re.compile(
    r"(?:\\Omega_\\Lambda|Omega_?Lambda|\\Omega_\\Lambda)\s*=\s*(?:\\ln\s*2|ln\s*2)"
)
_OMEGA_Z0_RE = re.compile(r"z\s*=\s*0")
_A0_RE = re.compile(
    r"(?:a_0|a0)\s*=\s*(?:c\s*H_0|c\s*\*?\s*H0|\\frac\{c\s*H_0\}\{2\\pi\})"
)
_TIME_INDEPENDENT_RE = re.compile(
    r"time-independent cosmological derivation", re.IGNORECASE
)

NEWTON_ARCHITECT_SYSTEM_DIRECTIVE = """# NEWTON Verification Audit & Resolution Plan
**Authority:** NEWTON ARCHITECT Protocol
**Reference:** `BobsDirections.md`
**Status:** In Progress (Audit Complete)

All material claims are labeled in strict compliance with the [P] / [C] / [O] protocol.
Required area operator: A_hat = 8 pi gamma l_P^2 sum sqrt(j(j+1)).
Omega_Lambda(z=0) = ln 2 and a0 = c H0 / 2pi are epoch-dependent [O] relations.
Forbidden: : True := trivial Lean placeholders. Mandatory: #print axioms.
"""


def system_directive() -> str:
    """Return the hardcoded Newton Architect system directive."""
    return NEWTON_ARCHITECT_SYSTEM_DIRECTIVE


def requires_pco_label(claim: str) -> bool:
    """Every material claim must carry a [P], [C], or [O] label."""
    return True


def has_pco_label(text: str) -> bool:
    return bool(_PCO_RE.search(text or ""))


def scan_artifact_text(text: str, *, system: str = "NewtonArchitect") -> List[Finding]:
    """Emit findings that enforce the Newton Architect protocol on source text."""
    findings: List[Finding] = []
    if not text:
        return findings

    for i, line in enumerate(text.splitlines(), start=1):
        if _VACUOUS_RE.search(line):
            findings.append(
                Finding(
                    code="NEWTON_VACUOUS_PROOF",
                    severity=Severity.VIOLATION,
                    message="Vacuous Lean placeholder `: True := trivial` is forbidden",
                    system=system,
                    line=i,
                    remediation="Strip placeholder theorems and run #print axioms",
                )
            )
        if _FORBIDDEN_AREA_RE.search(line) and "sqrt" not in line:
            findings.append(
                Finding(
                    code="NEWTON_AREA_OPERATOR",
                    severity=Severity.VIOLATION,
                    message=(
                        "Non-standard area operator sum C_2 without sqrt(j(j+1)); "
                        f"required form is {AREA_OPERATOR_REQUIRED}"
                    ),
                    system=system,
                    line=i,
                    remediation=AREA_OPERATOR_REQUIRED,
                )
            )

    if _OMEGA_LN2_RE.search(text) and not _OMEGA_Z0_RE.search(text):
        findings.append(
            Finding(
                code="NEWTON_EPOCH_OMEGA",
                severity=Severity.VIOLATION,
                message="Omega_Lambda = ln 2 must be declared at epoch z=0 as an [O] relation",
                system=system,
                remediation="Write Omega_Lambda(z=0) = ln 2 and label [O]",
            )
        )

    if _A0_RE.search(text) and "[O]" not in text and "[P]" in text:
        findings.append(
            Finding(
                code="NEWTON_A0_OVERCLAIM",
                severity=Severity.VIOLATION,
                message="a0 = c H0 / 2pi is an order-of-magnitude horizon relation [O], not an exact [P] derivation",
                system=system,
                remediation="Relabel a0 = c H0 / 2pi as [O]",
            )
        )

    if _TIME_INDEPENDENT_RE.search(text):
        findings.append(
            Finding(
                code="NEWTON_OVERREACH",
                severity=Severity.VIOLATION,
                message="Time-independent cosmological derivation claims are forbidden by Newton Architect",
                system=system,
                remediation="Classify Omega_Lambda(z=0)=ln 2 and a0=c H0/2pi as epoch-dependent [O]",
            )
        )

    return findings


def merge_newton_findings(findings: Iterable[Finding], text: str) -> List[Finding]:
    merged = list(findings)
    merged.extend(scan_artifact_text(text))
    return merged
