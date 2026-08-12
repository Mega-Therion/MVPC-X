"""Local heuristic Elo-style sketch rater (not a neural rater)."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SketchRating:
    elo: float
    reasons: list[str]


def rate_sketch(sketch: str, base: float = 1200.0) -> SketchRating:
    score = base
    reasons: list[str] = []
    if "sorry" in sketch or "admit" in sketch:
        score -= 150
        reasons.append("contains sorry/admit")
    if re.search(r"\bhave\b", sketch):
        score += 40
        reasons.append("uses structured have-subgoals")
    if len(sketch.splitlines()) > 3:
        score += 20
        reasons.append("multi-step structure")
    if len(sketch) < 20:
        score -= 30
        reasons.append("very short sketch")
    if re.search(r"\b(ring|linarith|simp|omega|aesop)\b", sketch):
        score += 50
        reasons.append("uses automation tactics")
    return SketchRating(elo=score, reasons=reasons)
