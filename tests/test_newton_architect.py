"""Newton Architect protocol enforcement tests."""
from mvpc.newton_architect import scan_artifact_text
from mvpc.policy import PolicyLevel, get_policy, evaluate_attestation
from mvpc.trust import AttestationState, CoverageReport, Severity
from mvpc.engine import VerificationEngine
from mvpc.backends.registry import get_default_registry


def test_scan_flags_vacuous_lean():
    findings = scan_artifact_text("theorem sovereign_convergence : True := trivial")
    assert any(f.code == "NEWTON_VACUOUS_PROOF" for f in findings)
    assert findings[0].severity == Severity.VIOLATION


def test_scan_flags_area_operator_without_sqrt():
    findings = scan_artifact_text("L_A = 1/(4 G_N) sum C_2(rho)")
    assert any(f.code == "NEWTON_AREA_OPERATOR" for f in findings)


def test_scan_requires_z0_for_omega_ln2():
    findings = scan_artifact_text("Omega_Lambda = ln 2")
    assert any(f.code == "NEWTON_EPOCH_OMEGA" for f in findings)
    ok = scan_artifact_text("Omega_Lambda = ln 2 at z=0 [O]")
    assert not any(f.code == "NEWTON_EPOCH_OMEGA" for f in ok)


def test_policy_carries_newton_authority():
    policy = get_policy(PolicyLevel.DEFAULT)
    assert policy.authority == "NEWTON ARCHITECT Protocol"
    assert ": True := trivial" in policy.blocked_patterns


def test_evaluate_attestation_rejects_newton_text():
    policy = get_policy(PolicyLevel.PERMISSIVE)
    coverage = CoverageReport(
        checks_performed=["Static Analysis"],
        checks_unavailable=[],
        assumptions=[],
        trust_boundaries=[],
    )
    state = evaluate_attestation(
        [],
        coverage,
        policy,
        artifact_text="theorem sovereign_convergence : True := trivial",
    )
    assert state == AttestationState.REJECTED


def test_engine_rejects_vacuous_artifact(tmp_path):
    path = tmp_path / "vacuous.lean"
    path.write_text("theorem sovereign_convergence : True := trivial\n", encoding="utf-8")
    engine = VerificationEngine(
        PolicyLevel.PERMISSIVE,
        get_default_registry(),
        enforce_system_integrity=False,
        mid_run_integrity_check=False,
    )
    claim = engine.verify_artifact(str(path))
    assert claim.attestation_state == AttestationState.REJECTED
    assert "Newton Architect Protocol" in claim.coverage.checks_performed
    assert any(f.code == "NEWTON_VACUOUS_PROOF" for f in claim.findings)
