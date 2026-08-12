from mvpc.failure_record import (
    ContainmentScope,
    FailureCode,
    FailureRecord,
    QuarantineState,
)


def test_failure_record_immutable_shape():
    rec = FailureRecord(
        failure_code=FailureCode.ERR_HASH_DIVERGENCE,
        message="mid-run fingerprint changed",
        baseline_hash="a",
        observed_hash="b",
    )
    assert rec.remediation_required
    assert "Do not rewrite prior witnesses" in rec.remediation_required
    assert rec.hash()


def test_quarantine_blocks_publication():
    q = QuarantineState(scope=ContainmentScope.WORKSPACE, reason="divergence")
    assert q.blocks_publication()
