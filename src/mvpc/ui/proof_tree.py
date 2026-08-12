"""Interactive proof-tree model with green/orange/red status."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from html import escape


class ProofStatus(str, Enum):
    VERIFIED = "green"
    SORRY = "orange"
    ERROR = "red"


@dataclass
class ProofNode:
    name: str
    status: ProofStatus
    detail: str = ""
    children: list["ProofNode"] = field(default_factory=list)


def export_proof_tree_markdown(root: ProofNode, indent: int = 0) -> str:
    pad = "  " * indent
    line = f"{pad}- **{root.name}** [{root.status.name}] {root.detail}".rstrip()
    parts = [line]
    for ch in root.children:
        parts.append(export_proof_tree_markdown(ch, indent + 1))
    return "\n".join(parts)


def export_proof_tree_html(root: ProofNode) -> str:
    color = {"green": "#1a7f37", "orange": "#9a6700", "red": "#cf222e"}[root.status.value]

    def render(node: ProofNode) -> str:
        kids = "".join(f"<li>{render(c)}</li>" for c in node.children)
        body = f"<ul>{kids}</ul>" if kids else ""
        return (
            f'<div style="color:{color}"><strong>{escape(node.name)}</strong> '
            f"[{node.status.name}] {escape(node.detail)}{body}</div>"
        )

    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>MVPC-X Proof Tree</title></head><body>{render(root)}</body></html>"
    )
