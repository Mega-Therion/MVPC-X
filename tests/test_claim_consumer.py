from mvpc.claim_consumer import judge_bundle
from mvpc.assurance import AssuranceLevel


def _claim(tier="[P]", status="VERIFIED", pass_val=True, artifacts=None, verification=None):
    return {
        "claim_id": "test",
        "epistemic_tier": tier,
        "status": status,
        "statement": "test proposition",
        "formal_proposition": "test proposition",
        "artifacts": artifacts or [{"path": "fake.lean", "sha256": "sha256:fake"}],
        "verification": verification or {
            "prover": "lean4",
            "pass": pass_val,
            "mathlib_pin": "5eec30bc",
            "gate_script": "verify.sh",
            "axiom_footprint": ["propext", "Classical.choice", "Quot.sound"],
        },
    }


def _bundle(claims):
    return {"source_repository": "test", "claims": claims}


def test_proved_claim_gets_d2_not_d3():
    """A [P] claim with no hardening metadata cannot exceed D2."""
    claim = _claim()
    claim["verification"].pop("axiom_footprint", None)
    claim["verification"].pop("gate_script", None)
    results = judge_bundle(_bundle([claim]))
    assert results[0]["assurance_level"] == "D2_FORMALLY_CHECKED"


def test_open_claim_stays_d0():
    """An [O] claim must not climb past D0/D1."""
    claim = _claim(tier="[O]", status="OPEN", pass_val=False)
    results = judge_bundle(_bundle([claim]))
    assert results[0]["assurance_value"] <= int(AssuranceLevel.D1_REPRODUCIBLY_COMPUTED)


def test_suspended_claim_stays_d0():
    """A suspended [O] claim must not get any assurance."""
    claim = _claim(tier="[O]", status="SUSPENDED", pass_val=False)
    results = judge_bundle(_bundle([claim]))
    assert results[0]["assurance_level"] == "D0_PROPOSED"


def test_phantom_module_cannot_get_formal():
    """A claim whose artifact hash is 'unknown' cannot be formal evidence."""
    claim = _claim(artifacts=[{"path": "Phantom.lean", "sha256": "unknown"}])
    results = judge_bundle(_bundle([claim]))
    assert results[0]["assurance_level"] in ("D1_REPRODUCIBLY_COMPUTED", "D0_PROPOSED")


def test_local_pass_is_not_publication_grade():
    """A single local Lean pass with hardening metadata is at most D3, never D6."""
    claim = _claim()
    results = judge_bundle(_bundle([claim]))
    assert int(results[0]["assurance_value"]) <= int(AssuranceLevel.D3_HARDENED_FORMAL)
    assert results[0]["assurance_level"] != "D6_PUBLICATION_GRADE"
