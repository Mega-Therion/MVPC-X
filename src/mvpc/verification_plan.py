"""Claim-centric verification plans.

A verification plan answers *which* independent mechanisms should check a
claim. It deliberately replaces the weaker model of selecting one backend
from an artifact filename.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class CheckKind(str, Enum):
    FORMAL = "formal"
    COMPUTATION = "computation"
    EXECUTION = "execution"
    PROVENANCE = "provenance"
    ENVIRONMENT = "environment"
    AXIOM_AUDIT = "axiom_audit"
    SIGNATURE = "signature"
    HUMAN_REVIEW = "human_review"


@dataclass(frozen=True)
class VerificationTarget:
    """One requested verification mechanism."""

    backend: str
    kind: CheckKind
    required: bool = False
    independent_group: str | None = None
    description: str = ""


@dataclass
class VerificationPlan:
    """Immutable-in-practice declaration of how a claim is to be checked."""

    claim_id: str
    targets: list[VerificationTarget] = field(default_factory=list)
    policy_id: str | None = None
    version: str = "1"

    def __post_init__(self) -> None:
        if not self.claim_id.strip():
            raise ValueError("claim_id must not be empty")
        self._validate_targets()

    def _validate_targets(self) -> None:
        seen: set[tuple[str, CheckKind]] = set()
        for target in self.targets:
            key = (target.backend, target.kind)
            if key in seen:
                raise ValueError(f"duplicate verification target: {key}")
            seen.add(key)

    def add(self, target: VerificationTarget) -> "VerificationPlan":
        self.targets.append(target)
        self._validate_targets()
        return self

    def required_targets(self) -> tuple[VerificationTarget, ...]:
        return tuple(t for t in self.targets if t.required)

    def formal_backends(self) -> tuple[str, ...]:
        return tuple(t.backend for t in self.targets if t.kind is CheckKind.FORMAL)

    def independent_formal_groups(self) -> frozenset[str]:
        return frozenset(
            t.independent_group
            for t in self.targets
            if t.kind is CheckKind.FORMAL and t.independent_group
        )

    def satisfies(self, completed_backends: Iterable[str]) -> bool:
        """Return whether every required target has a completed backend."""
        completed = set(completed_backends)
        return all(target.backend in completed for target in self.required_targets())
