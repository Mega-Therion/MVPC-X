"""Claim-centric assurance model for MVPC-X.

Assurance is deliberately separate from individual trust verdicts. A verdict
records what one check established; an assurance profile describes the set of
independent evidence required for a claim to reach a named level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import FrozenSet, Iterable

from .trust_verdicts import TrustVerdict


class AssuranceLevel(IntEnum):
    """Monotonic MVPC-X Diamond Assurance levels D0 through D6."""

    D0_PROPOSED = 0
    D1_REPRODUCIBLY_COMPUTED = 1
    D2_FORMALLY_CHECKED = 2
    D3_HARDENED_FORMAL = 3
    D4_INDEPENDENTLY_RECHECKED = 4
    D5_CROSS_FOUNDATION = 5
    D6_PUBLICATION_GRADE = 6

    @property
    def label(self) -> str:
        return self.name[3:].replace("_", " ")


@dataclass(frozen=True)
class VerificationEvidence:
    """One machine- or human-produced evidence item bound to a claim.

    A claim cannot climb past D1 unless the evidence names the proposition and
    artifact it verifies. Independence is recorded, never inferred from prose.
    """

    claim_id: str
    proposition: str
    source_id: str
    kind: str
    verdict: TrustVerdict
    foundation: str | None = None
    independent_from: FrozenSet[str] = field(default_factory=frozenset)
    environment_id: str | None = None
    artifact_hash: str | None = None
    declaration: str | None = None
    human_review_scope: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("claim_id", "proposition", "source_id", "kind"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        if self.verdict is TrustVerdict.FORMALLY_CHECKED and not self.artifact_hash:
            raise ValueError("formal verification evidence requires artifact_hash")


def derive_assurance(evidence: Iterable[VerificationEvidence]) -> AssuranceLevel:
    """Derive the highest defensible assurance level from recorded evidence.

    Conservative rule: evidence only supports its own claim/proposition/artifact.
    Model agreement, unrelated compilation, and unscoped human attestation do not
    upgrade assurance.
    """
    items = tuple(evidence)
    if not items:
        return AssuranceLevel.D0_PROPOSED

    claim_ids = {item.claim_id for item in items}
    propositions = {item.proposition for item in items}
    artifact_hashes = {item.artifact_hash for item in items if item.artifact_hash}
    if len(claim_ids) > 1 or len(propositions) > 1 or len(artifact_hashes) > 1:
        return AssuranceLevel.D0_PROPOSED

    verdicts = {item.verdict for item in items}
    if TrustVerdict.REJECTED in verdicts or TrustVerdict.UNSAFE_TO_VERIFY in verdicts:
        return AssuranceLevel.D0_PROPOSED

    computation = TrustVerdict.COMPUTATION_VERIFIED in verdicts
    formal_sources = [item for item in items if item.verdict == TrustVerdict.FORMALLY_CHECKED]
    formal = bool(formal_sources)
    human_review = any(
        item.verdict is TrustVerdict.HUMAN_ATTESTED and item.human_review_scope
        for item in items
    )

    if formal:
        level = AssuranceLevel.D2_FORMALLY_CHECKED
    elif computation:
        level = AssuranceLevel.D1_REPRODUCIBLY_COMPUTED
    else:
        return AssuranceLevel.D0_PROPOSED

    hardened_kinds = {"signature", "environment", "axiom_audit", "provenance"}
    present_kinds = {item.kind for item in items}
    if hardened_kinds.issubset(present_kinds):
        level = AssuranceLevel.D3_HARDENED_FORMAL

    independent = any(
        other.source_id != first.source_id
        and (other.source_id in first.independent_from or first.source_id in other.independent_from)
        for index, first in enumerate(formal_sources)
        for other in formal_sources[index + 1 :]
    )
    if level >= AssuranceLevel.D3_HARDENED_FORMAL and independent:
        level = AssuranceLevel.D4_INDEPENDENTLY_RECHECKED

    foundations = {item.foundation for item in formal_sources if item.foundation}
    if level >= AssuranceLevel.D4_INDEPENDENTLY_RECHECKED and len(foundations) >= 2:
        level = AssuranceLevel.D5_CROSS_FOUNDATION

    if level >= AssuranceLevel.D5_CROSS_FOUNDATION and human_review:
        level = AssuranceLevel.D6_PUBLICATION_GRADE

    return level
