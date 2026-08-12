"""Claim-to-formalization traceability matrix."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from mvpc.canonical import hash_canonical


class ArtifactKind(str, Enum):
    NATURAL_LANGUAGE_CLAIM = "NATURAL_LANGUAGE_CLAIM"
    STRUCTURED_CLAIM = "STRUCTURED_CLAIM"
    FORMAL_STATEMENT = "FORMAL_STATEMENT"
    PROOF_OR_CHECKER_RESULT = "PROOF_OR_CHECKER_RESULT"
    WITNESS = "WITNESS"


class ProvenanceLabel(str, Enum):
    HUMAN = "HUMAN"
    AI_PROPOSED = "AI_PROPOSED"
    MACHINE_DERIVED = "MACHINE_DERIVED"


@dataclass
class TraceLink:
    artifact_id: str
    kind: ArtifactKind
    content_hash: str
    provenance: ProvenanceLabel
    human_approved: bool = False
    approver: str | None = None
    approval_scope: str | None = None
    approved_at: str | None = None
    notes: str = ""

    def requires_human_gate(self) -> bool:
        return self.kind in {
            ArtifactKind.STRUCTURED_CLAIM,
            ArtifactKind.FORMAL_STATEMENT,
        } and self.provenance == ProvenanceLabel.AI_PROPOSED


@dataclass
class TraceabilityChain:
    chain_id: str = field(default_factory=lambda: f"tr-{uuid4().hex[:12]}")
    links: list[TraceLink] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def add(self, link: TraceLink) -> None:
        self.links.append(link)

    def unapproved_ai_mappings(self) -> list[TraceLink]:
        return [link for link in self.links if link.requires_human_gate() and not link.human_approved]

    def is_complete_for_formal(self) -> bool:
        kinds = {link.kind for link in self.links}
        needed = {
            ArtifactKind.NATURAL_LANGUAGE_CLAIM,
            ArtifactKind.STRUCTURED_CLAIM,
            ArtifactKind.FORMAL_STATEMENT,
            ArtifactKind.PROOF_OR_CHECKER_RESULT,
        }
        return needed.issubset(kinds) and not self.unapproved_ai_mappings()

    def approve(self, artifact_id: str, approver: str, scope: str) -> None:
        for link in self.links:
            if link.artifact_id == artifact_id:
                link.human_approved = True
                link.approver = approver
                link.approval_scope = scope
                link.approved_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                return
        raise KeyError(artifact_id)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for item in payload["links"]:
            item["kind"] = item["kind"] if isinstance(item["kind"], str) else item["kind"]
            item["provenance"] = (
                item["provenance"] if isinstance(item["provenance"], str) else item["provenance"]
            )
        return payload

    def hash(self) -> str:
        return hash_canonical(self.to_dict())

    def render_table(self) -> str:
        lines = [
            "| ID | Kind | Provenance | Human approved | Scope |",
            "|---|---|---|---|---|",
        ]
        for link in self.links:
            lines.append(
                f"| {link.artifact_id} | {link.kind.value} | {link.provenance.value} | "
                f"{link.human_approved} | {link.approval_scope or ''} |"
            )
        return "\n".join(lines)
