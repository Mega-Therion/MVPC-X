from typing import List, Tuple
from datetime import datetime, timezone
import re

from mvpc.backends.base import VerificationBackend
from mvpc.trust import Finding, Severity, CoverageReport
from mvpc.evidence import Evidence, EvidenceType
from mvpc.hashing import hash_file
from mvpc.explanations import get_explanation

class GenericBackend(VerificationBackend):
    def name(self) -> str:
        return "Generic Artifact Hasher"
        
    def supported_extensions(self) -> List[str]:
        return ["*"]
        
    def supports(self, path: str) -> bool:
        return True
        
    def check_native_available(self) -> bool:
        return False

    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings = []
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", line):
                    exp = get_explanation("GENERIC_PLACEHOLDER")
                    findings.append(Finding(
                        code="GENERIC_PLACEHOLDER",
                        severity=Severity.WARNING,
                        message=f"Placeholder marker detected on line {i}",
                        system="GenericScanner",
                        line=i,
                        remediation=exp["action"]
                    ))
                if re.search(r"\b(sorry|admit|Admitted|oops)\b", line):
                    exp = get_explanation("GENERIC_PLACEHOLDER")
                    findings.append(Finding(
                        code="GENERIC_PLACEHOLDER",
                        severity=Severity.VIOLATION,
                        message=f"Proof-escape token detected on line {i}",
                        system="GenericScanner",
                        line=i,
                        remediation=exp["action"]
                    ))
        except Exception:
            pass

        ev = Evidence(
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Generic cryptographic file hashing",
            timestamp=datetime.now(timezone.utc).isoformat(),
            artifact_path=path,
            artifact_hash=hash_file(path)
        )
        return findings, [ev]

    def run_native_verification(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        return [], []

    def audit(self, path: str) -> Tuple[List[Finding], List[Evidence], CoverageReport]:
        findings, evidence = self.run_static_analysis(path)
        
        coverage = CoverageReport(
            checks_performed=["Cryptographic SHA-256 Hash Computation"],
            checks_unavailable=["Native Formal Verification Kernel", "Semantic AST Verification"],
            assumptions=[],
            trust_boundaries=["Unstructured / Generic file format without dedicated formal backend"]
        )
        return findings, evidence, coverage
