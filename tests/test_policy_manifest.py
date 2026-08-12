from mvpc.policy_manifest import template_default, template_strict
from mvpc.trust_verdicts import TrustVerdict


def test_strict_template():
    p = template_strict()
    errs = [e for e in p.validate() if not e.startswith("warning")]
    assert errs == []
    assert p.minimum_verdict is TrustVerdict.FORMALLY_CHECKED
    assert p.allows_backend("lean")
    assert not p.allows_backend("generic")
    assert p.hash()


def test_meets_minimum():
    p = template_default()
    assert p.meets_minimum(TrustVerdict.FORMALLY_CHECKED)
    assert not p.meets_minimum(TrustVerdict.INCONCLUSIVE)
