import uuid
import json
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from mvpc.provenance import Provenance, SourceType
from mvpc.evidence import Evidence, EvidenceType
from mvpc.trust import AttestationState, Finding, CoverageReport


def generate_claim_id() -> str:
    year = datetime.now(timezone.utc).year
    return f"C-{year}-{uuid.uuid4().hex[:6].upper()}"


def _serialize_value(v: Any) -> Any:
    if isinstance(v, Enum):
        return v.name
    if isinstance(v, dict):
        return {k: _serialize_value(val) for k, val in v.items()}
    if isinstance(v, (list, tuple)):
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
        return _serialize_value(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def create_claim(statement: str, origin: SourceType, scope: str, definitions: Dict[str, str], provenance: Provenance) -> Claim:
    return Claim(
        id=generate_claim_id(), statement=statement, origin=origin, scope=scope,
        definitions=definitions, evidence=[], findings=[], assumptions=[], dependencies=[],
        provenance=provenance, attestation_state=AttestationState.UNVERIFIED,
        coverage=CoverageReport([], [], [], []), created_at=datetime.now(timezone.utc).isoformat()
    )


def _source_type(value: str | SourceType) -> SourceType:
    if isinstance(value, SourceType):
        return value
    key = str(value).strip().upper()
    try:
        return SourceType[key]
    except KeyError as exc:
        raise ValueError(f"unknown claim origin: {value!r}") from exc


def _evidence_type(value: str | EvidenceType) -> EvidenceType:
    if isinstance(value, EvidenceType):
        return value
    key = str(value).strip().upper()
    aliases = {"FORMAL": "FORMAL_PROOF", "PROOF": "FORMAL_PROOF", "COMPUTE": "COMPUTATION"}
    key = aliases.get(key, key)
    try:
        return EvidenceType[key]
    except KeyError as exc:
        raise ValueError(f"unknown evidence type: {value!r}") from exc


def load_claim_from_yaml(path: str) -> Claim:
    """Load the documented claim-manifest YAML schema into a real Claim object."""
    try:
        import yaml
    except ImportError as exc:
        raise ImportError("pyyaml is required to load claim manifests; install `pip install pyyaml`") from exc

    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    payload = data.get("claim", data)
    if not isinstance(payload, dict):
        raise ValueError("claim manifest must contain a mapping")

    statement = str(payload.get("statement", "")).strip()
    scope = str(payload.get("scope", "")).strip()
    if not statement or not scope:
        raise ValueError("claim manifest requires statement and scope")

    source = _source_type(payload.get("origin", "UNKNOWN"))
    now = datetime.now(timezone.utc).isoformat()
    provenance = Provenance(
        source_type=source,
        origin_description=str(payload.get("origin_description", f"manifest:{path}")),
        timestamp=str(payload.get("timestamp", now)),
        metadata=payload.get("metadata"),
    )

    evidence: list[Evidence] = []
    for item in payload.get("evidence", []) or []:
        if not isinstance(item, dict):
            raise ValueError("each evidence entry must be a mapping")
        evidence.append(Evidence(
            evidence_type=_evidence_type(item.get("type", "SOURCE_DOCUMENT")),
            description=str(item.get("description", "manifest evidence")),
            timestamp=str(item.get("timestamp", now)),
            artifact_path=item.get("path"),
            artifact_hash=item.get("hash"),
            content_summary=item.get("summary"),
            metadata=item.get("metadata"),
        ))

    return Claim(
        id=str(payload.get("id", generate_claim_id())),
        statement=statement,
        origin=source,
        scope=scope,
        definitions=dict(payload.get("definitions", {}) or {}),
        evidence=evidence,
        findings=[],
        assumptions=[str(v) for v in (payload.get("assumptions", []) or [])],
        dependencies=[str(v) for v in (payload.get("dependencies", []) or [])],
        provenance=provenance,
        attestation_state=AttestationState.UNVERIFIED,
        coverage=CoverageReport([], [], [], []),
        created_at=str(payload.get("created_at", now)),
        human_signoff=payload.get("human_signoff"),
    )
