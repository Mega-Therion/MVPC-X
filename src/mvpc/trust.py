"""Compatibility trust structures backed by the canonical MVPC-X taxonomy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .trust_verdicts import TrustVerdict, from_legacy


class AttestationState(Enum):
    """Legacy compatibility enum.

    New code should use :class:`TrustVerdict` directly. The old names remain
    import-compatible while no longer defining a competing trust taxonomy.
    """

    VERIFIED = TrustVerdict.FORMALLY_CHECKED.value
    CONDITIONAL = TrustVerdict.EVIDENCE_SUPPORTED.value
    REJECTED = TrustVerdict.REJECTED.value
    UNVERIFIED = TrustVerdict.INCONCLUSIVE.value

    @classmethod
    def from_label(cls, label: str) -> "AttestationState":
        return cls(from_legacy(label).value)

    @property
    def verdict(self) -> TrustVerdict:
        return TrustVerdict(self.value)


class Severity(Enum):
    VIOLATION = "VIOLATION"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Finding:
    code: str
    severity: Severity
    message: str
    system: str
    line: Optional[int] = None
    remediation: Optional[str] = None


@dataclass
class CoverageReport:
    checks_performed: List[str]
    checks_unavailable: List[str]
    assumptions: List[str]
    trust_boundaries: List[str]
