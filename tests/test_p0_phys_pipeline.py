from mvpc.cps_realization import CPSRealizationBridge
from mvpc.nexus_pipeline import SovereignNexusPipeline
from mvpc.phys.si_units import SIDimensionChecker
from mvpc.trust_verdicts import TrustVerdict


def test_si_force_equation():
    c = SIDimensionChecker()
    ok, msg = c.verify_equation("F", [("m", 1.0), ("a", 1.0)])
    assert ok, msg


def test_cps_bridge_violation():
    b = CPSRealizationBridge()
    r = b.audit_claim_physics(
        {"m": "mass", "v": "velocity"},
        trajectory_data=([0.0, 1.0], [1.0, 200.0], [300.0, 300.0]),
        max_velocity=50.0,
    )
    assert r["cps_safety_passed"] is False


def test_pipeline_sorry_fails():
    p = SovereignNexusPipeline()
    r = p.run_pipeline(
        {
            "formal_code": "theorem t : True := by\n  sorry\n",
            "target_backend": "lean4",
            "proposer_type": "biological",
            "physical_realization_profile": {
                "requires_si_checking": True,
                "physical_variables": {"m": "mass"},
            },
        }
    )
    assert r["overall_status"] == "FAILED"
    assert r["safe_verify_audit"]["passed"] is False


def test_pipeline_clean_not_formally_checked():
    p = SovereignNexusPipeline()
    r = p.run_pipeline(
        {
            "formal_code": "theorem t : True := by\n  trivial\n",
            "target_backend": "lean4",
            "proposer_type": "biological",
            "physical_realization_profile": {
                "requires_si_checking": True,
                "requires_cps_bounds": False,
                "physical_variables": {"m": "mass", "v": "velocity"},
            },
        },
        trajectory_data=([0.0, 1.0], [1.0, 2.0], [300.0, 301.0]),
    )
    assert r["trust_verdict"] != TrustVerdict.FORMALLY_CHECKED.value
    assert r["driver_mode"] == "heuristic"
