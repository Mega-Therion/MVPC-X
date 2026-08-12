"""Tests for witness generation, integrity, and human attestation sealing."""
from mvpc.claim import create_claim
from mvpc.evidence import Evidence, EvidenceType
from mvpc.policy import PolicyLevel, get_policy
from mvpc.provenance import Provenance, SourceType
from mvpc.trust import AttestationState, CoverageReport, Finding, Severity
from mvpc.witness import Witness, generate_witness
from mvpc.hashing import verify_witness_hash


def _sample_claim(with_violation: bool = False):
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
        checks_performed=["Static Analysis", "Native Verification"],
        checks_unavailable=[],
        assumptions=[],
        trust_boundaries=[],
    )
    if with_violation:
        claim.findings = [
            Finding("LEAN_SORRY", Severity.VIOLATION, "sorry", "LeanStatic", line=1)
        ]
        claim.attestation_state = AttestationState.REJECTED
    else:
        claim.attestation_state = AttestationState.VERIFIED
    return claim


def test_generate_witness_has_hash():
    claim = _sample_claim()
    policy = get_policy(PolicyLevel.DEFAULT)
    w = generate_witness(claim, policy, {"os": "test"})
    assert isinstance(w, Witness)
    assert w.witness_id.startswith("W-")
    assert w.claim_id == claim.id
    assert len(w.witness_hash) == 64
    assert w.verify_integrity() is True
    assert verify_witness_hash(w.to_dict()) is True


def test_witness_tamper_breaks_integrity():
    claim = _sample_claim()
    w = generate_witness(claim, get_policy(PolicyLevel.DEFAULT), {"os": "test"})
    w.attestation_state = "REJECTED"
    assert w.verify_integrity() is False


def test_add_human_attestation_reseals_hash():
    claim = _sample_claim()
    w = generate_witness(claim, get_policy(PolicyLevel.STRICT), {"os": "test"})
    old = w.witness_hash
    w.add_human_attestation("Dr. Test", notes="LGTM", accepted=True)
    assert w.witness_hash != old
    assert w.verify_integrity() is True
    assert len(w.human_attestations) == 1
    assert w.human_attestations[0]["signer"] == "Dr. Test"
    assert w.human_attestations[0]["accepted"] is True


def test_human_attestation_clears_missing_finding():
    claim = _sample_claim()
    w = generate_witness(claim, get_policy(PolicyLevel.DEFAULT), {})
    w.findings.append(
        {
            "code": "HUMAN_ATTESTATION_MISSING",
            "severity": "WARNING",
            "message": "need human",
            "system": "gov",
        }
    )
    w.human_review_obligations = ["Human review required"]
    w.recompute_hash()
    w.add_human_attestation("Reviewer", accepted=True)
    assert all(f.get("code") != "HUMAN_ATTESTATION_MISSING" for f in w.findings)
    assert w.human_review_obligations == []


def test_witness_markdown_contains_state():
    claim = _sample_claim(with_violation=True)
    w = generate_witness(claim, get_policy(PolicyLevel.DEFAULT), {})
    md = w.to_markdown()
    assert "REJECTED" in md or claim.attestation_state.name in md
    assert w.witness_id in md
