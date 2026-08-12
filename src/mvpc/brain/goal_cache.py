"""Cryptographic subgoal deduplication cache."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mvpc.canonical import hash_canonical


def goal_hash(hypotheses: list[str], target: str) -> str:
    return hash_canonical({"hyps": list(hypotheses), "goal": target})


@dataclass
class GoalCache:
    store: dict[str, Any] = field(default_factory=dict)

    def lookup(self, hypotheses: list[str], target: str) -> Any | None:
        return self.store.get(goal_hash(hypotheses, target))

    def store_result(self, hypotheses: list[str], target: str, result: Any) -> str:
        key = goal_hash(hypotheses, target)
        self.store[key] = result
        return key

    def __contains__(self, key: str) -> bool:
        return key in self.store
