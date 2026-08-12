"""Tests for the policy engine and attestation evaluation."""
import pytest
from mvpc.policy import PolicyLevel, Policy, get_policy, evaluate_attestation
from mvpc.trust import AttestationState, Finding, Severity, CoverageReport


def test_get_policy_levels():
    """All three policy levels should be constructable."""
    for level in PolicyLevel:
        policy = get_policy(level)
        assert policy.level == level


def test_default_policy_no_native_gives_conditional():
    """DEFAULT policy + no native verification → CONDITIONAL."""
    policy = get_policy(PolicyLevel.DEFAULT)
    coverage = CoverageReport(
        checks_performed=["Static Analysis"],
        checks_unavailable=["Native Verification (lean/lake binary missing)"],
        assumptions=[],
        trust_boundaries=[],
    )
    result = evaluate_attestation([], coverage, policy)
    assert result == AttestationState.CONDITIONAL


def test_strict_policy_no_native_gives_rejected():
    """STRICT policy + no native verification → REJECTED."""
    policy = get_policy(PolicyLevel.STRICT)
    coverage = CoverageReport(
        checks_performed=["Static Analysis"],
        checks_unavailable=["Native Verification"],
        assumptions=[],
        trust_boundaries=[],
    )
    result = evaluate_attestation([], coverage, policy)
    assert result == AttestationState.REJECTED


def test_permissive_policy_static_only_gives_verified():
    """PERMISSIVE policy + static analysis clean → VERIFIED."""
    policy = get_policy(PolicyLevel.PERMISSIVE)
    coverage = CoverageReport(
        checks_performed=["Static Analysis"],
        checks_unavailable=[],
        assumptions=[],
        trust_boundaries=[],
    )
    result = evaluate_attestation([], coverage, policy)
    assert result == AttestationState.VERIFIED


def test_any_policy_violations_gives_rejected():
    """Any policy + VIOLATION findings → REJECTED."""
    violation = Finding(
        code="TEST_VIOLATION",
        severity=Severity.VIOLATION,
        message="Test violation",
        system="test",
    )
    coverage = CoverageReport(
        checks_performed=["Static Analysis", "Native Verification"],
        checks_unavailable=[],
        assumptions=[],
        trust_boundaries=[],
    )
    for level in PolicyLevel:
        policy = get_policy(level)
        result = evaluate_attestation([violation], coverage, policy)
        assert result == AttestationState.REJECTED, f"Policy {level.name} should REJECT on violations"


def test_default_policy_with_native_gives_verified():
    """DEFAULT policy + native verification + no violations → VERIFIED."""
    policy = get_policy(PolicyLevel.DEFAULT)
    coverage = CoverageReport(
        checks_performed=["Static Analysis", "Native Verification"],
        checks_unavailable=[],
        assumptions=[],
        trust_boundaries=[],
    )
    result = evaluate_attestation([], coverage, policy)
    assert result == AttestationState.VERIFIED


def test_strict_policy_with_native_gives_verified():
    """STRICT policy + native verification + no violations → VERIFIED."""
    policy = get_policy(PolicyLevel.STRICT)
    coverage = CoverageReport(
        checks_performed=["Static Analysis", "Native Verification"],
        checks_unavailable=[],
        assumptions=[],
        trust_boundaries=[],
    )
    result = evaluate_attestation([], coverage, policy)
    assert result == AttestationState.VERIFIED


def test_warnings_dont_cause_rejection():
    """WARNING severity findings should not cause REJECTED status."""
    warning = Finding(
        code="TEST_WARNING",
        severity=Severity.WARNING,
        message="Test warning",
        system="test",
    )
    policy = get_policy(PolicyLevel.PERMISSIVE)
    coverage = CoverageReport(
        checks_performed=["Static Analysis"],
        checks_unavailable=[],
        assumptions=[],
        trust_boundaries=[],
    )
    result = evaluate_attestation([warning], coverage, policy)
    assert result != AttestationState.REJECTED
