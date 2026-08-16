"""Canonical binding between natural claims, formal propositions, and proofs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .canonical import canonical_json, hash_canonical


@dataclass(frozen=True)
class SemanticTest:
    test_id: str
    description: str
    expected: str
    observed: str | None = None
    passed: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "description": self.description,
            "expected": self.expected,
            "observed": self.observed,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class ClaimBinding:
    """Immutable identity chain from a claim to the checked proof target."""

    claim_id: str
    natural_statement: str
    scope: str
    definitions: Mapping[str, str] = field(default_factory=dict)
    assumptions: tuple[str, ...] = ()
    formal_language: str | None = None
    formal_statement: str | None = None
    declaration: str | None = None
    proof_artifact_hash: str | None = None
    formalization_version: str = "1"
    semantic_tests: tuple[SemanticTest, ...] = ()

    def __post_init__(self) -> None:
        if not self.claim_id.strip():
            raise ValueError("claim_id must not be empty")
        if not self.natural_statement.strip():
            raise ValueError("natural_statement must not be empty")
        if not self.scope.strip():
            raise ValueError("scope must not be empty")

    @property
    def semantic_tests_passed(self) -> bool:
        return bool(self.semantic_tests) and all(t.passed is True for t in self.semantic_tests)

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema": "mvpcx.claim-binding/v1",
            "claim_id": self.claim_id,
            "natural_statement": self.natural_statement,
            "scope": self.scope,
            "definitions": dict(self.definitions),
            "assumptions": list(self.assumptions),
            "formal_language": self.formal_language,
            "formal_statement": self.formal_statement,
            "declaration": self.declaration,
            "proof_artifact_hash": self.proof_artifact_hash,
            "formalization_version": self.formalization_version,
            "semantic_tests": [t.to_dict() for t in self.semantic_tests],
        }

    @property
    def binding_digest(self) -> str:
        return hash_canonical(self.identity_payload())

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["binding_digest"] = self.binding_digest
        return payload

    def canonical_json(self) -> str:
        return canonical_json(self.to_dict())


def bind_claim_to_formal_proof(
    *,
    claim_id: str,
    natural_statement: str,
    scope: str,
    formal_language: str,
    formal_statement: str,
    declaration: str,
    proof_artifact_hash: str,
    definitions: Mapping[str, str] | None = None,
    assumptions: list[str] | tuple[str, ...] | None = None,
    semantic_tests: list[SemanticTest] | tuple[SemanticTest, ...] | None = None,
) -> ClaimBinding:
    return ClaimBinding(
        claim_id=claim_id,
        natural_statement=natural_statement,
        scope=scope,
        definitions=definitions or {},
        assumptions=tuple(assumptions or ()),
        formal_language=formal_language,
        formal_statement=formal_statement,
        declaration=declaration,
        proof_artifact_hash=proof_artifact_hash,
        semantic_tests=tuple(semantic_tests or ()),
    )
