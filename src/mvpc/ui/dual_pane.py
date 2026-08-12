"""Dual-pane cognitive alignment document model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DualPaneDocument:
    title: str
    cognitive_cot: str
    formal_ast: str
    alignment_notes: list[str] = field(default_factory=list)


def export_dual_pane_markdown(doc: DualPaneDocument) -> str:
    notes = "\n".join(f"- {n}" for n in doc.alignment_notes) or "- (none)"
    return (
        f"# {doc.title}\n\n"
        f"## Pane 1 — Cognitive CoT\n\n{doc.cognitive_cot}\n\n"
        f"## Pane 2 — Formal AST / Code\n\n```\n{doc.formal_ast}\n```\n\n"
        f"## Alignment notes\n\n{notes}\n"
    )
