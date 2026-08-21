"""Glass Box presentation contract for MVPC-X Sovereign Nexus.

The module returns serializable data and Markdown. It does not expose model
reasoning or fabricate proof traces; the left pane holds owner-provided intent
and the right pane holds source-derived normalized artifacts and real receipts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .ast_normalizer import NormalizedAst
from .backend_array import BackendReceipt
from .policy import NexusVerdict, PolicyDecision


class TrafficLight(str, Enum):
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"


@dataclass(frozen=True)
class ProofTreeNode:
    node_id: str
    label: str
    status: TrafficLight
    detail: str
    children: tuple[ProofTreeNode, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class GlassBoxDocument:
    schema_version: str
    natural_language_plan: str
    normalized_ast: dict[str, Any]
    formal_source: str
    policy: dict[str, Any]
    backend_receipt: dict[str, Any]
    final_verdict: str
    traffic_light: TrafficLight
    proof_tree: ProofTreeNode
    notices: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["traffic_light"] = self.traffic_light.value
        return data

    def to_markdown(self) -> str:
        ast_nodes = self.normalized_ast.get("nodes", [])
        declaration_lines = (
            "\n".join(
                f"- `{node.get('kind')}` `{node.get('name') or '(anonymous)'}` at line {node.get('line')}"
                for node in ast_nodes
            )
            or "- No formal declarations were recognized."
        )
        notices = "\n".join(f"- {notice}" for notice in self.notices) or "- None"
        return "\n".join(
            [
                "# MVPC-X Sovereign Nexus Glass Box",
                "",
                "## Pane 1 — Human Intent / Informal Plan",
                "",
                self.natural_language_plan or "No human plan was supplied.",
                "",
                "## Pane 2 — Normalized Formal Artifact",
                "",
                f"- **Language:** `{self.normalized_ast.get('language')}`",
                f"- **Source hash:** `{self.normalized_ast.get('source_hash')}`",
                f"- **Final verdict:** `{self.final_verdict}`",
                f"- **Traffic light:** `{self.traffic_light.value}`",
                "",
                "### Source-Derived Declarations",
                declaration_lines,
                "",
                "### Backend Receipt",
                "",
                f"- **Backend:** `{self.backend_receipt.get('backend')}`",
                f"- **Native completed:** `{self.backend_receipt.get('native_completed')}`",
                f"- **Blocking findings:** `{', '.join(self.backend_receipt.get('blockers', [])) or 'none'}`",
                "",
                "## Trust Notices",
                "",
                notices,
                "",
                "> Green means a qualifying native backend receipt completed without blocking findings. Orange means conditional or untranslated work. Red means rejected or corrupted work. CAS evidence is never presented as a substitute for native-kernel verification.",
                "",
            ]
        )


def _traffic_light(verdict: NexusVerdict, backend: BackendReceipt) -> TrafficLight:
    if verdict is NexusVerdict.FORMALLY_VERIFIED and backend.native_completed:
        return TrafficLight.GREEN
    if verdict in {NexusVerdict.REJECTED, NexusVerdict.CORRUPTED}:
        return TrafficLight.RED
    return TrafficLight.ORANGE


def build_glassbox(
    *,
    natural_language_plan: str,
    formal_source: str,
    ast: NormalizedAst,
    policy: PolicyDecision,
    backend: BackendReceipt,
    final_verdict: NexusVerdict,
) -> GlassBoxDocument:
    light = _traffic_light(final_verdict, backend)
    policy_reasons = tuple(policy.reasons)
    backend_blockers = tuple(backend.blockers)
    root = ProofTreeNode(
        node_id="claim",
        label="Claim verification",
        status=light,
        detail=final_verdict.value,
        children=(
            ProofTreeNode(
                node_id="intake",
                label="Source normalization and policy",
                status=TrafficLight.RED
                if policy.verdict is NexusVerdict.REJECTED
                else TrafficLight.ORANGE
                if policy.verdict is NexusVerdict.UNTRANSLATED
                else TrafficLight.GREEN,
                detail="; ".join(policy_reasons),
            ),
            ProofTreeNode(
                node_id="backend",
                label=backend.backend,
                status=TrafficLight.GREEN
                if backend.native_completed
                else TrafficLight.RED
                if backend_blockers
                else TrafficLight.ORANGE,
                detail=(
                    "; ".join(backend_blockers)
                    if backend_blockers
                    else "; ".join(backend.notes)
                ),
            ),
        ),
    )
    notices: list[str] = []
    if ast.translation_required:
        notices.append(
            "Source requires formal translation; normalized intake is not a proof object."
        )
    if not backend.native_completed:
        notices.append(
            "No qualifying native backend receipt is available; formal verification is not claimed."
        )
    if backend_blockers:
        notices.append("Backend blocking findings prevent a verification verdict.")
    return GlassBoxDocument(
        schema_version="mvpc.nexus.glassbox.v1",
        natural_language_plan=natural_language_plan,
        normalized_ast=ast.to_dict(),
        formal_source=formal_source,
        policy=policy.to_dict(),
        backend_receipt=backend.to_dict(),
        final_verdict=final_verdict.value,
        traffic_light=light,
        proof_tree=root,
        notices=tuple(notices),
    )
