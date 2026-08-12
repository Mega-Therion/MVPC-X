from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

class SourceType(Enum):
    HUMAN = auto()
    AI = auto()
    MACHINE = auto()
    MEASUREMENT = auto()
    DATABASE = auto()
    LITERATURE = auto()
    MIXED = auto()
    UNKNOWN = auto()

@dataclass
class AIProvenance:
    model: str
    provider: str
    prompt_hash: str
    generation_time: str
    revision_chain: List[str]
    human_edits: bool

@dataclass
class Provenance:
    source_type: SourceType
    origin_description: str
    timestamp: str
    ai_provenance: Optional[AIProvenance] = None
    metadata: Optional[Dict[str, Any]] = None
