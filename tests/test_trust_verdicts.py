from mvpc.trust_verdicts import TrustVerdict, from_legacy, may_render_as_verified


def test_truth_implying_verdicts():
    assert TrustVerdict.FORMALLY_CHECKED.implies_truth
    assert TrustVerdict.COMPUTATION_VERIFIED.implies_truth
    assert not TrustVerdict.EXECUTION_OBSERVED.implies_truth
    assert not TrustVerdict.HUMAN_ATTESTED.implies_truth


def test_legacy_migration():
    assert from_legacy("VERIFIED") is TrustVerdict.FORMALLY_CHECKED
    assert from_legacy("CONDITIONAL") is TrustVerdict.EVIDENCE_SUPPORTED
    assert from_legacy("UNVERIFIED") is TrustVerdict.INCONCLUSIVE


def test_display_and_verified_gate():
    assert TrustVerdict.EVIDENCE_SUPPORTED.display_label() == "EVIDENCE_SUPPORTED"
    assert may_render_as_verified(TrustVerdict.FORMALLY_CHECKED)
    assert not may_render_as_verified(TrustVerdict.EXECUTION_OBSERVED)
