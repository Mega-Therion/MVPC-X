"""Tactical solver interface (parallel provers plug in here)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mvpc.brain.elo_rating import rate_sketch
from mvpc.brain.goal_cache import GoalCache


@dataclass
class SolverResult:
    success: bool
    tactic: str
    elo: float
    cached: bool = False
    notes: str = ""


class TacticSolver(Protocol):
    def solve(self, goal: str, hypotheses: list[str]) -> SolverResult: ...


@dataclass
class LocalStubSolver:
    def solve(self, goal: str, hypotheses: list[str]) -> SolverResult:
        sketch = "simp" if "=" in goal else "trivial"
        rating = rate_sketch(sketch)
        return SolverResult(
            success=False,
            tactic=sketch,
            elo=rating.elo,
            notes="local stub — requires real prover/neural solver for success",
        )


def try_solve_subgoal(
    goal: str,
    hypotheses: list[str] | None = None,
    *,
    cache: GoalCache | None = None,
    solver: TacticSolver | None = None,
) -> SolverResult:
    hyps = hypotheses or []
    cache = cache or GoalCache()
    hit = cache.lookup(hyps, goal)
    if hit is not None and isinstance(hit, SolverResult):
        hit.cached = True
        return hit
    eng = solver or LocalStubSolver()
    result = eng.solve(goal, hyps)
    cache.store_result(hyps, goal, result)
    return result
