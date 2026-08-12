import os
import subprocess
from typing import List, Tuple
from mvpc.backends.base import VerificationBackend
from mvpc.trust import Finding, Severity, CoverageReport
from mvpc.evidence import Evidence, EvidenceType
from mvpc.hashing import hash_file
from datetime import datetime

class CoqBackend(VerificationBackend):
    def name(self) -> str:
        return "Coq"
        
    def supported_extensions(self) -> List[str]:
        return [".v"]
        
    def supports(self, path: str) -> bool:
        return any(path.endswith(ext) for ext in self.supported_extensions())
        
    def check_native_available(self) -> bool:
        from shutil import which
        return which("coqc") is not None

    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                if 'Admitted.' in line:
                    findings.append(Finding(code="COQ_ADMIT", severity=Severity.VIOLATION, message="Use of 'Admitted' detected", system="CoqStatic", line=i+1))
                if 'Axiom ' in line:
                    findings.append(Finding(code="COQ_AXIOM", severity=Severity.WARNING, message="Axiom usage detected", system="CoqStatic", line=i+1))

        except Exception as e:
            findings.append(Finding(code="STATIC_ERROR", severity=Severity.WARNING, message=str(e), system="CoqStatic"))
            
        ev = Evidence(
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Coq static analysis",
            timestamp=datetime.utcnow().isoformat(),
            artifact_path=path,
            artifact_hash=hash_file(path)
        )
        return findings, [ev]

    def run_native_verification(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings = []
        evidence = []
        if not self.check_native_available():
            return findings, evidence
            
        try:
            res = subprocess.run(["coqc", path], capture_output=True, text=True)
            if res.returncode != 0:
                findings.append(Finding(code="COQ_COMPILE_ERROR", severity=Severity.VIOLATION, message=res.stderr, system="CoqNative"))
            ev = Evidence(
                evidence_type=EvidenceType.NATIVE_VERIFICATION,
                description="Coq native compilation",
                timestamp=datetime.utcnow().isoformat(),
                artifact_path=path,
                artifact_hash=hash_file(path)
            )
            evidence.append(ev)
        except Exception as e:
            findings.append(Finding(code="NATIVE_ERROR", severity=Severity.WARNING, message=str(e), system="CoqNative"))
            
        return findings, evidence

    def audit(self, path: str) -> Tuple[List[Finding], List[Evidence], CoverageReport]:
        findings = []
        evidence = []
        checks_performed = ["Static Analysis"]
        checks_unavailable = []
        
        static_f, static_e = self.run_static_analysis(path)
        findings.extend(static_f)
        evidence.extend(static_e)
        
        if self.check_native_available():
            checks_performed.append("Native Verification")
            nat_f, nat_e = self.run_native_verification(path)
            findings.extend(nat_f)
            evidence.extend(nat_e)
        else:
            checks_unavailable.append("Native Verification (coqc binary missing)")
            
        coverage = CoverageReport(
            checks_performed=checks_performed,
            checks_unavailable=checks_unavailable,
            assumptions=[],
            trust_boundaries=[]
        )
        return findings, evidence, coverage
