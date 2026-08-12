from enum import Enum, auto
from dataclasses import dataclass
from typing import Set, List
from mvpc.trust import AttestationState, Finding, Severity, CoverageReport

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

def get_policy(level: PolicyLevel) -> Policy:
    """Factory function to get a policy based on level."""
    if level == PolicyLevel.PERMISSIVE:
        return Policy(
            level=level,
            require_native_verification=False,
            allow_static_only=True,
            allowed_axioms={"propext", "Classical.choice", "Quot.sound"},
            blocked_patterns=[],
            require_human_signoff=False
        )
    elif level == PolicyLevel.DEFAULT:
        return Policy(
            level=level,
            require_native_verification=True,
            allow_static_only=False, # Static analysis -> CONDITIONAL
            allowed_axioms={"propext", "Classical.choice", "Quot.sound"},
            blocked_patterns=[],
            require_human_signoff=False
        )
    elif level == PolicyLevel.STRICT:
        return Policy(
            level=level,
            require_native_verification=True,
            allow_static_only=False,
            allowed_axioms=set(), # No axioms allowed
            blocked_patterns=["sorry", "admit", "native_decide"],
            require_human_signoff=True
        )
    raise ValueError(f"Unknown policy level: {level}")

def evaluate_attestation(findings: List[Finding], coverage: CoverageReport, policy: Policy) -> AttestationState:
    """Evaluate attestation state based on findings, coverage, and policy."""
    # If any violations found, it's rejected
    if any(f.severity == Severity.VIOLATION for f in findings):
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
