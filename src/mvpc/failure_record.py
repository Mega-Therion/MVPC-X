"""Immutable failure records — never mutate a signed witness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from mvpc.canonical import hash_canonical


class FailureCode(str, Enum):
    ERR_HASH_DIVERGENCE = "ERR_HASH_DIVERGENCE"
    ERR_INTAKE_REJECTED = "ERR_INTAKE_REJECTED"
    ERR_SANDBOX_VIOLATION = "ERR_SANDBOX_VIOLATION"
    ERR_BACKEND_CRASH = "ERR_BACKEND_CRASH"
    ERR_TIMEOUT = "ERR_TIMEOUT"
    ERR_POLICY_VIOLATION = "ERR_POLICY_VIOLATION"
    ERR_TCB_MISMATCH = "ERR_TCB_MISMATCH"
    ERR_SIGNATURE_INVALID = "ERR_SIGNATURE_INVALID"
    ERR_FORK_DETECTED = "ERR_FORK_DETECTED"
    ERR_UNAPPROVED_AI_MAPPING = "ERR_UNAPPROVED_AI_MAPPING"
    ERR_SYSTEM_INTEGRITY = "ERR_SYSTEM_INTEGRITY"


class ContainmentScope(str, Enum):
    WORKSPACE = "WORKSPACE"
    BACKEND_PROFILE = "BACKEND_PROFILE"
    EVIDENCE_LEDGER = "EVIDENCE_LEDGER"
    GLOBAL_PUBLICATION = "GLOBAL_PUBLICATION"


@dataclass
class FailureRecord:
    failure_code: FailureCode
    message: str
    failure_id: str = field(default_factory=lambda: f"fail-{uuid4().hex[:12]}")
    affected_artifact_hashes: list[str] = field(default_factory=list)
    baseline_hash: str | None = None
    observed_hash: str | None = None
    containment_scope: ContainmentScope = ContainmentScope.WORKSPACE
    remediation_required: list[str] = field(default_factory=list)
    related_request_id: str | None = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.remediation_required:
            self.remediation_required = default_remediation(self.failure_code)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["failure_code"] = self.failure_code.value
        data["containment_scope"] = self.containment_scope.value
        return data

    def hash(self) -> str:
        return hash_canonical(self.to_dict())


def default_remediation(code: FailureCode) -> list[str]:
    mapping = {
        FailureCode.ERR_HASH_DIVERGENCE: [
            "Quarantine workspace",
            "Preserve forensic failure record",
            "Re-establish integrity baseline",
            "Do not rewrite prior witnesses",
        ],
        FailureCode.ERR_INTAKE_REJECTED: [
            "Fix path/size/symlink/syntax issues",
            "Re-run preflight",
        ],
        FailureCode.ERR_SANDBOX_VIOLATION: [
            "Inspect backend command and mounts",
            "Re-run under stricter sandbox profile",
        ],
        FailureCode.ERR_TIMEOUT: [
            "Treat as INCONCLUSIVE",
            "Increase timeout only under explicit policy",
        ],
        FailureCode.ERR_UNAPPROVED_AI_MAPPING: [
            "Route to semantic review triage",
            "Require human approval of claim mapping",
        ],
        FailureCode.ERR_FORK_DETECTED: [
            "Surface both successors",
            "Block silent ledger merge",
        ],
    }
    return list(mapping.get(code, ["Inspect failure record", "Re-run after containment"]))


@dataclass
class QuarantineState:
    scope: ContainmentScope
    active: bool = True
    reason: str = ""
    failure_ids: list[str] = field(default_factory=list)

    def blocks_publication(self) -> bool:
        return self.active and self.scope in {
            ContainmentScope.EVIDENCE_LEDGER,
            ContainmentScope.GLOBAL_PUBLICATION,
            ContainmentScope.WORKSPACE,
        }
