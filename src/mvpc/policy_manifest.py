"""Declarative, hash-addressed policy manifests."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from mvpc.canonical import hash_canonical
from mvpc.trust_verdicts import TrustVerdict


class PolicyLevel(str, Enum):
    PERMISSIVE = "PERMISSIVE"
    DEFAULT = "DEFAULT"
    STRICT = "STRICT"
    CUSTOM = "CUSTOM"


@dataclass
class PolicyManifest:
    policy_id: str
    version: str
    level: PolicyLevel
    minimum_verdict: TrustVerdict
    require_human_attestation: bool = False
    require_ai_provenance_label: bool = True
    reject_on_inconclusive: bool = True
    reject_on_timeout: bool = True
    require_signed_witness: bool = True
    allowed_backends: list[str] = field(default_factory=list)
    max_timeout_seconds: int = 60
    max_memory_mb: int = 1024
    max_file_size_mb: int = 100
    max_process_count: int = 1
    network_allowed: bool = False
    signing_key_id: str | None = None
    signature: str | None = None
    description: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.policy_id.strip():
            errors.append("policy_id is required")
        if not self.version.strip():
            errors.append("version is required")
        if self.max_timeout_seconds <= 0:
            errors.append("max_timeout_seconds must be > 0")
        if self.max_memory_mb <= 0:
            errors.append("max_file_size_mb must be > 0" if False else "max_memory_mb must be > 0")
        if self.max_file_size_mb <= 0:
            errors.append("max_file_size_mb must be > 0")
        if self.max_process_count < 1:
            errors.append("max_process_count must be >= 1")
        if not self.allowed_backends:
            errors.append("allowed_backends must not be empty")
        if self.network_allowed:
            errors.append("warning: network_allowed=true weakens sandbox guarantees")
        return errors

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["level"] = self.level.value
        data["minimum_verdict"] = self.minimum_verdict.value
        return data

    def content_for_hash(self) -> dict[str, Any]:
        data = self.to_dict()
        data.pop("signature", None)
        return data

    def hash(self) -> str:
        return hash_canonical(self.content_for_hash())

    def allows_backend(self, name: str) -> bool:
        return name in self.allowed_backends

    def meets_minimum(self, verdict: TrustVerdict) -> bool:
        order = [
            TrustVerdict.UNSAFE_TO_VERIFY,
            TrustVerdict.REJECTED,
            TrustVerdict.CONFLICTING_VERDICTS,
            TrustVerdict.INCONCLUSIVE,
            TrustVerdict.HUMAN_ATTESTED,
            TrustVerdict.EVIDENCE_SUPPORTED,
            TrustVerdict.EXECUTION_OBSERVED,
            TrustVerdict.COMPUTATION_VERIFIED,
            TrustVerdict.FORMALLY_CHECKED,
        ]
        return order.index(verdict) >= order.index(self.minimum_verdict)


def template_permissive() -> PolicyManifest:
    return PolicyManifest(
        policy_id="permissive-v1",
        version="1.0.0",
        level=PolicyLevel.PERMISSIVE,
        minimum_verdict=TrustVerdict.EXECUTION_OBSERVED,
        require_human_attestation=False,
        require_signed_witness=False,
        reject_on_inconclusive=False,
        reject_on_timeout=False,
        allowed_backends=["lean", "coq", "isabelle", "python", "generic"],
        max_timeout_seconds=300,
        description="Permissive observation-oriented policy",
    )


def template_default() -> PolicyManifest:
    return PolicyManifest(
        policy_id="default-v1",
        version="1.0.0",
        level=PolicyLevel.DEFAULT,
        minimum_verdict=TrustVerdict.EVIDENCE_SUPPORTED,
        require_human_attestation=False,
        require_ai_provenance_label=True,
        require_signed_witness=True,
        allowed_backends=["lean", "coq", "isabelle", "python"],
        description="Default evidence-oriented policy",
    )


def template_strict() -> PolicyManifest:
    return PolicyManifest(
        policy_id="strict-formal-v1",
        version="1.0.0",
        level=PolicyLevel.STRICT,
        minimum_verdict=TrustVerdict.FORMALLY_CHECKED,
        require_human_attestation=True,
        require_ai_provenance_label=True,
        require_signed_witness=True,
        allowed_backends=["lean", "coq", "isabelle"],
        max_timeout_seconds=60,
        description="Strict formal verification with human attestation",
    )
