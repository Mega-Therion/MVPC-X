"""Claim-centric assurance model for MVPC-X."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import FrozenSet, Iterable

from .trust_verdicts import TrustVerdict


class AssuranceLevel(IntEnum):
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
    """One machine- or human-produced evidence item bound to a claim."""

    source_id: str
    kind: str
    verdict: TrustVerdict
    foundation: str | None = None
    independent_from: FrozenSet[str] = field(default_factory=frozenset)
    environment_id: str | None = None
    artifact_hash: str | None = None
    declaration: str | None = None
    notes: str | None = None
    independence_group: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.kind.strip():
            raise ValueError("kind must not be empty")


def derive_assurance(evidence: Iterable[VerificationEvidence]) -> AssuranceLevel:
    """Return the highest level justified by explicit evidence only."""
    items = tuple(evidence)
    verdicts = {item.verdict for item in items}
    if TrustVerdict.REJECTED in verdicts or TrustVerdict.UNSAFE_TO_VERIFY in verdicts:
        return AssuranceLevel.D0_PROPOSED
    if not items:
        return AssuranceLevel.D0_PROPOSED

    formal_items = [item for item in items if item.verdict is TrustVerdict.FORMALLY_CHECKED]
    computation = TrustVerdict.COMPUTATION_VERIFIED in verdicts
    if not formal_items:
        return AssuranceLevel.D1_REPRODUCIBLY_COMPUTED if computation else AssuranceLevel.D0_PROPOSED

    level = AssuranceLevel.D2_FORMALLY_CHECKED
    hardened_kinds = {"signature", "environment", "axiom_audit", "provenance"}
    if hardened_kinds.issubset({item.kind for item in items}):
        level = AssuranceLevel.D3_HARDENED_FORMAL

    formal_sources = {item.source_id for item in formal_items}
    formal_groups = {
        item.independence_group
        for item in formal_items
        if item.independence_group is not None
    }
    explicit_pair = any(
        other.source_id in first.independent_from or first.source_id in other.independent_from
        for index, first in enumerate(formal_items)
        for other in formal_items[index + 1 :]
    )
    independent = len(formal_sources) >= 2 and (len(formal_groups) >= 2 or explicit_pair)
    if level >= AssuranceLevel.D3_HARDENED_FORMAL and independent:
        level = AssuranceLevel.D4_INDEPENDENTLY_RECHECKED

    foundations = {item.foundation for item in formal_items if item.foundation}
    if level >= AssuranceLevel.D4_INDEPENDENTLY_RECHECKED and len(foundations) >= 2:
        level = AssuranceLevel.D5_CROSS_FOUNDATION

    human = TrustVerdict.HUMAN_ATTESTED in verdicts
    if level >= AssuranceLevel.D5_CROSS_FOUNDATION and human:
        level = AssuranceLevel.D6_PUBLICATION_GRADE
    return level
