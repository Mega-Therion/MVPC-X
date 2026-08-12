import os
import subprocess
from typing import List, Tuple
from mvpc.backends.base import VerificationBackend
from mvpc.trust import Finding, Severity, CoverageReport
from mvpc.evidence import Evidence, EvidenceType
from mvpc.hashing import hash_file
from datetime import datetime

class LeanBackend(VerificationBackend):
    def name(self) -> str:
        return "Lean 4"
        
    def supported_extensions(self) -> List[str]:
        return [".lean"]
        
    def supports(self, path: str) -> bool:
        return any(path.endswith(ext) for ext in self.supported_extensions())
        
    def check_native_available(self) -> bool:
        from shutil import which
        return which("lean") is not None or which("lake") is not None

    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                if 'sorry' in line:
                    findings.append(Finding(code="LEAN_SORRY", severity=Severity.VIOLATION, message="Use of 'sorry' detected", system="LeanStatic", line=i+1))
                if 'admit' in line:
                    findings.append(Finding(code="LEAN_ADMIT", severity=Severity.VIOLATION, message="Use of 'admit' detected", system="LeanStatic", line=i+1))
                if 'axiom ' in line:
                    findings.append(Finding(code="LEAN_AXIOM", severity=Severity.WARNING, message="Axiom usage detected", system="LeanStatic", line=i+1))
                if 'native_decide' in line:
                    findings.append(Finding(code="LEAN_NATIVE_DECIDE", severity=Severity.WARNING, message="native_decide usage detected", system="LeanStatic", line=i+1))

        except Exception as e:
            findings.append(Finding(code="STATIC_ERROR", severity=Severity.WARNING, message=str(e), system="LeanStatic"))
            
        ev = Evidence(
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Lean static analysis",
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
            res = subprocess.run(["lean", path], capture_output=True, text=True)
            if res.returncode != 0:
                findings.append(Finding(code="LEAN_COMPILE_ERROR", severity=Severity.VIOLATION, message=res.stderr, system="LeanNative"))
            ev = Evidence(
                evidence_type=EvidenceType.NATIVE_VERIFICATION,
                description="Lean native compilation",
                timestamp=datetime.utcnow().isoformat(),
                artifact_path=path,
                artifact_hash=hash_file(path)
            )
            evidence.append(ev)
        except Exception as e:
            findings.append(Finding(code="NATIVE_ERROR", severity=Severity.WARNING, message=str(e), system="LeanNative"))
            
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
            checks_unavailable.append("Native Verification (lean/lake binary missing)")
            
        coverage = CoverageReport(
            checks_performed=checks_performed,
            checks_unavailable=checks_unavailable,
            assumptions=[],
            trust_boundaries=[]
        )
        return findings, evidence, coverage
