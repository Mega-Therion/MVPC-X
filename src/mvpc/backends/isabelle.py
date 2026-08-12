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

class IsabelleBackend(VerificationBackend):
    def name(self) -> str:
        return "Isabelle"

    def supported_extensions(self) -> List[str]:
        return [".thy"]

    def supports(self, path: str) -> bool:
        p = path.lower()
        return any(p.endswith(ext) for ext in self.supported_extensions()) or os.path.basename(path) == "ROOT"

    def check_native_available(self) -> bool:
        return which("isabelle") is not None

    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings: List[Finding] = []
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                # Ignore comments
                stripped = line.strip()
                if stripped.startswith("(*") and stripped.endswith("*)"):
                    continue

                if re.search(r"\b(sorry|oops)\b", line):
                    exp = get_explanation("ISABELLE_SORRY")
                    findings.append(Finding(
                        code="ISABELLE_SORRY",
                        severity=Severity.VIOLATION,
                        message=f"Incomplete proof (sorry/oops) detected on line {i}",
                        system="IsabelleStatic",
                        line=i,
                        remediation=exp["action"]
                    ))

                if re.search(r"\baxiomatization\b", line):
                    exp = get_explanation("ISABELLE_AXIOM")
                    findings.append(Finding(
                        code="ISABELLE_AXIOM",
                        severity=Severity.VIOLATION,
                        message=f"Axiomatization declaration detected on line {i}",
                        system="IsabelleStatic",
                        line=i,
                        remediation=exp["action"]
                    ))

        except Exception as e:
            findings.append(Finding(
                code="STATIC_ERROR",
                severity=Severity.WARNING,
                message=str(e),
                system="IsabelleStatic"
            ))

        ev = Evidence(
            evidence_type=EvidenceType.STATIC_ANALYSIS,
            description="Isabelle static AST / text scan",
            timestamp=datetime.now(timezone.utc).isoformat(),
            artifact_path=path,
            artifact_hash=hash_file(path)
        )
        return findings, [ev]

    def run_native_verification(self, path: str) -> Tuple[List[Finding], List[Evidence]]:
        findings: List[Finding] = []
        evidence: List[Evidence] = []
        if not self.check_native_available():
            return findings, evidence

        # Search for parent ROOT file
        root_dir = os.path.dirname(os.path.abspath(path))
        found_root = False
        current = root_dir
        for _ in range(4):
            if os.path.isfile(os.path.join(current, "ROOT")):
                root_dir = current
                found_root = True
                break
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

        if not found_root:
            exp = get_explanation("COVERAGE_DEGRADED")
            findings.append(Finding(
                code="COVERAGE_DEGRADED",
                severity=Severity.WARNING,
                message="No Isabelle ROOT session file found in directory hierarchy; session build skipped.",
                system="IsabelleNative",
                remediation="Provide a ROOT session file to enable full 'isabelle build -D .'"
            ))
            return findings, evidence

        try:
            res = subprocess.run(
                ["isabelle", "build", "-D", root_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            if res.returncode != 0:
                exp = get_explanation("ISABELLE_BUILD_FAILED")
                findings.append(Finding(
                    code="ISABELLE_BUILD_FAILED",
                    severity=Severity.VIOLATION,
                    message=f"isabelle build failed:\n{res.stderr or res.stdout}",
                    system="IsabelleNative",
                    remediation=exp["action"]
                ))
            ev = Evidence(
                evidence_type=EvidenceType.NATIVE_VERIFICATION,
                description="Isabelle session build verification",
                timestamp=datetime.now(timezone.utc).isoformat(),
                artifact_path=path,
                artifact_hash=hash_file(path)
            )
            evidence.append(ev)
        except Exception as e:
            findings.append(Finding(
                code="NATIVE_ERROR",
                severity=Severity.WARNING,
                message=str(e),
                system="IsabelleNative"
            ))

        return findings, evidence

    def audit(self, path: str) -> Tuple[List[Finding], List[Evidence], CoverageReport]:
        findings: List[Finding] = []
        evidence: List[Evidence] = []
        checks_performed = ["Static Analysis"]
        checks_unavailable: List[str] = []

        static_f, static_e = self.run_static_analysis(path)
        findings.extend(static_f)
        evidence.extend(static_e)

        if self.check_native_available():
            checks_performed.append("Native Verification")
            nat_f, nat_e = self.run_native_verification(path)
            findings.extend(nat_f)
            evidence.extend(nat_e)
        else:
            checks_unavailable.append("Native Verification (isabelle executable missing)")

        coverage = CoverageReport(
            checks_performed=checks_performed,
            checks_unavailable=checks_unavailable,
            assumptions=[],
            trust_boundaries=[]
        )
        return findings, evidence, coverage
