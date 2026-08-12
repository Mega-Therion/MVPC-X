"""Strict lexical zoning: EVOLVE-BLOCK / EVOLVE-VALUE edit boundaries."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

BEGIN_BLOCK = "EVOLVE-BLOCK-BEGIN"
END_BLOCK = "EVOLVE-BLOCK-END"
BEGIN_VALUE = "EVOLVE-VALUE-BEGIN"
END_VALUE = "EVOLVE-VALUE-END"

_ZONE_RE = re.compile(
    rf"(?P<kind>{BEGIN_BLOCK}|{BEGIN_VALUE})(?P<body>.*?)(?P<end>{END_BLOCK}|{END_VALUE})",
    re.DOTALL,
)


class LexicalZoneError(ValueError):
    pass


@dataclass
class Zone:
    kind: str
    name: str
    body: str
    start: int
    end: int


def extract_zones(source: str) -> list[Zone]:
    zones: list[Zone] = []
    for m in _ZONE_RE.finditer(source):
        begin = m.group("kind")
        end = m.group("end")
        if begin == BEGIN_BLOCK and end != END_BLOCK:
            raise LexicalZoneError("Mismatched EVOLVE-BLOCK markers")
        if begin == BEGIN_VALUE and end != END_VALUE:
            raise LexicalZoneError("Mismatched EVOLVE-VALUE markers")
        kind = "block" if begin == BEGIN_BLOCK else "value"
        body = m.group("body")
        first_line, _, rest = body.partition("\n")
        name = first_line.strip() or f"zone_{len(zones)}"
        zones.append(Zone(kind=kind, name=name, body=rest if rest else body, start=m.start(), end=m.end()))
    return zones


def validate_zones(source: str) -> None:
    extract_zones(source)
    if source.count(BEGIN_BLOCK) != source.count(END_BLOCK):
        raise LexicalZoneError("Unbalanced EVOLVE-BLOCK markers")
    if source.count(BEGIN_VALUE) != source.count(END_VALUE):
        raise LexicalZoneError("Unbalanced EVOLVE-VALUE markers")


def _frozen_skeleton(source: str) -> str:
    def repl(m: re.Match[str]) -> str:
        return f"{m.group('kind')}__ZONE__{m.group('end')}"

    return _ZONE_RE.sub(repl, source)


def apply_zoned_edit(original: str, proposed: str) -> str:
    validate_zones(original)
    validate_zones(proposed)
    if _frozen_skeleton(original) != _frozen_skeleton(proposed):
        raise LexicalZoneError(
            "Edit touches content outside EVOLVE-BLOCK / EVOLVE-VALUE zones"
        )
    return proposed


def zone_hash(source: str) -> str:
    validate_zones(source)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()
