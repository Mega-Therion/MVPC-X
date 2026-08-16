"""Claim-centric verification plans and result aggregation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable

from .assurance import VerificationEvidence
from .canonical import hash_canonical
from .trust_verdicts import TrustVerdict


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
    backend: str
    kind: CheckKind
    required: bool = False
    independent_group: str | None = None
    description: str = ""
    artifact_path: str | None = None
    foundation: str | None = None
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.backend.strip():
            raise ValueError("backend must not be empty")
        if self.artifact_path is not None and not self.artifact_path.strip():
            raise ValueError("artifact_path cannot be blank")


@dataclass(frozen=True)
class VerificationResult:
    target_backend: str
    kind: CheckKind
    verdict: TrustVerdict
    artifact_hash: str | None = None
    artifact_path: str | None = None
    foundation: str | None = None
    independent_group: str | None = None
    declaration: str | None = None
    environment_id: str | None = None
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_evidence(self) -> VerificationEvidence:
        return VerificationEvidence(
            source_id=f"{self.target_backend}:{self.kind.value}",
            kind=self.kind.value,
            verdict=self.verdict,
            foundation=self.foundation,
            independence_group=self.independent_group,
            environment_id=self.environment_id,
            artifact_hash=self.artifact_hash,
            declaration=self.declaration,
            notes=self.message,
        )


@dataclass
class VerificationPlan:
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
        completed = set(completed_backends)
        return all(target.backend in completed for target in self.required_targets())

    @property
    def plan_digest(self) -> str:
        return hash_canonical(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "mvpcx.verification-plan/v1",
            "claim_id": self.claim_id,
            "policy_id": self.policy_id,
            "version": self.version,
            "targets": [
                {
                    "backend": t.backend,
                    "kind": t.kind.value,
                    "required": t.required,
                    "independent_group": t.independent_group,
                    "description": t.description,
                    "artifact_path": t.artifact_path,
                    "foundation": t.foundation,
                    "options": t.options,
                }
                for t in self.targets
            ],
        }

    def evaluate(self, results: Iterable[VerificationResult]) -> dict[str, Any]:
        results = tuple(results)
        expected = {(t.backend, t.kind): t for t in self.targets}
        observed = {(r.target_backend, r.kind): r for r in results}
        missing = [
            {"backend": t.backend, "kind": t.kind.value}
            for key, t in expected.items()
            if t.required and key not in observed
        ]
        unknown = [
            {"backend": r.target_backend, "kind": r.kind.value}
            for key, r in observed.items()
            if key not in expected
        ]
        failures = [
            {"backend": r.target_backend, "kind": r.kind.value, "verdict": r.verdict.value}
            for r in results
            if r.verdict in {TrustVerdict.REJECTED, TrustVerdict.UNSAFE_TO_VERIFY}
        ]
        conflicts = [
            {"backend": r.target_backend, "kind": r.kind.value}
            for r in results
            if r.verdict is TrustVerdict.CONFLICTING_VERDICTS
        ]
        return {
            "schema": "mvpcx.verification-evaluation/v1",
            "claim_id": self.claim_id,
            "plan_digest": self.plan_digest,
            "complete": not missing and not unknown,
            "missing_required": missing,
            "unknown_results": unknown,
            "failures": failures,
            "conflicts": conflicts,
        }
