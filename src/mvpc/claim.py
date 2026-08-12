import uuid
import json
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from mvpc.provenance import Provenance, SourceType
from mvpc.evidence import Evidence, EvidenceType
from mvpc.trust import AttestationState, Finding, CoverageReport, Severity

def generate_claim_id() -> str:
    """Generate an auto-generated claim id in format C-YYYY-NNNNNN."""
    year = datetime.now(timezone.utc).year
    hex_id = uuid.uuid4().hex[:6].upper()
    return f"C-{year}-{hex_id}"

def _serialize_value(v: Any) -> Any:
    """Recursively serialize enum values in nested structures."""
    if isinstance(v, Enum):
        return v.name
    if isinstance(v, dict):
        return {k: _serialize_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_serialize_value(item) for item in v]
    return v

@dataclass
class Claim:
    id: str
    statement: str
    origin: SourceType
    scope: str
    definitions: Dict[str, str]
    evidence: List[Evidence]
    findings: List[Finding]
    assumptions: List[str]
    dependencies: List[str]
    provenance: Provenance
    attestation_state: AttestationState
    coverage: CoverageReport
    created_at: str
    human_signoff: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Claim to dictionary with all enums converted to strings."""
        d = asdict(self)
        return _serialize_value(d)

    def to_json(self) -> str:
        """Serialize Claim to JSON."""
        return json.dumps(self.to_dict(), indent=2)

def create_claim(statement: str, origin: SourceType, scope: str, definitions: Dict[str, str],
                 provenance: Provenance) -> Claim:
    """Factory function for creating a new Claim."""
    return Claim(
        id=generate_claim_id(),
        statement=statement,
        origin=origin,
        scope=scope,
        definitions=definitions,
        evidence=[],
        findings=[],
        assumptions=[],
        dependencies=[],
        provenance=provenance,
        attestation_state=AttestationState.UNVERIFIED,
        coverage=CoverageReport([], [], [], []),
        created_at=datetime.now(timezone.utc).isoformat()
    )

def load_claim_from_yaml(path: str) -> Claim:
    """Load a claim manifest from a YAML file (gracefully fallback if pyyaml is missing)."""
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # Conversion logic would be here
            raise NotImplementedError("Claim YAML parsing logic incomplete")
    except ImportError:
        raise ImportError("pyyaml is required to load claim manifests from YAML files")
