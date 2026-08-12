import os
import re
import subprocess
from datetime import datetime, timezone
from typing import List, Tuple
from shutil import which

from mvpc.backends.base import VerificationBackend
from mvpc.trust import Finding, Severity, CoverageReport
from mvpc.evidence import Evidence, EvidenceType
from mvpc.hashing import hash_file
from mvpc.explanations import get_explanation

class CoqBackend(VerificationBackend):
    def name(self) -> str:
        return "Coq"
        
    def supported_extensions(self) -> List[str]:
        return [".v"]
        
    def supports(self, path: str) -> bool:
        return any(path.endswith(ext) for ext in self.supported_extensions())
        
    def check_native_available(self) -> bool:
        return which("coqc") is not None

    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings = []
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("(*") and stripped.endswith("*)"):
                    continue

                if re.search(r"\b(Admitted|admit)\b", line):
                    exp = get_explanation("COQ_ADMIT")
                    findings.append(Finding(
                        code="COQ_ADMIT",
                        severity=Severity.VIOLATION,
                        message="Use of 'Admitted' / 'admit' placeholder detected",
                        system="CoqStatic",
                        line=i,
                        remediation=exp["action"]
                    ))
                if re.match(r"^\s*Axiom\s+\S+", line):
                    exp = get_explanation("COQ_AXIOM")
                    findings.append(Finding(
                        code="COQ_AXIOM",
                        severity=Severity.WARNING,
                        message=f"Bare Axiom declared: {line.strip()}",
                        system="CoqStatic",
                        line=i,
                        remediation=exp["action"]
                    ))

        except Exception as e:
            findings.append(Finding(code="STATIC_ERROR", severity=Severity.WARNING, message=str(e), system="CoqStatic"))
            
        ev = Evidence(
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Coq static syntax analysis",
            timestamp=datetime.now(timezone.utc).isoformat(),
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
            res = subprocess.run(["coqc", path], capture_output=True, text=True, timeout=120)
            if res.returncode != 0:
                exp = get_explanation("COQ_COMPILE_ERROR")
                findings.append(Finding(
                    code="COQ_COMPILE_ERROR",
                    severity=Severity.VIOLATION,
                    message=res.stderr or res.stdout,
                    system="CoqNative",
                    remediation=exp["action"]
                ))
            ev = Evidence(
                evidence_type=EvidenceType.NATIVE_VERIFICATION,
                description="Coq native compilation",
                timestamp=datetime.now(timezone.utc).isoformat(),
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
