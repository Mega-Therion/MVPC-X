from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Set, List, Optional

from mvpc.trust import AttestationState, Finding, Severity, CoverageReport
from mvpc.newton_architect import (
    AUTHORITY,
    LEAN_FORBIDDEN_PLACEHOLDERS,
    merge_newton_findings,
)


class PolicyLevel(Enum):
    PERMISSIVE = auto()
    DEFAULT = auto()
    STRICT = auto()


@dataclass
class Policy:
    level: PolicyLevel
    require_native_verification: bool
    allow_static_only: bool
    allowed_axioms: Set[str]
    blocked_patterns: List[str]
    require_human_signoff: bool
    authority: str = AUTHORITY
    newton_enforced: bool = True


def get_policy(level: PolicyLevel) -> Policy:
    """Factory function to get a policy based on level."""
    newton_blocks = list(LEAN_FORBIDDEN_PLACEHOLDERS) + [
        "sum C_2",
        "time-independent cosmological derivation",
    ]
    if level == PolicyLevel.PERMISSIVE:
        return Policy(
            level=level,
            require_native_verification=False,
            allow_static_only=True,
            allowed_axioms={"propext", "Classical.choice", "Quot.sound"},
            blocked_patterns=newton_blocks,
            require_human_signoff=False,
        )
    elif level == PolicyLevel.DEFAULT:
        return Policy(
            level=level,
            require_native_verification=True,
            allow_static_only=False,
            allowed_axioms={"propext", "Classical.choice", "Quot.sound"},
            blocked_patterns=newton_blocks,
            require_human_signoff=False,
        )
    elif level == PolicyLevel.STRICT:
        return Policy(
            level=level,
            require_native_verification=True,
            allow_static_only=False,
            allowed_axioms=set(),
            blocked_patterns=["sorry", "admit", "native_decide"] + newton_blocks,
            require_human_signoff=True,
        )
    raise ValueError(f"Unknown policy level: {level}")


def evaluate_attestation(
    findings: List[Finding],
    coverage: CoverageReport,
    policy: Policy,
    artifact_text: Optional[str] = None,
    statement: Optional[str] = None,
) -> AttestationState:
    """Evaluate attestation state based on findings, coverage, and policy."""
    combined = list(findings)
    if getattr(policy, "newton_enforced", True):
        if artifact_text:
            combined = merge_newton_findings(combined, artifact_text)
        if statement:
            combined = merge_newton_findings(combined, statement)

    if any(f.severity == Severity.VIOLATION for f in combined):
        return AttestationState.REJECTED

    has_native = "Native Verification" in coverage.checks_performed
    has_static = "Static Analysis" in coverage.checks_performed

    if policy.level == PolicyLevel.STRICT:
        if not has_native:
            return AttestationState.REJECTED
        return AttestationState.VERIFIED

    if policy.level == PolicyLevel.DEFAULT:
        if has_native:
            return AttestationState.VERIFIED
        elif has_static:
            return AttestationState.CONDITIONAL
        else:
            return AttestationState.UNVERIFIED

    if policy.level == PolicyLevel.PERMISSIVE:
        if has_native or has_static:
            return AttestationState.VERIFIED
        return AttestationState.UNVERIFIED

    return AttestationState.UNVERIFIED
