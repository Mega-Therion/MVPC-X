"""Atomic trust verdict taxonomy for MVPC-X."""

from __future__ import annotations

from enum import Enum


class TrustVerdict(str, Enum):
    """Nine atomic verification outcomes. Never collapse to bare 'verified'."""

    FORMALLY_CHECKED = "FORMALLY_CHECKED"
    COMPUTATION_VERIFIED = "COMPUTATION_VERIFIED"
    EXECUTION_OBSERVED = "EXECUTION_OBSERVED"
    EVIDENCE_SUPPORTED = "EVIDENCE_SUPPORTED"
    HUMAN_ATTESTED = "HUMAN_ATTESTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    REJECTED = "REJECTED"
    UNSAFE_TO_VERIFY = "UNSAFE_TO_VERIFY"
    CONFLICTING_VERDICTS = "CONFLICTING_VERDICTS"

    @property
    def implies_truth(self) -> bool:
        return self in {
            TrustVerdict.FORMALLY_CHECKED,
            TrustVerdict.COMPUTATION_VERIFIED,
        }

    @property
    def is_negative(self) -> bool:
        return self in {
            TrustVerdict.REJECTED,
            TrustVerdict.UNSAFE_TO_VERIFY,
            TrustVerdict.CONFLICTING_VERDICTS,
            TrustVerdict.INCONCLUSIVE,
        }

    @property
    def description(self) -> str:
        return _DESCRIPTIONS[self]

    def display_label(self) -> str:
        return self.value


_DESCRIPTIONS = {
    TrustVerdict.FORMALLY_CHECKED: (
        "A named formal checker accepted a theorem under captured assumptions."
    ),
    TrustVerdict.COMPUTATION_VERIFIED: (
        "A deterministic computation or identity check passed under a specified environment."
    ),
    TrustVerdict.EXECUTION_OBSERVED: (
        "A controlled execution emitted recorded output; this is not proof."
    ),
    TrustVerdict.EVIDENCE_SUPPORTED: (
        "Evidence met a declared policy threshold; this is not proof."
    ),
    TrustVerdict.HUMAN_ATTESTED: (
        "A person or system signed a scoped statement; this is not proof."
    ),
    TrustVerdict.INCONCLUSIVE: (
        "Insufficient evidence, formalization, resources, or semantic support."
    ),
    TrustVerdict.REJECTED: (
        "Policy, integrity, or backend explicitly rejected the artifact."
    ),
    TrustVerdict.UNSAFE_TO_VERIFY: (
        "Intake, sandbox, dependency, or integrity requirements were not met."
    ),
    TrustVerdict.CONFLICTING_VERDICTS: (
        "Independent backends or runs produced incompatible results."
    ),
}

_LEGACY = {
    "VERIFIED": TrustVerdict.FORMALLY_CHECKED,
    "CONDITIONAL": TrustVerdict.EVIDENCE_SUPPORTED,
    "REJECTED": TrustVerdict.REJECTED,
    "UNVERIFIED": TrustVerdict.INCONCLUSIVE,
}


def from_legacy(label: str) -> TrustVerdict:
    """Map legacy trust labels onto the v8 taxonomy."""
    key = (label or "").strip().upper()
    if key in TrustVerdict.__members__:
        return TrustVerdict[key]
    if key in _LEGACY:
        return _LEGACY[key]
    raise ValueError(f"unknown trust label: {label!r}")


def may_render_as_verified(verdict: TrustVerdict) -> bool:
    """Only truth-implying verdicts may ever be summarized as verified."""
    return verdict.implies_truth
