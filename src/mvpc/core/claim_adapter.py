"""Source-agnostic ingestion: proposer-neutral claim normalization."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from mvpc.canonical import hash_canonical, sha256_hex


class ProposerType(str, Enum):
    """Origin labels are metadata only — never affect mechanical verdict."""

    BIOLOGICAL = "biological"
    SYNTHETIC = "synthetic"
    SYMBIOTIC = "symbiotic"


class TargetBackend(str, Enum):
    LEAN4 = "lean4"
    ROCQ = "rocq"
    ISABELLE = "isabelle"
    DAFNY = "dafny"
    PYTHON = "python"
    GENERIC = "generic"


_EXT_MAP = {
    ".lean": TargetBackend.LEAN4,
    ".v": TargetBackend.ROCQ,
    ".thy": TargetBackend.ISABELLE,
    ".dfy": TargetBackend.DAFNY,
    ".py": TargetBackend.PYTHON,
}


@dataclass
class NeutralClaim:
    """Unified intake struct (gold-spec Module 1)."""

    claim_id: str
    proposer_type: ProposerType
    target_backend: TargetBackend
    header_code: str
    proof_skeleton: str = ""
    natural_language: str = ""
    source_path: str | None = None
    lexical_zones: dict[str, list[str]] = field(
        default_factory=lambda: {"evolve_block": [], "evolve_value": []}
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["proposer_type"] = self.proposer_type.value
        d["target_backend"] = self.target_backend.value
        return d

    def content_hash(self) -> str:
        payload = {
            "header_code": self.header_code,
            "proof_skeleton": self.proof_skeleton,
            "natural_language": self.natural_language,
            "target_backend": self.target_backend.value,
        }
        return hash_canonical(payload)


def _split_header_body(text: str, backend: TargetBackend) -> tuple[str, str]:
    if backend == TargetBackend.LEAN4:
        m = re.search(r"(?ms)^(theorem|lemma|example)\b.*?:=\s*by\b", text)
        if m:
            return text[: m.end()], text[m.end() :]
    if backend == TargetBackend.ROCQ:
        m = re.search(r"(?ms)^(Theorem|Lemma|Example)\b.*?\.", text)
        if m:
            return text[: m.end()], text[m.end() :]
    if backend == TargetBackend.DAFNY:
        m = re.search(r"(?ms)^(method|function|lemma)\b.*?\{", text)
        if m:
            return text[: m.end()], text[m.end() :]
    lines = text.strip().splitlines()
    if not lines:
        return "", ""
    if len(lines) == 1:
        return lines[0], ""
    return lines[0], "\n".join(lines[1:])


def adapt_claim(
    *,
    source: str | Path | None = None,
    text: str | None = None,
    proposer_type: ProposerType | str = ProposerType.BIOLOGICAL,
    target_backend: TargetBackend | str | None = None,
    natural_language: str = "",
    lexical_zones: dict[str, list[str]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> NeutralClaim:
    """Normalize any supported input into a NeutralClaim.

    Proposer type is recorded but never used to weaken or strengthen checking.
    """
    if isinstance(proposer_type, str):
        proposer_type = ProposerType(proposer_type)

    source_path = None
    body = text or ""
    if source is not None:
        path = Path(source)
        source_path = str(path)
        body = path.read_text(encoding="utf-8")
        if target_backend is None:
            target_backend = _EXT_MAP.get(path.suffix.lower(), TargetBackend.GENERIC)

    if target_backend is None:
        target_backend = TargetBackend.GENERIC
    if isinstance(target_backend, str):
        target_backend = TargetBackend(target_backend)

    if not body and natural_language:
        body = f"// informal claim pending autoformalization\n// {natural_language[:200]}"

    header, skeleton = _split_header_body(body, target_backend)
    claim_id = sha256_hex(body.encode("utf-8") if body else natural_language.encode("utf-8"))

    return NeutralClaim(
        claim_id=claim_id,
        proposer_type=proposer_type,
        target_backend=target_backend,
        header_code=header.strip() or body.strip(),
        proof_skeleton=skeleton.strip(),
        natural_language=natural_language,
        source_path=source_path,
        lexical_zones=lexical_zones
        or {"evolve_block": [], "evolve_value": []},
        metadata=metadata or {},
    )
