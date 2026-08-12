"""P-UCB matchmaker for proof-search expansion."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SearchNode:
    name: str
    q_value: float
    prior: float
    visits: int
    children: list["SearchNode"] | None = None


def pucb_score(node: SearchNode, parent_visits: int, c: float = 1.25) -> float:
    return node.q_value + c * node.prior * math.sqrt(parent_visits) / (1.0 + node.visits)


def select_child(parent: SearchNode, c: float = 1.25) -> SearchNode | None:
    if not parent.children:
        return None
    return max(parent.children, key=lambda ch: pucb_score(ch, max(parent.visits, 1), c))
