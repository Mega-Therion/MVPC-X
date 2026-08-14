"""Verification orchestrator with system self-integrity seals."""
from __future__ import annotations

import os
import platform
from typing import Optional

from mvpc.backends.registry import BackendRegistry
from mvpc.policy import PolicyLevel, get_policy, evaluate_attestation
from mvpc.claim import Claim, create_claim, load_claim_from_yaml
from mvpc.provenance import Provenance, SourceType
from mvpc.witness import generate_witness
from mvpc.trust import Finding, Severity
from mvpc.security import (
    IntegritySession,
    validate_intake,
    diff_system_fingerprints,
    DEFAULT_MAX_ARTIFACT_BYTES,
)
from mvpc.explanations import get_explanation
from mvpc.newton_architect import (
    AUTHORITY,
    merge_newton_findings,
    system_directive,
)


class VerificationEngine:
    def __init__(
        self,
        policy_level: PolicyLevel,
        registry: BackendRegistry,
        *,
        enforce_system_integrity: bool = True,
        mid_run_integrity_check: bool = True,
        max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
        allow_symlinks: bool = False,
    ):
        self.policy = get_policy(policy_level)
        self.registry = registry
        self.enforce_system_integrity = enforce_system_integrity
        self.mid_run_integrity_check = mid_run_integrity_check
        self.max_artifact_bytes = max_artifact_bytes
        self.allow_symlinks = allow_symlinks

    def _get_environment(self) -> dict:
        return {
            "os": os.name,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "newton_authority": AUTHORITY,
        }

    def verify_artifact(
        self,
        path: str,
        statement: Optional[str] = None,
        origin: Optional[SourceType] = None,
    ) -> Claim:
        path = os.path.abspath(path)

        intake = validate_intake(
            path,
            max_bytes=self.max_artifact_bytes,
            allow_symlinks=self.allow_symlinks,
        )
        if not intake.allowed:
            prov = Provenance(
                source_type=origin or SourceType.UNKNOWN,
                origin_description="Blocked at intake",
                timestamp="unknown",
                metadata={"intake": intake.to_dict()},
            )
            claim = create_claim(
                statement=statement or f"Intake blocked for {os.path.basename(path)}",
                origin=origin or SourceType.UNKNOWN,
                scope="file",
                definitions={},
                provenance=prov,
            )
            exp = get_explanation("INTAKE_BLOCKED")
            claim.findings = [
                Finding(
                    code="INTAKE_BLOCKED",
                    severity=Severity.VIOLATION,
                    message="; ".join(intake.reasons),
                    system="SecurityIntake",
                    remediation=exp.get("action"),
                )
            ]
            from mvpc.trust import AttestationState, CoverageReport

            claim.attestation_state = AttestationState.REJECTED
            claim.coverage = CoverageReport(
                checks_performed=["Intake Security Guard"],
                checks_unavailable=["All backends (blocked before audit)"],
                assumptions=[],
                trust_boundaries=["Untrusted path failed intake policy"],
            )
            return claim

        session = IntegritySession.begin(path if os.path.isfile(path) else None)

        backend = self.registry.get_backend(path)
        findings, evidence, coverage = backend.audit(path)

        artifact_text = ""
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    artifact_text = fh.read()
            except OSError:
                artifact_text = ""
        findings = merge_newton_findings(findings, artifact_text)
        if statement:
            findings = merge_newton_findings(findings, statement)
        coverage.checks_performed = list(coverage.checks_performed) + [
            "Newton Architect Protocol"
        ]

        if self.mid_run_integrity_check:
            if not session.check_mid():
                exp = get_explanation("SYSTEM_INTEGRITY_FAILURE")
                diffs = diff_system_fingerprints(
                    session.system_before, session.system_mid or {}
                )
                findings.append(
                    Finding(
                        code="SYSTEM_INTEGRITY_FAILURE",
                        severity=Severity.VIOLATION,
                        message=(
                            "MVPC-X package fingerprint changed MID-RUN. "
                            "Possible self-modification. "
                            + ("; ".join(diffs[:12]) or "(see integrity session)")
                        ),
                        system="SystemIntegrity",
                        remediation=exp.get("action"),
                    )
                )

        session.finalize()
        if self.enforce_system_integrity and not session.system_intact:
            exp = get_explanation("SYSTEM_INTEGRITY_FAILURE")
            diffs = diff_system_fingerprints(
                session.system_before, session.system_after or {}
            )
            findings.append(
                Finding(
                    code="SYSTEM_INTEGRITY_FAILURE",
                    severity=Severity.VIOLATION,
                    message=(
                        "MVPC-X package fingerprint changed during audit. "
                        "Verifier may be corrupted. "
                        + ("; ".join(diffs[:12]) or "")
                    ),
                    system="SystemIntegrity",
                    remediation=exp.get("action"),
                )
            )

        if session.artifact_ok is False:
            exp = get_explanation("ARTIFACT_MUTATION")
            findings.append(
                Finding(
                    code="ARTIFACT_MUTATION",
                    severity=Severity.VIOLATION,
                    message=(
                        "Artifact SHA-256 changed during audit "
                        f"(before={session.artifact_hash_before}, "
                        f"after={session.artifact_hash_after})"
                    ),
                    system="ArtifactIntegrity",
                    remediation=exp.get("action"),
                )
            )

        for reason in intake.reasons:
            if reason not in ("Intake OK", "Directory intake OK"):
                findings.append(
                    Finding(
                        code="INTAKE_WARNING",
                        severity=Severity.WARNING,
                        message=reason,
                        system="SecurityIntake",
                    )
                )

        coverage.checks_performed = list(coverage.checks_performed) + [
            "System Self-Integrity Seal",
            "Artifact Pre/Post Hash",
            "Intake Security Guard",
        ]

        attestation_state = evaluate_attestation(
            findings,
            coverage,
            self.policy,
            artifact_text=artifact_text,
            statement=statement,
        )

        stmt = statement or (
            f"Artifact {os.path.basename(path)} satisfies policy level {self.policy.level.name}"
        )
        org = origin or SourceType.UNKNOWN
        prov = Provenance(
            source_type=org,
            origin_description="Auto-generated by engine for artifact",
            timestamp=evidence[0].timestamp if evidence else "unknown",
            metadata={
                "integrity": session.to_dict(),
                "intake": intake.to_dict(),
                "newton_authority": AUTHORITY,
                "newton_directive": system_directive(),
            },
        )

        claim = create_claim(
            statement=stmt,
            origin=org,
            scope="file",
            definitions={},
            provenance=prov,
        )
        claim.evidence = evidence
        claim.findings = findings
        claim.coverage = coverage
        claim.attestation_state = attestation_state

        env = self._get_environment()
        env["system_integrity"] = session.to_dict()
        witness = generate_witness(claim, self.policy, env)
        if not claim.provenance.metadata:
            claim.provenance.metadata = {}
        claim.provenance.metadata["witness"] = witness.to_dict()
        claim.provenance.metadata["integrity"] = session.to_dict()

        return claim

    def verify_claim(self, claim_yaml_path: str) -> Claim:
        claim = load_claim_from_yaml(claim_yaml_path)
        return claim
