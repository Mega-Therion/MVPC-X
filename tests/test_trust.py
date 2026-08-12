"""Tests for trust primitives: states, findings, coverage."""
from mvpc.trust import AttestationState, CoverageReport, Finding, Severity


def test_attestation_states():
    names = {s.name for s in AttestationState}
    assert names == {"VERIFIED", "CONDITIONAL", "REJECTED", "UNVERIFIED"}


def test_severity_levels():
    assert Severity.VIOLATION
    assert Severity.WARNING
    assert Severity.INFO


def test_finding_fields():
    f = Finding(
        code="LEAN_SORRY",
        severity=Severity.VIOLATION,
        message="sorry found",
        system="LeanStatic",
        line=3,
        remediation="Remove sorry",
    )
    assert f.line == 3
    assert f.remediation.startswith("Remove")


def test_coverage_report_lists():
    c = CoverageReport(
        checks_performed=["Static Analysis"],
        checks_unavailable=["Native Verification"],
        assumptions=["lean missing"],
        trust_boundaries=["static-only"],
    )
    assert "Static Analysis" in c.checks_performed
    assert len(c.trust_boundaries) == 1
