"""Tests for the SAMO V_mech mechanical witness feed (witness_feed.py)."""
import json

from mvpc.claim import create_claim
from mvpc.evidence import Evidence, EvidenceType
from mvpc.policy import PolicyLevel, get_policy
from mvpc.provenance import Provenance, SourceType
from mvpc.trust import AttestationState, CoverageReport, Finding, Severity
from mvpc.witness import generate_witness
from mvpc.witness_feed import (
    FEED_SCHEMA,
    mechanical_witness_feed,
    mechanical_witness_feed_json,
)


def _witness(performed, unavailable, state, violation=False, error=False):
    prov = Provenance(
        source_type=SourceType.HUMAN,
        origin_description="test",
        timestamp="2026-08-12T00:00:00+00:00",
        metadata={},
    )
    claim = create_claim("demo", SourceType.HUMAN, "file", {}, prov)
    claim.evidence = [
        Evidence(
            EvidenceType.STATIC_ANALYSIS,
            "scan",
            "2026-08-12T00:00:00+00:00",
            artifact_path="demo.lean",
            artifact_hash="a" * 64,
        )
    ]
    claim.coverage = CoverageReport(
        checks_performed=performed,
        checks_unavailable=unavailable,
        assumptions=[],
        trust_boundaries=[],
    )
    if violation:
        claim.findings = [
            Finding("LEAN_SORRY", Severity.VIOLATION, "sorry", "LeanStatic", line=1)
        ]
    if error:
        claim.findings = [
            Finding(
                "NATIVE_ERROR",
                Severity.WARNING,
                "coqc invocation timed out",
                "CoqNative",
            )
        ]
    claim.attestation_state = state
    return generate_witness(claim, get_policy(PolicyLevel.DEFAULT), {"os": "test"})


def _clean_witness():
    return _witness(
        ["Static Analysis", "Native Verification"], [], AttestationState.VERIFIED
    )


def test_clean_witness_yields_one():
    feed = mechanical_witness_feed([_clean_witness()])
    assert feed["schema"] == FEED_SCHEMA
    assert feed["v_mech"] == 1.0
    assert feed["checks_passed"] == 2
    assert feed["checks_total"] == 2
    assert feed["checks_unavailable"] == []
    assert feed["witnesses"][0]["integrity_ok"] is True


def test_unavailable_checks_count_against_yield_and_are_named():
    w = _witness(
        ["Static Analysis"], ["Native Verification"], AttestationState.CONDITIONAL
    )
    feed = mechanical_witness_feed([w])
    assert feed["v_mech"] == 0.5
    assert feed["checks_passed"] == 1
    assert feed["checks_total"] == 2
    # Zero hidden checks_unavailable: the name is surfaced at the top level.
    assert feed["checks_unavailable"] == ["Native Verification"]


def test_violation_witness_earns_no_yield():
    w = _witness(
        ["Static Analysis", "Native Verification"],
        [],
        AttestationState.REJECTED,
        violation=True,
    )
    feed = mechanical_witness_feed([w])
    assert feed["v_mech"] == 0.0
    assert feed["checks_passed"] == 0
    assert feed["checks_total"] == 2
    assert feed["witnesses"][0]["violation_count"] == 1


def test_tampered_witness_earns_no_yield():
    w = _clean_witness()
    w.attestation_state = "CONDITIONAL"  # mutate after sealing: hash breaks
    feed = mechanical_witness_feed([w])
    assert feed["witnesses"][0]["integrity_ok"] is False
    assert feed["v_mech"] == 0.0


def test_empty_feed_is_zero_not_one():
    feed = mechanical_witness_feed([])
    assert feed["v_mech"] == 0.0
    assert feed["checks_total"] == 0
    assert feed["witnesses"] == []


def test_mixed_witnesses_aggregate_by_checks():
    clean = _clean_witness()  # 2 passed / 2 total
    partial = _witness(
        ["Static Analysis"], ["Native Verification"], AttestationState.CONDITIONAL
    )  # 1 passed / 2 total
    feed = mechanical_witness_feed([clean, partial])
    assert feed["checks_passed"] == 3
    assert feed["checks_total"] == 4
    assert feed["v_mech"] == 0.75


def test_feed_json_round_trips():
    payload = mechanical_witness_feed_json([_clean_witness()])
    parsed = json.loads(payload)
    assert parsed["schema"] == FEED_SCHEMA
    assert parsed["v_mech"] == 1.0


def test_execution_error_witness_earns_no_yield():
    # A checker invocation that raises (here: a coqc timeout, emitted by the
    # backend as a WARNING-severity NATIVE_ERROR) verified nothing: the
    # performed checks earn no credit, but stay in the denominator.
    w = _witness(
        ["Static Analysis", "Native Verification"],
        [],
        AttestationState.CONDITIONAL,
        error=True,
    )
    feed = mechanical_witness_feed([w])
    assert feed["v_mech"] == 0.0
    assert feed["checks_passed"] == 0
    assert feed["checks_total"] == 2
    assert feed["witnesses"][0]["error_count"] == 1
