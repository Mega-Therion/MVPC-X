from mvpc.assurance import AssuranceLevel, VerificationEvidence, derive_assurance
from mvpc.trust_verdicts import TrustVerdict


CLAIM_ID = "res-nova:F7"
PROPOSITION = "17 tracked Lean modules elaborate with standard axioms"
ARTIFACT_HASH = "sha256:run-007"


def test_computation_is_not_formal_proof():
    evidence = [
        VerificationEvidence(
            claim_id=CLAIM_ID,
            proposition=PROPOSITION,
            source_id="sympy",
            kind="computation",
            verdict=TrustVerdict.COMPUTATION_VERIFIED,
        )
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D1_REPRODUCIBLY_COMPUTED


def test_formal_requires_hardening_evidence_for_d3():
    evidence = [
        VerificationEvidence(
            claim_id=CLAIM_ID,
            proposition=PROPOSITION,
            source_id="lean",
            kind="formal",
            verdict=TrustVerdict.FORMALLY_CHECKED,
            foundation="lean4-mathlib",
            artifact_hash=ARTIFACT_HASH,
        ),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "sig", "signature", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "env", "environment", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "axioms", "axiom_audit", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "prov", "provenance", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D3_HARDENED_FORMAL


def test_rejection_cannot_be_upgraded():
    evidence = [
        VerificationEvidence(
            claim_id=CLAIM_ID,
            proposition=PROPOSITION,
            source_id="lean",
            kind="formal",
            verdict=TrustVerdict.FORMALLY_CHECKED,
            foundation="lean4-mathlib",
            artifact_hash=ARTIFACT_HASH,
        ),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "guard", "policy", TrustVerdict.REJECTED, artifact_hash=ARTIFACT_HASH),
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D0_PROPOSED


def test_independent_formal_recheck_is_explicit():
    evidence = [
        VerificationEvidence(
            claim_id=CLAIM_ID,
            proposition=PROPOSITION,
            source_id="lean-a",
            kind="formal",
            verdict=TrustVerdict.FORMALLY_CHECKED,
            foundation="lean4-mathlib",
            independent_from=frozenset({"lean-b"}),
            artifact_hash=ARTIFACT_HASH,
        ),
        VerificationEvidence(
            claim_id=CLAIM_ID,
            proposition=PROPOSITION,
            source_id="lean-b",
            kind="formal",
            verdict=TrustVerdict.FORMALLY_CHECKED,
            foundation="lean4-mathlib",
            independent_from=frozenset({"lean-a"}),
            artifact_hash=ARTIFACT_HASH,
        ),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "sig", "signature", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "env", "environment", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "axioms", "axiom_audit", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "prov", "provenance", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D4_INDEPENDENTLY_RECHECKED


def test_mixed_claims_cannot_upgrade_assurance():
    evidence = [
        VerificationEvidence(
            claim_id=CLAIM_ID,
            proposition=PROPOSITION,
            source_id="lean-a",
            kind="formal",
            verdict=TrustVerdict.FORMALLY_CHECKED,
            artifact_hash=ARTIFACT_HASH,
        ),
        VerificationEvidence(
            claim_id="res-nova:D3.1",
            proposition="lim_{x->inf} mu(x)=1",
            source_id="lean-b",
            kind="formal",
            verdict=TrustVerdict.FORMALLY_CHECKED,
            artifact_hash=ARTIFACT_HASH,
        ),
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D0_PROPOSED


def test_human_attestation_needs_scope_before_d6():
    evidence = [
        VerificationEvidence(
            claim_id=CLAIM_ID,
            proposition=PROPOSITION,
            source_id="lean-a",
            kind="formal",
            verdict=TrustVerdict.FORMALLY_CHECKED,
            foundation="lean4-mathlib",
            independent_from=frozenset({"rocq"}),
            artifact_hash=ARTIFACT_HASH,
        ),
        VerificationEvidence(
            claim_id=CLAIM_ID,
            proposition=PROPOSITION,
            source_id="rocq",
            kind="formal",
            verdict=TrustVerdict.FORMALLY_CHECKED,
            foundation="coq",
            independent_from=frozenset({"lean-a"}),
            artifact_hash=ARTIFACT_HASH,
        ),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "sig", "signature", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "env", "environment", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "axioms", "axiom_audit", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "prov", "provenance", TrustVerdict.EVIDENCE_SUPPORTED, artifact_hash=ARTIFACT_HASH),
        VerificationEvidence(CLAIM_ID, PROPOSITION, "human", "human_review", TrustVerdict.HUMAN_ATTESTED, artifact_hash=ARTIFACT_HASH),
    ]
    assert derive_assurance(evidence) == AssuranceLevel.D5_CROSS_FOUNDATION

    evidence.append(
        VerificationEvidence(
            claim_id=CLAIM_ID,
            proposition=PROPOSITION,
            source_id="human-scoped",
            kind="human_review",
            verdict=TrustVerdict.HUMAN_ATTESTED,
            artifact_hash=ARTIFACT_HASH,
            human_review_scope="natural-language/formal statement/definitions/assumptions",
        )
    )
    assert derive_assurance(evidence) == AssuranceLevel.D6_PUBLICATION_GRADE
