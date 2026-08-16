import textwrap

from mvpc.assurance import AssuranceLevel, VerificationEvidence, derive_assurance
from mvpc.claim import load_claim_from_yaml
from mvpc.claim_binding import SemanticTest, bind_claim_to_formal_proof
from mvpc.formalization import build_formalization_review
from mvpc.trust_verdicts import TrustVerdict
from mvpc.verification_plan import CheckKind, VerificationPlan, VerificationResult, VerificationTarget
from mvpc.verification_fabric import VerificationFabric
from mvpc.proof_record import ProofRecord
from mvpc.witness_seal import generate_signing_keypair, seal_payload, verify_sealed_payload


def test_binding_digest_changes_when_formal_target_changes():
    t = SemanticTest("meaning", "formal captures intended statement", "same", "same", True)
    common = dict(claim_id="C-TEST-1", natural_statement="For every real x, x + 0 = x.", scope="real numbers", formal_language="Lean4", proof_artifact_hash="abc", semantic_tests=[t])
    a = bind_claim_to_formal_proof(formal_statement="∀ x : ℝ, x + 0 = x", declaration="add_zero", **common)
    b = bind_claim_to_formal_proof(formal_statement="∀ x : ℝ, x + 0 = x + 1", declaration="wrong", **common)
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
    plan = VerificationPlan("C-1", [VerificationTarget("lean", CheckKind.FORMAL, required=True, artifact_path="proof.lean")])
    evaluation = plan.evaluate([VerificationResult("rogue", CheckKind.FORMAL, TrustVerdict.FORMALLY_CHECKED)])
    assert evaluation["complete"] is False
    assert evaluation["unknown_results"]
    assert evaluation["missing_required"]


def test_formalization_mismatch_blocks_publication_grade():
    review = build_formalization_review(
        claim_id="C-1", natural_statement="A", formal_statement="B", formal_language="Lean4",
        tests=[SemanticTest("t", "semantic", "A", "B", True)], divergences=["B changes the domain"],
    )
    assert review.approved_for_formal_check is False


def test_sealed_record_is_tamper_evident():
    key, public = generate_signing_keypair()
    bundle = seal_payload({"claim_id": "C-1", "result": "FORMALLY_CHECKED"}, key)
    assert bundle["signing_key_id"] == public
    assert verify_sealed_payload(bundle) is True
    bundle["payload"]["result"] = "REJECTED"
    assert verify_sealed_payload(bundle) is False


def _bound_fixture():
    test = SemanticTest("t", "semantic fidelity", "same", "same", True)
    binding = bind_claim_to_formal_proof(
        claim_id="C-99", natural_statement="A", scope="test", formal_language="Lean4",
        formal_statement="A_formal", declaration="theorem_a", proof_artifact_hash="hash-proof", semantic_tests=[test],
    )
    plan = VerificationPlan(
        "C-99", [VerificationTarget("lean", CheckKind.FORMAL, required=True, independent_group="A", foundation="Lean", artifact_path="proof.lean")],
    )
    review = build_formalization_review(
        claim_id="C-99", natural_statement="A", formal_statement="A_formal", formal_language="Lean4", tests=[test],
    )
    return binding, plan, review


def test_proof_record_binds_exact_proof_identity():
    binding, plan, review = _bound_fixture()
    good = VerificationResult("lean", CheckKind.FORMAL, TrustVerdict.FORMALLY_CHECKED, artifact_hash="hash-proof", artifact_path="proof.lean", foundation="Lean", independent_group="A", declaration="theorem_a")
    record = ProofRecord(binding, plan, review, [good])
    assert record.bindings_valid is True
    assert record.assurance_level == AssuranceLevel.D2_FORMALLY_CHECKED
    assert record.record_digest

    bad = VerificationResult("lean", CheckKind.FORMAL, TrustVerdict.FORMALLY_CHECKED, artifact_hash="wrong-hash", artifact_path="proof.lean", foundation="Lean", independent_group="A", declaration="theorem_a")
    tampered = ProofRecord(binding, plan, review, [bad])
    assert tampered.bindings_valid is False
    assert "artifact hash mismatch" in tampered.validation_errors()[0]


def test_claim_manifest_yaml_round_trip(tmp_path):
    manifest = textwrap.dedent("""
        claim:
          id: C-YAML-1
          statement: "3 + 4 = 7"
          origin: human
          scope: "integer arithmetic"
          assumptions:
            - "standard arithmetic"
          evidence:
            - type: computation
              path: result.py
    """)
    path = tmp_path / "claim.yaml"
    path.write_text(manifest, encoding="utf-8")
    claim = load_claim_from_yaml(str(path))
    assert claim.id == "C-YAML-1"
    assert claim.statement == "3 + 4 = 7"
    assert claim.assumptions == ["standard arithmetic"]
    assert claim.evidence[0].artifact_path == "result.py"


def test_fabric_executes_only_registered_verifier_and_preserves_identity():
    binding, plan, review = _bound_fixture()
    fabric = VerificationFabric()

    def fake_adapter(*, target, binding, formalization):
        assert binding.claim_id == "C-99"
        assert formalization.approved_for_formal_check is True
        return VerificationResult(
            target_backend=target.backend,
            kind=target.kind,
            verdict=TrustVerdict.FORMALLY_CHECKED,
            artifact_hash=binding.proof_artifact_hash,
            artifact_path=target.artifact_path,
            foundation=target.foundation,
            independent_group=target.independent_group,
            declaration=binding.declaration,
        )

    fabric.register("lean", fake_adapter)
    record = fabric.verify(binding=binding, plan=plan, formalization=review)
    assert len(record.results) == 1
    assert record.bindings_valid is True
    assert record.assurance_level == AssuranceLevel.D2_FORMALLY_CHECKED
