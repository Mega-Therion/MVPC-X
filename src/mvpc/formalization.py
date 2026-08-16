"""Formalization fidelity model for MVPC-X.

A kernel can prove the formal proposition it receives. This module makes the
natural-to-formal translation itself an auditable object.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .canonical import hash_canonical
from .claim_binding import SemanticTest


@dataclass(frozen=True)
class FormalizationReview:
    claim_id: str
    natural_statement: str
    formal_statement: str
    formal_language: str
    definitions: dict[str, str] = field(default_factory=dict)
    assumptions: tuple[str, ...] = ()
    semantic_tests: tuple[SemanticTest, ...] = ()
    divergences: tuple[str, ...] = ()
    reviewer_id: str | None = None
    reviewer_notes: str | None = None

    @property
    def tests_passed(self) -> bool:
        return bool(self.semantic_tests) and all(t.passed is True for t in self.semantic_tests)

    @property
    def materially_divergent(self) -> bool:
        return bool(self.divergences)

    @property
    def review_digest(self) -> str:
        return hash_canonical(self.to_dict(include_digest=False))

    @property
    def approved_for_formal_check(self) -> bool:
        return bool(
            self.claim_id.strip()
            and self.natural_statement.strip()
            and self.formal_statement.strip()
            and self.formal_language.strip()
            and self.tests_passed
            and not self.materially_divergent
        )

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": "mvpcx.formalization-review/v1",
            "claim_id": self.claim_id,
            "natural_statement": self.natural_statement,
            "formal_statement": self.formal_statement,
            "formal_language": self.formal_language,
            "definitions": self.definitions,
            "assumptions": list(self.assumptions),
            "semantic_tests": [t.to_dict() for t in self.semantic_tests],
            "divergences": list(self.divergences),
            "reviewer_id": self.reviewer_id,
            "reviewer_notes": self.reviewer_notes,
        }
        if include_digest:
            payload["review_digest"] = self.review_digest
        return payload


def build_formalization_review(
    *,
    claim_id: str,
    natural_statement: str,
    formal_statement: str,
    formal_language: str,
    tests: list[SemanticTest] | tuple[SemanticTest, ...],
    divergences: list[str] | tuple[str, ...] = (),
    definitions: dict[str, str] | None = None,
    assumptions: list[str] | tuple[str, ...] = (),
    reviewer_id: str | None = None,
    reviewer_notes: str | None = None,
) -> FormalizationReview:
    return FormalizationReview(
        claim_id=claim_id,
        natural_statement=natural_statement,
        formal_statement=formal_statement,
        formal_language=formal_language,
        definitions=definitions or {},
        assumptions=tuple(assumptions),
        semantic_tests=tuple(tests),
        divergences=tuple(divergences),
        reviewer_id=reviewer_id,
        reviewer_notes=reviewer_notes,
    )
