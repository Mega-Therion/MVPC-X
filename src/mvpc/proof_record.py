"""End-to-end, content-addressed proof record for MVPC-X."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .assurance import AssuranceLevel, VerificationEvidence, derive_assurance
from .canonical import canonical_json, hash_canonical
from .claim_binding import ClaimBinding
from .formalization import FormalizationReview
from .verification_plan import VerificationPlan, VerificationResult


@dataclass
class ProofRecord:
    binding: ClaimBinding
    plan: VerificationPlan
    formalization: FormalizationReview | None = None
    results: list[VerificationResult] = field(default_factory=list)
    supplemental_evidence: list[VerificationEvidence] = field(default_factory=list)
    witness_id: str | None = None

    @property
    def evidence(self) -> tuple[VerificationEvidence, ...]:
        return tuple([r.to_evidence() for r in self.results] + list(self.supplemental_evidence))

    @property
    def assurance_level(self) -> AssuranceLevel:
        return derive_assurance(self.evidence)

    @property
    def record_digest(self) -> str:
        return hash_canonical(self.to_dict(include_digest=False))

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": "mvpcx.proof-record/v1",
            "binding": self.binding.to_dict(),
            "plan": self.plan.to_dict(),
            "formalization": self.formalization.to_dict() if self.formalization else None,
            "results": [
                {
                    "target_backend": r.target_backend,
                    "kind": r.kind.value,
                    "verdict": r.verdict.value,
                    "artifact_hash": r.artifact_hash,
                    "artifact_path": r.artifact_path,
                    "foundation": r.foundation,
                    "independent_group": r.independent_group,
                    "declaration": r.declaration,
                    "environment_id": r.environment_id,
                    "message": r.message,
                    "timestamp": r.timestamp,
                }
                for r in self.results
            ],
            "supplemental_evidence": [
                {
                    "source_id": e.source_id,
                    "kind": e.kind,
                    "verdict": e.verdict.value,
                    "foundation": e.foundation,
                    "environment_id": e.environment_id,
                    "artifact_hash": e.artifact_hash,
                    "declaration": e.declaration,
                    "notes": e.notes,
                }
                for e in self.supplemental_evidence
            ],
            "witness_id": self.witness_id,
            "assurance_level": int(self.assurance_level),
            "assurance_label": self.assurance_level.label,
        }
        if include_digest:
            payload["record_digest"] = hash_canonical(payload)
        return payload

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())
