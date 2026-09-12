"""Shared result types for external artifact verification.

GateStatus is intentionally distinct from mvpc.trust_verdicts.TrustVerdict:
TrustVerdict describes MVPC-X's own atomic verification outcomes for
claims it verifies directly (Lean/backend runs). GateStatus describes the
narrower question this package asks of a *declared* upstream field: did
this specific checkable property hold, fail, go unchecked, or not apply.
Never treat GateStatus.UNAVAILABLE as GateStatus.PASSED (rule 5 in the
issue: unknown/unavailable/missing data must not be treated as passed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GateStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"


# Aggregation order: the overall verdict is the "worst" gate status present,
# with FAILED dominating everything, then UNAVAILABLE, then NOT_APPLICABLE,
# and only PASSED if every gate passed or was legitimately not applicable.
_SEVERITY = {
    GateStatus.FAILED: 3,
    GateStatus.UNAVAILABLE: 2,
    GateStatus.NOT_APPLICABLE: 1,
    GateStatus.PASSED: 0,
}


@dataclass
class Gate:
    name: str
    status: GateStatus
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status.value, "detail": self.detail}


def overall_verdict(gates: list[Gate]) -> GateStatus:
    """Fail-closed aggregation: any failed gate fails the artifact; any
    unavailable *required* gate is surfaced as unavailable rather than
    silently passing. NOT_APPLICABLE gates never contribute a pass on
    their own — an artifact whose gates are entirely not_applicable is
    reported not_applicable, never passed, since nothing was actually
    checked."""
    if not gates:
        return GateStatus.UNAVAILABLE
    worst = max(gates, key=lambda g: _SEVERITY[g.status])
    if worst.status in (GateStatus.FAILED, GateStatus.UNAVAILABLE):
        return worst.status
    if all(g.status == GateStatus.NOT_APPLICABLE for g in gates):
        return GateStatus.NOT_APPLICABLE
    return GateStatus.PASSED


@dataclass
class ArtifactVerificationResult:
    """The full deterministic, machine-readable verification record
    described in issue #8 Phase 5."""

    verifier_name: str
    verifier_version: str
    artifact_type: str
    schema_id: str
    schema_version: str
    source_path: str
    canonical_hash: str
    provenance: dict[str, Any]
    gates: list[Gate]
    policy_version: str
    verdict: GateStatus = field(init=False)

    def __post_init__(self) -> None:
        self.verdict = overall_verdict(self.gates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verifier": {"name": self.verifier_name, "version": self.verifier_version},
            "artifact": {
                "type": self.artifact_type,
                "schema_id": self.schema_id,
                "schema_version": self.schema_version,
                "source_path": self.source_path,
                "canonical_hash": self.canonical_hash,
                "provenance": self.provenance,
            },
            "gates": [g.to_dict() for g in self.gates],
            "verdict": self.verdict.value,
            "policy_version": self.policy_version,
        }
