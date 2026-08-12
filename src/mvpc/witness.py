import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from mvpc.claim import Claim
from mvpc.policy import Policy
from mvpc.trust import AttestationState, Finding, CoverageReport
from mvpc.evidence import Evidence
from mvpc.hashing import hash_dict

@dataclass
class Witness:
    witness_id: str
    claim_id: str
    artifact_path: str
    artifact_hash: str
    environment: Dict[str, str]
    policy: Dict[str, Any]
    checks_performed: List[str]
    findings: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    coverage: Dict[str, Any]
    attestation_state: str
    remediation: Optional[str]
    human_review_obligations: List[str]
    timestamp: str
    witness_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def verify_integrity(self) -> bool:
        """Verify the self-hash of this witness."""
        d = self.to_dict()
        provided_hash = d.pop('witness_hash', '')
        computed_hash = hash_dict(d)
        return provided_hash == computed_hash

    def to_markdown(self) -> str:
        """Generate human-readable markdown report for this witness."""
        md = f"# Verification Witness for Claim {self.claim_id}\n\n"
        md += f"**State**: {self.attestation_state}\n"
        md += f"**Timestamp**: {self.timestamp}\n"
        md += f"**Artifact**: {self.artifact_path} (Hash: {self.artifact_hash})\n"
        md += f"\n## Findings\n"
        for finding in self.findings:
            md += f"- [{finding.get('severity', 'INFO')}] {finding.get('code')}: {finding.get('message')}\n"
        return md

def generate_witness(claim: Claim, policy: Policy, environment: Dict[str, str]) -> Witness:
    from uuid import uuid4
    
    # Extract findings and evidence dicts
    findings_dicts = [asdict(f) for f in claim.findings]
    for f in findings_dicts:
        if isinstance(f.get('severity'), Enum):
            f['severity'] = f['severity'].name
            
    evidence_dicts = [asdict(e) for e in claim.evidence]
    for e in evidence_dicts:
        if isinstance(e.get('evidence_type'), Enum):
            e['evidence_type'] = e['evidence_type'].name

    policy_dict = {
        'level': policy.level.name,
        'require_native_verification': policy.require_native_verification,
        'allow_static_only': policy.allow_static_only
    }
    
    w = Witness(
        witness_id=f"W-{uuid4().hex[:8].upper()}",
        claim_id=claim.id,
        artifact_path=claim.evidence[0].artifact_path if claim.evidence else "unknown",
        artifact_hash=claim.evidence[0].artifact_hash if claim.evidence else "unknown",
        environment=environment,
        policy=policy_dict,
        checks_performed=claim.coverage.checks_performed,
        findings=findings_dicts,
        evidence=evidence_dicts,
        coverage=asdict(claim.coverage),
        attestation_state=claim.attestation_state.name if isinstance(claim.attestation_state, Enum) else claim.attestation_state,
        remediation=next((f.remediation for f in claim.findings if f.remediation), None),
        human_review_obligations=["Review required"] if policy.require_human_signoff else [],
        timestamp=datetime.utcnow().isoformat()
    )
    
    # Compute witness hash
    d = w.to_dict()
    d.pop('witness_hash', None)
    w.witness_hash = hash_dict(d)
    return w
