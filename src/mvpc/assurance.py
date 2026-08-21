"""Diamond Assurance derivation for MVPC-X verification evidence.

Assurance is deliberately separate from individual trust verdicts. A verdict
records what one check established; an assurance profile describes the set of
independent evidence required for a claim to reach a named level.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import IntEnum

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


@dataclass(frozen=True, init=False)
class VerificationEvidence:
    """One machine- or human-produced evidence item bound to a claim.

    The three positional fields retain compatibility with the historic
    ``VerificationEvidence(source_id, kind, verdict)`` surface. New producers
    should also pass ``claim_id`` and ``proposition``; scoped formal evidence
    then requires a non-placeholder artifact hash.
    """

    source_id: str
    kind: str
    verdict: TrustVerdict
    foundation: str | None
    independence_group: str | None
    claim_id: str
    proposition: str
    independent_from: frozenset[str]
    environment_id: str | None
    artifact_hash: str | None
    declaration: str | None
    human_review_scope: str | None
    notes: str | None

    def __init__(
        self,
        *args: object,
        source_id: str | None = None,
        kind: str | None = None,
        verdict: TrustVerdict | None = None,
        foundation: str | None = None,
        independence_group: str | None = None,
        claim_id: str = "",
        proposition: str = "",
        independent_from: frozenset[str] | Iterable[str] = frozenset(),
        environment_id: str | None = None,
        artifact_hash: str | None = None,
        declaration: str | None = None,
        human_review_scope: str | None = None,
        notes: str | None = None,
    ) -> None:
        # Compatibility surfaces:
        #   VerificationEvidence(source_id, kind, verdict)
        #   VerificationEvidence(claim_id, proposition, source_id, kind, verdict)
        # Keyword construction remains the preferred explicit form.
        if args:
            if (
                len(args) == 3
                and source_id is None
                and kind is None
                and verdict is None
            ):
                source_id, kind, verdict = args  # type: ignore[assignment]
            elif (
                len(args) == 5
                and source_id is None
                and kind is None
                and verdict is None
            ):
                claim_id, proposition, source_id, kind, verdict = args  # type: ignore[assignment]
            else:
                raise TypeError(
                    "use either 3 legacy positional fields or 5 scoped positional fields"
                )
        if (
            not isinstance(source_id, str)
            or not isinstance(kind, str)
            or not isinstance(verdict, TrustVerdict)
        ):
            raise TypeError("source_id, kind, and TrustVerdict are required")
        for field_name, value in (("source_id", source_id), ("kind", kind)):
            if not value.strip():
                raise ValueError(f"{field_name} must not be empty")
        if (
            not isinstance(claim_id, str)
            or not isinstance(proposition, str)
            or bool(claim_id) != bool(proposition)
        ):
            raise ValueError("claim_id and proposition must be provided together")
        if (
            verdict is TrustVerdict.FORMALLY_CHECKED
            and claim_id
            and (not artifact_hash or artifact_hash.lower() == "unknown")
        ):
            raise ValueError(
                "scoped formal verification evidence requires a concrete artifact_hash"
            )
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "verdict", verdict)
        object.__setattr__(self, "foundation", foundation)
        object.__setattr__(self, "independence_group", independence_group)
        object.__setattr__(self, "claim_id", claim_id)
        object.__setattr__(self, "proposition", proposition)
        object.__setattr__(self, "independent_from", frozenset(independent_from))
        object.__setattr__(self, "environment_id", environment_id)
        object.__setattr__(self, "artifact_hash", artifact_hash)
        object.__setattr__(self, "declaration", declaration)
        object.__setattr__(self, "human_review_scope", human_review_scope)
        object.__setattr__(self, "notes", notes)


def derive_assurance(evidence: Iterable[VerificationEvidence]) -> AssuranceLevel:
    """Derive the highest defensible assurance level from recorded evidence.

    Conservative rule: scoped evidence only supports its own claim,
    proposition, and non-placeholder artifact. Legacy unscoped evidence remains
    readable for compatibility but cannot silently acquire scoped identity.
    """
    items = tuple(evidence)
    if not items:
        return AssuranceLevel.D0_PROPOSED

    scoped = [item for item in items if item.claim_id]
    claim_ids = {item.claim_id for item in scoped}
    propositions = {item.proposition for item in scoped}
    artifact_hashes = {
        item.artifact_hash
        for item in scoped
        if item.artifact_hash and item.artifact_hash.lower() != "unknown"
    }
    if len(claim_ids) > 1 or len(propositions) > 1 or len(artifact_hashes) > 1:
        return AssuranceLevel.D0_PROPOSED

    verdicts = {item.verdict for item in items}
    if TrustVerdict.REJECTED in verdicts or TrustVerdict.UNSAFE_TO_VERIFY in verdicts:
        return AssuranceLevel.D0_PROPOSED

    computation = TrustVerdict.COMPUTATION_VERIFIED in verdicts
    formal_sources = [
        item for item in items if item.verdict is TrustVerdict.FORMALLY_CHECKED
    ]
    formal = bool(formal_sources)
    human_review = any(
        item.verdict is TrustVerdict.HUMAN_ATTESTED
        and (bool(item.human_review_scope) or not item.claim_id)
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
        and (
            (
                first.independence_group
                and other.independence_group
                and first.independence_group != other.independence_group
            )
            or other.source_id in first.independent_from
            or first.source_id in other.independent_from
        )
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
