from mvpc.sovereign_engine import SovereignNexusEngine
from mvpc.trust_verdicts import TrustVerdict


def _base_claim(code: str, claim_id: str = "t1") -> dict:
    return {
        "claim_id": claim_id,
        "proposer_type": "biological",
        "target_backend": "lean4",
        "formal_code": code,
        "physical_realization_profile": {
            "requires_si_checking": True,
            "requires_cps_bounds": True,
            "max_allowable_temperature": 400.0,
            "max_allowable_velocity": 200.0,
            "physical_variables": {"m": "mass", "v": "velocity"},
        },
        "lexical_zoning": {"evolve_block": ["helper_lemmas"], "evolve_value": ["hyperparameters"]},
    }


def test_sorry_fails_safe_verify():
    eng = SovereignNexusEngine()
    r = eng.process_and_verify(_base_claim("theorem t : True := by\n  sorry\n"))
    assert r["overall_status"] == "FAILED"
    assert r["safe_verify_audit"]["passed"] is False
    assert r["verification_result"]["has_unverified_axioms"] is True


def test_clean_heuristic_is_not_formally_checked():
    eng = SovereignNexusEngine()
    code = "theorem t : True := by\n  trivial\n"
    r = eng.process_and_verify(
        _base_claim(code, "t2"),
        trajectory_data=([0.0, 1.0], [1.0, 2.0], [300.0, 301.0]),
        cas_polynomials=("x**2 - y**2", ["x - y"], "x y"),
    )
    assert r["trust_verdict"] != TrustVerdict.FORMALLY_CHECKED.value
    assert r["driver_mode"] == "heuristic"
    assert "FORMALLY_CHECKED" in r["note"] or "kernel" in r["note"].lower()
    assert r["newton_architect"]["authority"] == "NEWTON ARCHITECT Protocol"


def test_cps_velocity_violation():
    eng = SovereignNexusEngine()
    claim = _base_claim("theorem t : True := by\n  trivial\n", "t3")
    claim["physical_realization_profile"]["max_allowable_velocity"] = 5.0
    r = eng.process_and_verify(
        claim,
        trajectory_data=([0.0, 1.0], [1.0, 50.0], [300.0, 300.0]),
    )
    assert r["cps_safety_certification"]["certified"] is False
    assert r["overall_status"] == "FAILED"


def test_ledger_chain_grows():
    eng = SovereignNexusEngine()
    eng.process_and_verify(_base_claim("theorem a : True := by trivial", "a"))
    eng.process_and_verify(_base_claim("theorem b : True := by trivial", "b"))
    assert len(eng.ledger.chain) == 2
    assert eng.ledger.chain[0].evidence_chain_hash != eng.ledger.chain[1].evidence_chain_hash


def test_newton_vacuous_proof_fails_sovereign():
    eng = SovereignNexusEngine()
    r = eng.process_and_verify(
        _base_claim("theorem sovereign_convergence : True := trivial", "newton-vacuous")
    )
    assert r["overall_status"] == "FAILED"
    assert r["newton_architect"]["passed"] is False
    assert any(f["code"] == "NEWTON_VACUOUS_PROOF" for f in r["newton_architect"]["findings"])
    assert r["trust_verdict"] == TrustVerdict.REJECTED.value
