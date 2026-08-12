from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional

class AttestationState(Enum):
    VERIFIED = auto()
    CONDITIONAL = auto()
    REJECTED = auto()
    UNVERIFIED = auto()

class Severity(Enum):
    VIOLATION = auto()
    WARNING = auto()
    INFO = auto()

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
