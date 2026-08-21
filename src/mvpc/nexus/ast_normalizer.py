"""Source-agnostic structural normalization for Sovereign Nexus intake.

This module deliberately performs deterministic parsing and structural extraction,
not probabilistic translation. Informal and LaTeX inputs can be normalized and
tracked, but cannot become formal proofs without an independently supplied
formal-language artifact accepted by a native kernel.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class SourceLanguage(str, Enum):
    LEAN = "lean"
    ROCQ = "rocq"
    ISABELLE = "isabelle"
    DAFNY = "dafny"
    LATEX = "latex"
    NATURAL_LANGUAGE = "natural_language"
    UNKNOWN = "unknown"


_EXTENSION_LANGUAGE = {
    ".lean": SourceLanguage.LEAN,
    ".v": SourceLanguage.ROCQ,
    ".thy": SourceLanguage.ISABELLE,
    ".dfy": SourceLanguage.DAFNY,
    ".tex": SourceLanguage.LATEX,
    ".latex": SourceLanguage.LATEX,
    ".md": SourceLanguage.NATURAL_LANGUAGE,
    ".txt": SourceLanguage.NATURAL_LANGUAGE,
}

_DECLARATION_PATTERNS: dict[SourceLanguage, re.Pattern[str]] = {
    SourceLanguage.LEAN: re.compile(
        r"(?m)^\s*(?:protected\s+|private\s+)?(?:theorem|lemma|def|example)\s+([\w'!?]+)"
    ),
    SourceLanguage.ROCQ: re.compile(
        r"(?m)^\s*(?:Theorem|Lemma|Definition|Fixpoint|Corollary)\s+([\w']+)"
    ),
    SourceLanguage.ISABELLE: re.compile(
        r"(?m)^\s*(?:lemma|theorem|definition|corollary)\s+([\w'.-]+)"
    ),
    SourceLanguage.DAFNY: re.compile(
        r"(?m)^\s*(?:lemma|method|function|predicate)\s+([\w_]+)"
    ),
}

_FORBIDDEN_MARKERS: dict[SourceLanguage, tuple[str, ...]] = {
    SourceLanguage.LEAN: ("sorry", "admit", "sorryAx", "axiom "),
    SourceLanguage.ROCQ: ("Admitted", "admit", "Axiom "),
    SourceLanguage.ISABELLE: ("sorry", "oops", "axiomatization"),
    SourceLanguage.DAFNY: ("assume false", "assume("),
}


@dataclass(frozen=True)
class AstNode:
    """A canonical, source-derived structural node.

    ``kind`` is descriptive only. It is not a theorem-prover AST and must not be
    treated as a proof object.
    """

    kind: str
    name: str | None
    line: int
    source_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NormalizedAst:
    schema_version: str
    language: SourceLanguage
    source_path: str | None
    source_hash: str
    byte_length: int
    nodes: tuple[AstNode, ...]
    delimiter_balanced: bool
    forbidden_markers: tuple[str, ...]
    translation_required: bool
    parse_notes: tuple[str, ...]

    @property
    def is_formal_source(self) -> bool:
        return self.language in {
            SourceLanguage.LEAN,
            SourceLanguage.ROCQ,
            SourceLanguage.ISABELLE,
            SourceLanguage.DAFNY,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "language": self.language.value,
            "source_path": self.source_path,
            "source_hash": self.source_hash,
            "byte_length": self.byte_length,
            "nodes": [node.to_dict() for node in self.nodes],
            "delimiter_balanced": self.delimiter_balanced,
            "forbidden_markers": list(self.forbidden_markers),
            "translation_required": self.translation_required,
            "parse_notes": list(self.parse_notes),
        }


def detect_language(path: str | Path | None, source: str) -> SourceLanguage:
    if path:
        suffix = Path(path).suffix.lower()
        if suffix in _EXTENSION_LANGUAGE:
            return _EXTENSION_LANGUAGE[suffix]
    lowered = source.lower()
    if (
        re.search(r"(?m)^\s*(?:theorem|lemma|def)\s+", source)
        or "import mathlib" in lowered
    ):
        return SourceLanguage.LEAN
    if (
        re.search(r"(?m)^\s*(?:theorem|lemma|definition)\s+", source)
        and "qed." in lowered
    ):
        return SourceLanguage.ROCQ
    if re.search(r"(?m)^\s*theory\s+", source) or "isabelle" in lowered:
        return SourceLanguage.ISABELLE
    if (
        re.search(r"(?m)^\s*(?:method|function|lemma)\s+", source)
        and "ensures" in lowered
    ):
        return SourceLanguage.DAFNY
    if "\\begin{" in source or "\\[" in source or "\\frac" in source:
        return SourceLanguage.LATEX
    return SourceLanguage.NATURAL_LANGUAGE if source.strip() else SourceLanguage.UNKNOWN


def _balanced_delimiters(source: str) -> bool:
    matching = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for char in source:
        if char in "([{":
            stack.append(char)
        elif char in matching and (not stack or stack.pop() != matching[char]):
            return False
    return not stack


def _line_at(source: str, index: int) -> int:
    return source[:index].count("\n") + 1


def normalize_source(source: str, *, path: str | Path | None = None) -> NormalizedAst:
    """Return a canonical structural representation without executing source."""
    language = detect_language(path, source)
    source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
    nodes: list[AstNode] = []
    notes: list[str] = []
    pattern = _DECLARATION_PATTERNS.get(language)
    if pattern:
        for match in pattern.finditer(source):
            nodes.append(
                AstNode(
                    kind="declaration",
                    name=match.group(1),
                    line=_line_at(source, match.start()),
                    source_hash=source_hash,
                )
            )
    elif language == SourceLanguage.LATEX:
        notes.append(
            "LaTeX normalized as an informal mathematical source; formal translation is required."
        )
    elif language == SourceLanguage.NATURAL_LANGUAGE:
        notes.append(
            "Natural-language source normalized as a proposal; formal translation is required."
        )
    else:
        notes.append(
            "No recognized formal declaration grammar was available for this source."
        )

    if not _balanced_delimiters(source):
        notes.append("Unbalanced delimiters detected during structural normalization.")
    if not nodes and language in _DECLARATION_PATTERNS:
        notes.append(
            "No recognized declarations found for the declared formal language."
        )

    markers = tuple(
        marker
        for marker in _FORBIDDEN_MARKERS.get(language, ())
        if marker.lower() in source.lower()
    )
    if markers:
        notes.append(
            "Potential unsound or placeholder marker detected; policy or backend review is required."
        )

    return NormalizedAst(
        schema_version="mvpc.nexus.ast.v1",
        language=language,
        source_path=str(Path(path).resolve()) if path else None,
        source_hash=source_hash,
        byte_length=len(source.encode("utf-8")),
        nodes=tuple(nodes),
        delimiter_balanced=_balanced_delimiters(source),
        forbidden_markers=markers,
        translation_required=language
        in {
            SourceLanguage.LATEX,
            SourceLanguage.NATURAL_LANGUAGE,
            SourceLanguage.UNKNOWN,
        },
        parse_notes=tuple(notes),
    )


def normalize_file(path: str | Path) -> NormalizedAst:
    resolved = Path(path).resolve(strict=True)
    return normalize_source(
        resolved.read_text(encoding="utf-8", errors="replace"), path=resolved
    )
