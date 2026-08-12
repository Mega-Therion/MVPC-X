"""Portable witness bundles (.mvpcx logical layout)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from mvpc.canonical import HashBuilder, hash_canonical
from mvpc.failure_record import FailureRecord
from mvpc.policy_manifest import PolicyManifest
from mvpc.tcb import TCBDeclaration
from mvpc.traceability import TraceabilityChain
from mvpc.trust_verdicts import TrustVerdict, may_render_as_verified

BUNDLE_FORMAT_VERSION = "1.0.0"


@dataclass
class Attestation:
    attester: str
    scope: str
    statement: str
    attestation_id: str = field(default_factory=lambda: f"att-{uuid4().hex[:12]}")
    key_id: str | None = None
    signature: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def hash(self) -> str:
        return hash_canonical(self.to_dict())


@dataclass
class WitnessEntry:
    verdict: TrustVerdict
    claim_hash: str
    policy_hash: str
    tcb_hash: str
    witness_id: str = field(default_factory=lambda: f"w-{uuid4().hex[:12]}")
    formalization_hash: str | None = None
    evidence_hashes: list[str] = field(default_factory=list)
    backend_name: str | None = None
    backend_result: dict[str, Any] = field(default_factory=dict)
    backend_log_hash: str | None = None
    traceability_hash: str | None = None
    previous_witness_hash: str | None = None
    merkle_checkpoint: str | None = None
    assumptions: list[str] = field(default_factory=list)
    admitted_lemmas: list[str] = field(default_factory=list)
    timeout_seconds: int | None = None
    resource_limits: dict[str, Any] = field(default_factory=dict)
    ai_provenance: dict[str, Any] = field(default_factory=dict)
    signing_key_id: str | None = None
    signature: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["verdict"] = self.verdict.value
        return data

    def content_for_hash(self) -> dict[str, Any]:
        data = self.to_dict()
        data.pop("signature", None)
        return data

    def hash(self) -> str:
        return hash_canonical(self.content_for_hash())


@dataclass
class WitnessBundle:
    witness: WitnessEntry
    tcb: TCBDeclaration
    policy: PolicyManifest
    traceability: TraceabilityChain | None = None
    attestations: list[Attestation] = field(default_factory=list)
    failure_record: FailureRecord | None = None
    evidence_hashes: list[str] = field(default_factory=list)
    prover_log_hashes: list[str] = field(default_factory=list)
    environment_lock_hash: str | None = None
    sbom_hash: str | None = None
    format_version: str = BUNDLE_FORMAT_VERSION
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def manifest(self) -> dict[str, Any]:
        att_hashes = [a.hash() for a in self.attestations]
        return {
            "format_version": self.format_version,
            "created_at": self.created_at,
            "witness_hash": self.witness.hash(),
            "tcb_hash": self.tcb.hash(),
            "policy_hash": self.policy.hash(),
            "traceability_hash": self.traceability.hash() if self.traceability else None,
            "attestation_hashes": att_hashes,
            "failure_record_hash": self.failure_record.hash() if self.failure_record else None,
            "sbom_hash": self.sbom_hash,
            "environment_lock_hash": self.environment_lock_hash,
            "evidence_count": len(self.evidence_hashes),
            "prover_log_count": len(self.prover_log_hashes),
        }

    def manifest_hash(self) -> str:
        return hash_canonical(self.manifest())

    def composite_hash(self) -> str:
        b = HashBuilder()
        m = self.manifest()
        for key, value in m.items():
            if value is None:
                continue
            b.add_data(key, value)
        return b.digest()

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        errors.extend(self.policy.validate())
        if self.witness.policy_hash != self.policy.hash():
            errors.append("witness.policy_hash does not match policy")
        if self.witness.tcb_hash != self.tcb.hash():
            errors.append("witness.tcb_hash does not match tcb")
        if self.traceability and self.witness.traceability_hash != self.traceability.hash():
            errors.append("witness.traceability_hash does not match chain")
        if self.traceability:
            pending = self.traceability.unapproved_ai_mappings()
            if pending and self.witness.verdict.implies_truth:
                errors.append("truth-implying verdict with unapproved AI mappings")
        if may_render_as_verified(self.witness.verdict):
            if not self.witness.assumptions and self.witness.verdict == TrustVerdict.FORMALLY_CHECKED:
                pass
            if not self.tcb.limitations:
                errors.append("truth-implying verdict requires TCB limitations disclosure")
        if self.failure_record and self.witness.verdict.implies_truth:
            errors.append("failure_record present with truth-implying verdict")
        return errors

    def is_valid(self) -> bool:
        return not self.validation_errors()

    def summary(self) -> str:
        v = self.witness.verdict
        lines = [
            f"Verdict: {v.display_label()}",
            f"Description: {v.description}",
            f"Implies truth: {v.implies_truth}",
            f"Policy: {self.policy.policy_id} ({self.policy.hash()[:12]})",
            f"TCB: {self.tcb.hash()[:12]}",
            f"Manifest: {self.manifest_hash()[:12]}",
        ]
        if self.failure_record:
            lines.append(
                f"Failure: {self.failure_record.failure_code.value} "
                f"({self.failure_record.containment_scope.value})"
            )
        if not may_render_as_verified(v):
            lines.append("Note: do not render as generic VERIFIED.")
        return "\n".join(lines)
