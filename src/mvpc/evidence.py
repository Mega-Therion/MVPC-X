from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Dict, Any

class EvidenceType(Enum):
    FORMAL_PROOF = auto()
    COMPUTATION = auto()
    STATIC_ANALYSIS = auto()
    NATIVE_VERIFICATION = auto()
    STATISTICAL_TEST = auto()
    DATA_INTEGRITY = auto()
    REPRODUCTION = auto()
    SOURCE_DOCUMENT = auto()
    EXPERT_REVIEW = auto()

@dataclass
class Evidence:
    evidence_type: EvidenceType
    description: str
    timestamp: str
    artifact_path: Optional[str] = None
    artifact_hash: Optional[str] = None
    content_summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
