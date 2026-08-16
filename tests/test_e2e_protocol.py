from mvpc.assurance import AssuranceLevel, VerificationEvidence, derive_assurance
from mvpc.claim_binding import SemanticTest, bind_claim_to_formal_proof
from mvpc.formalization import build_formalization_review
from mvpc.trust_verdicts import TrustVerdict
from mvpc.verification_plan import CheckKind, VerificationPlan, VerificationResult, VerificationTarget
from mvpc.proof_record import ProofRecord
from mvpc.witness_seal import generate_signing_keypair, seal_payload, verify_sealed_payload


def test_binding_digest_changes_when_formal_target_changes():
    t = SemanticTest("meaning", "formal captures intended statement", "same", "same", True)
    a = bind_claim_to_formal_proof(
        claim_id="C-TEST-1",
        natural_statement="For every real x, x + 0 = x.",
        scope="real numbers",
        formal_language="Lean4",
        formal_statement="∀ x : ℝ, x + 0 = x",
        declaration="add_zero",
        proof_artifact_hash="abc",
        semantic_tests=[t],
    )
    b = bind_claim_to_formal_proof(
        claim_id="C-TEST-1",
        natural_statement="For every real x, x + 0 = x.",
        scope="real numbers",
        formal_language="Lean4",
        formal_statement="∀ x : ℝ, x + 0 = x + 1",
        declaration="wrong",
        proof_artifact_hash="abc",
        semantic_tests=[t],
    )
    assert a.binding_digest != b.binding_digest


def test_assurance_requires_explicit_independence_and_foundations():
    common = [
        VerificationEvidence("lean", "formal", TrustVerdict.FORMALLY_CHECKED, foundation="Lean", independence_group="A"),
        VerificationEvidence("environment", "environment", TrustVerdict.EVIDENCE_SUPPORTED),
        VerificationEvidence("axioms", "axiom_audit", TrustVerdict.EVIDENCE_SUPPORTED),
        VerificationEvidence("provenance", "provenance", TrustVerdict.EVIDENCE_SUPPORTED),
        VerificationEvidence("signature", "signature", TrustVerdict.EVIDENCE_SUPPORTED),
    ]
    assert derive_assurance(common) == AssuranceLevel.D3_HARDENED_FORMAL
    common.append(VerificationEvidence("rocq", "formal", TrustVerdict.FORMALLY_CHECKED, foundation="Rocq", independence_group="B"))
    assert derive_assurance(common) == AssuranceLevel.D5_CROSS_FOUNDATION
    common.append(VerificationEvidence("human", "human_review", TrustVerdict.HUMAN_ATTESTED))
    assert derive_assurance(common) == AssuranceLevel.D6_PUBLICATION_GRADE


def test_plan_rejects_unexpected_results():
    plan = VerificationPlan(
        "C-1",
        [VerificationTarget("lean", CheckKind.FORMAL, required=True, artifact_path="proof.lean")],
    )
    result = VerificationResult("rogue", CheckKind.FORMAL, TrustVerdict.FORMALLY_CHECKED)
    evaluation = plan.evaluate([result])
    assert evaluation["complete"] is False
    assert evaluation["unknown_results"]
    assert evaluation["missing_required"]


def test_formalization_mismatch_blocks_publication_grade():
    review = build_formalization_review(
        claim_id="C-1",
        natural_statement="A",
        formal_statement="B",
        formal_language="Lean4",
        tests=[SemanticTest("t", "semantic", "A", "B", True)],
        divergences=["B changes the domain"],
    )
    assert review.approved_for_formal_check is False


def test_sealed_record_is_tamper_evident():
    key, public = generate_signing_keypair()
    payload = {"claim_id": "C-1", "result": "FORMALLY_CHECKED"}
    bundle = seal_payload(payload, key)
    assert bundle["signing_key_id"] == public
    assert verify_sealed_payload(bundle) is True
    bundle["payload"]["result"] = "REJECTED"
    assert verify_sealed_payload(bundle) is False


def test_proof_record_binds_all_layers():
    test = SemanticTest("t", "semantic fidelity", "same", "same", True)
    binding = bind_claim_to_formal_proof(
        claim_id="C-99",
        natural_statement="A",
        scope="test",
        formal_language="Lean4",
        formal_statement="A_formal",
        declaration="theorem_a",
        proof_artifact_hash="hash-proof",
        semantic_tests=[test],
    )
    plan = VerificationPlan(
        "C-99",
        [VerificationTarget("lean", CheckKind.FORMAL, required=True, independent_group="A", foundation="Lean", artifact_path="proof.lean")],
    )
    review = build_formalization_review(
        claim_id="C-99",
        natural_statement="A",
        formal_statement="A_formal",
        formal_language="Lean4",
        tests=[test],
    )
    result = VerificationResult(
        "lean", CheckKind.FORMAL, TrustVerdict.FORMALLY_CHECKED,
        artifact_hash="hash-proof", artifact_path="proof.lean",
        foundation="Lean", independent_group="A", declaration="theorem_a",
    )
    record = ProofRecord(binding, plan, review, [result])
    assert record.binding.claim_id == record.plan.claim_id == record.formalization.claim_id
    assert record.assurance_level == AssuranceLevel.D2_FORMALLY_CHECKED
    assert record.record_digest
