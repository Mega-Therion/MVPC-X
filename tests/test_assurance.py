from mvpc.assurance import AssuranceLevel, VerificationEvidence, derive_assurance
from mvpc.trust_verdicts import TrustVerdict


def test_computation_is_not_formal_proof():
    evidence = [
        VerificationEvidence("sympy", "computation", TrustVerdict.COMPUTATION_VERIFIED)
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D1_REPRODUCIBLY_COMPUTED


def test_formal_requires_hardening_evidence_for_d3():
    evidence = [
        VerificationEvidence("lean", "formal", TrustVerdict.FORMALLY_CHECKED),
        VerificationEvidence("sig", "signature", TrustVerdict.EVIDENCE_SUPPORTED),
        VerificationEvidence("env", "environment", TrustVerdict.EVIDENCE_SUPPORTED),
        VerificationEvidence("axioms", "axiom_audit", TrustVerdict.EVIDENCE_SUPPORTED),
        VerificationEvidence("prov", "provenance", TrustVerdict.EVIDENCE_SUPPORTED),
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D3_HARDENED_FORMAL


def test_rejection_cannot_be_upgraded():
    evidence = [
        VerificationEvidence("lean", "formal", TrustVerdict.FORMALLY_CHECKED),
        VerificationEvidence("guard", "policy", TrustVerdict.REJECTED),
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D0_PROPOSED


def test_independent_formal_recheck_is_explicit():
    evidence = [
        VerificationEvidence("lean-a", "formal", TrustVerdict.FORMALLY_CHECKED, frozenset({"lean-b"})),
        VerificationEvidence("lean-b", "formal", TrustVerdict.FORMALLY_CHECKED, frozenset({"lean-a"})),
        VerificationEvidence("sig", "signature", TrustVerdict.EVIDENCE_SUPPORTED),
        VerificationEvidence("env", "environment", TrustVerdict.EVIDENCE_SUPPORTED),
        VerificationEvidence("axioms", "axiom_audit", TrustVerdict.EVIDENCE_SUPPORTED),
        VerificationEvidence("prov", "provenance", TrustVerdict.EVIDENCE_SUPPORTED),
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D4_INDEPENDENTLY_RECHECKED
