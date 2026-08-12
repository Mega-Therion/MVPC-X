"""Strategic planner interface. Default is a deterministic local stub."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class PlanStep:
    goal: str
    skeleton: str
    depends_on: list[str] = field(default_factory=list)


class Planner(Protocol):
    def plan(self, claim_header: str, natural_language: str = "") -> list[PlanStep]: ...


@dataclass
class LocalStubPlanner:
    def plan(self, claim_header: str, natural_language: str = "") -> list[PlanStep]:
        steps: list[PlanStep] = []
        if natural_language.strip():
            parts = [p.strip() for p in natural_language.replace(";", ".").split(".") if p.strip()]
            for i, part in enumerate(parts):
                steps.append(
                    PlanStep(
                        goal=f"subgoal_{i}: {part}",
                        skeleton=f"have h{i} : True := by sorry  -- {part}",
                        depends_on=[f"subgoal_{i-1}"] if i else [],
                    )
                )
        if not steps:
            steps.append(PlanStep(goal="main", skeleton=f"{claim_header}\n  sorry"))
        return steps


def plan_subgoals(
    claim_header: str,
    natural_language: str = "",
    planner: Planner | None = None,
) -> list[PlanStep]:
    eng = planner or LocalStubPlanner()
    return eng.plan(claim_header, natural_language)
