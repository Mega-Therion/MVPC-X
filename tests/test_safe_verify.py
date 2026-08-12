from mvpc.core.safe_verify import safe_verify_source


def test_detects_sorry():
    report = safe_verify_source("theorem t : True := by\n  sorry\n")
    assert not report.clean
    assert any(f.rule == "sorry" for f in report.findings)


def test_clean_trivial():
    report = safe_verify_source("theorem t : True := by\n  trivial\n")
    assert report.clean
