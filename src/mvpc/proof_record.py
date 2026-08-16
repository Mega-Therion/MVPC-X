"""End-to-end, content-addressed proof record for MVPC-X."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .assurance import AssuranceLevel, VerificationEvidence, derive_assurance
from .canonical import canonical_json, hash_canonical
from .claim_binding import ClaimBinding
from .formalization import FormalizationReview
from .trust_verdicts import TrustVerdict
from .verification_plan import CheckKind, VerificationPlan, VerificationResult


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
        if not self.bindings_valid:
            return AssuranceLevel.D0_PROPOSED
        return derive_assurance(self.evidence)

    @property
    def bindings_valid(self) -> bool:
        if self.binding.claim_id != self.plan.claim_id:
            return False
        if self.formalization is not None and self.formalization.claim_id != self.binding.claim_id:
            return False
        formal_results = [r for r in self.results if r.kind is CheckKind.FORMAL and r.verdict is TrustVerdict.FORMALLY_CHECKED]
        if not formal_results:
            return True
        if not self.binding.formal_statement or not self.binding.declaration or not self.binding.proof_artifact_hash:
            return False
        if self.formalization is not None and not self.formalization.approved_for_formal_check:
            return False
        return all(
            r.declaration == self.binding.declaration
            and r.artifact_hash == self.binding.proof_artifact_hash
            for r in formal_results
        )

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        if self.binding.claim_id != self.plan.claim_id:
            errors.append("claim_id mismatch between binding and verification plan")
        if self.formalization is not None and self.formalization.claim_id != self.binding.claim_id:
            errors.append("claim_id mismatch between binding and formalization review")
        for result in self.results:
            if result.kind is CheckKind.FORMAL and result.verdict is TrustVerdict.FORMALLY_CHECKED:
                if result.artifact_hash != self.binding.proof_artifact_hash:
                    errors.append(f"formal artifact hash mismatch for {result.target_backend}")
                if result.declaration != self.binding.declaration:
                    errors.append(f"formal declaration mismatch for {result.target_backend}")
        if self.formalization is not None and not self.formalization.approved_for_formal_check:
            errors.append("formalization review is not approved for formal checking")
        if any(r.kind is CheckKind.FORMAL and r.verdict is TrustVerdict.FORMALLY_CHECKED for r in self.results):
            if not self.binding.formal_statement or not self.binding.declaration or not self.binding.proof_artifact_hash:
                errors.append("formal result lacks complete binding identity")
        return errors

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
                    "independence_group": e.independence_group,
                    "environment_id": e.environment_id,
                    "artifact_hash": e.artifact_hash,
                    "declaration": e.declaration,
                    "notes": e.notes,
                }
                for e in self.supplemental_evidence
            ],
            "witness_id": self.witness_id,
            "bindings_valid": self.bindings_valid,
            "validation_errors": self.validation_errors(),
            "assurance_level": int(self.assurance_level),
            "assurance_label": self.assurance_level.label,
        }
        if include_digest:
            payload["record_digest"] = hash_canonical(payload)
        return payload

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())
