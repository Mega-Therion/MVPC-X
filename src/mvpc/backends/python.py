import os
import subprocess
from typing import List, Tuple
from mvpc.backends.base import VerificationBackend
from mvpc.trust import Finding, Severity, CoverageReport
from mvpc.evidence import Evidence, EvidenceType
from mvpc.hashing import hash_file
from datetime import datetime

class PythonBackend(VerificationBackend):
    def name(self) -> str:
        return "Python"
        
    def supported_extensions(self) -> List[str]:
        return [".py"]
        
    def supports(self, path: str) -> bool:
        return any(path.endswith(ext) for ext in self.supported_extensions())
        
    def check_native_available(self) -> bool:
        from shutil import which
        return which("python") is not None or which("python3") is not None

    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for i, line in enumerate(lines):
                if 'exec(' in line:
                    findings.append(Finding(code="PY_EXEC", severity=Severity.WARNING, message="Use of 'exec()' detected", system="PythonStatic", line=i+1))
                if 'eval(' in line:
                    findings.append(Finding(code="PY_EVAL", severity=Severity.WARNING, message="Use of 'eval()' detected", system="PythonStatic", line=i+1))
                if 'os.system(' in line:
                    findings.append(Finding(code="PY_OS_SYSTEM", severity=Severity.WARNING, message="Use of 'os.system()' detected", system="PythonStatic", line=i+1))
                if 'shell=True' in line:
                    findings.append(Finding(code="PY_SHELL_TRUE", severity=Severity.WARNING, message="Use of subprocess with 'shell=True' detected", system="PythonStatic", line=i+1))

        except Exception as e:
            findings.append(Finding(code="STATIC_ERROR", severity=Severity.WARNING, message=str(e), system="PythonStatic"))
            
        ev = Evidence(
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Python static analysis",
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
            from shutil import which
            py_bin = "python3" if which("python3") else "python"
            res = subprocess.run([py_bin, "-m", "py_compile", path], capture_output=True, text=True)
            if res.returncode != 0:
                findings.append(Finding(code="PY_SYNTAX_ERROR", severity=Severity.VIOLATION, message=res.stderr, system="PythonNative"))
            ev = Evidence(
                evidence_type=EvidenceType.NATIVE_VERIFICATION,
                description="Python syntax check",
                timestamp=datetime.utcnow().isoformat(),
                artifact_path=path,
                artifact_hash=hash_file(path)
            )
            evidence.append(ev)
        except Exception as e:
            findings.append(Finding(code="NATIVE_ERROR", severity=Severity.WARNING, message=str(e), system="PythonNative"))
            
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
            checks_unavailable.append("Native Verification (python binary missing)")
            
        coverage = CoverageReport(
            checks_performed=checks_performed,
            checks_unavailable=checks_unavailable,
            assumptions=[],
            trust_boundaries=[]
        )
        return findings, evidence, coverage
