"""Proposer-neutral Nexus policy gates.

PANI is enforced structurally: policy evaluation accepts a normalized artifact and
mechanical observations, never the author/proposer identity. Provenance may be
preserved in a witness but is not part of the verdict material.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from mvpc.core.lexical_zones import LexicalZoneError, extract_zones, validate_zones

from .ast_normalizer import NormalizedAst


class NexusVerdict(str, Enum):
    FORMALLY_VERIFIED = "FORMALLY_VERIFIED"
    CONDITIONAL = "CONDITIONAL"
    REJECTED = "REJECTED"
    UNTRANSLATED = "UNTRANSLATED"
    CORRUPTED = "CORRUPTED"


@dataclass(frozen=True)
class PolicyDecision:
    verdict: NexusVerdict
    reasons: tuple[str, ...]
    zero_axiom_clean: bool
    lexical_zones: tuple[dict[str, Any], ...]
    source_hash: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["verdict"] = self.verdict.value
        return value


def evaluate_source_policy(ast: NormalizedAst, source: str) -> PolicyDecision:
    """Evaluate source-only gates before any external backend is invoked."""
    reasons: list[str] = []
    zones: tuple[dict[str, Any], ...] = ()
    try:
        validate_zones(source)
        zones = tuple(
            {"kind": zone.kind, "name": zone.name, "start": zone.start, "end": zone.end}
            for zone in extract_zones(source)
        )
    except LexicalZoneError as exc:
        reasons.append(f"Lexical-zone violation: {exc}")

    if not ast.delimiter_balanced:
        reasons.append("Structural intake rejected: source delimiters are unbalanced.")
    if ast.forbidden_markers:
        reasons.append(
            "Zero-axiom intake audit rejected markers: "
            + ", ".join(ast.forbidden_markers)
        )
    if reasons:
        return PolicyDecision(
            verdict=NexusVerdict.REJECTED,
            reasons=tuple(reasons),
            zero_axiom_clean=False,
            lexical_zones=zones,
            source_hash=ast.source_hash,
        )
    if ast.translation_required:
        return PolicyDecision(
            verdict=NexusVerdict.UNTRANSLATED,
            reasons=(
                "Informal or unrecognized source was normalized, but no formal proof artifact was supplied.",
            ),
            zero_axiom_clean=True,
            lexical_zones=zones,
            source_hash=ast.source_hash,
        )
    if not ast.nodes:
        return PolicyDecision(
            verdict=NexusVerdict.REJECTED,
            reasons=(
                "Formal source contains no recognized declarations for its language.",
            ),
            zero_axiom_clean=True,
            lexical_zones=zones,
            source_hash=ast.source_hash,
        )
    return PolicyDecision(
        verdict=NexusVerdict.CONDITIONAL,
        reasons=(
            "Structural policy passed; a qualifying native backend receipt is still required.",
        ),
        zero_axiom_clean=True,
        lexical_zones=zones,
        source_hash=ast.source_hash,
    )


def derive_native_verdict(
    policy: PolicyDecision,
    *,
    native_completed: bool,
    backend_blockers: Iterable[str],
    integrity_intact: bool,
) -> NexusVerdict:
    """Derive the final verdict without considering proposer identity."""
    if not integrity_intact:
        return NexusVerdict.CORRUPTED
    if policy.verdict in {NexusVerdict.REJECTED, NexusVerdict.UNTRANSLATED}:
        return policy.verdict
    if tuple(backend_blockers):
        return NexusVerdict.REJECTED
    if native_completed and policy.zero_axiom_clean:
        return NexusVerdict.FORMALLY_VERIFIED
    return NexusVerdict.CONDITIONAL
