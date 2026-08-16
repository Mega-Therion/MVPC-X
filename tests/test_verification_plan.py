import pytest

from mvpc.verification_plan import CheckKind, VerificationPlan, VerificationTarget


def test_plan_is_claim_centric_and_supports_multiple_backends():
    plan = VerificationPlan("claim-001")
    plan.add(VerificationTarget("lean", CheckKind.FORMAL, required=True, independent_group="dependent-type"))
    plan.add(VerificationTarget("sympy", CheckKind.COMPUTATION))
    plan.add(VerificationTarget("rocq", CheckKind.FORMAL, independent_group="cic"))

    assert plan.formal_backends() == ("lean", "rocq")
    assert plan.independent_formal_groups() == frozenset({"dependent-type", "cic"})
    assert not plan.satisfies({"sympy"})
    assert plan.satisfies({"lean"})


def test_duplicate_target_is_rejected():
    plan = VerificationPlan("claim-002")
    plan.add(VerificationTarget("lean", CheckKind.FORMAL))
    with pytest.raises(ValueError):
        plan.add(VerificationTarget("lean", CheckKind.FORMAL))
