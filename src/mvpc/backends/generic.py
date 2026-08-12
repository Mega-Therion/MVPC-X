from typing import List, Tuple
from mvpc.backends.base import VerificationBackend
from mvpc.trust import Finding, CoverageReport
from mvpc.evidence import Evidence, EvidenceType
from mvpc.hashing import hash_file
from datetime import datetime

class GenericBackend(VerificationBackend):
    def name(self) -> str:
        return "Generic"
        
    def supported_extensions(self) -> List[str]:
        return ["*"]
        
    def supports(self, path: str) -> bool:
        return True
        
    def check_native_available(self) -> bool:
        return False

    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        ev = Evidence(
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Generic file hashing",
            timestamp=datetime.utcnow().isoformat(),
            artifact_path=path,
            artifact_hash=hash_file(path)
        )
        return [], [ev]

    def run_native_verification(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        return [], []

    def audit(self, path: str) -> Tuple[List[Finding], List[Evidence], CoverageReport]:
        findings, evidence = self.run_static_analysis(path)
        
        coverage = CoverageReport(
            checks_performed=["Hash Computation"],
            checks_unavailable=["Static Analysis", "Native Verification"],
            assumptions=[],
            trust_boundaries=["Unknown file format"]
        )
        return findings, evidence, coverage
