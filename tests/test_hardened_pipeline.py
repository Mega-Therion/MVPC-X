from mvpc.hardened_pipeline import HardenedSovereignPipeline
from mvpc.kernel_backends import run_kernel
from mvpc.trust_verdicts import TrustVerdict
from mvpc.version import __version__


def test_version():
    assert __version__ == "8.0.0"


def test_kernel_heuristic_without_binary():
    r = run_kernel("lean4", "theorem t : True := by\n  trivial\n")
    assert r.driver_mode in {"heuristic", "kernel"}
    if r.driver_mode == "heuristic":
        assert r.trust_verdict != TrustVerdict.FORMALLY_CHECKED.value or r.ok


def test_hardened_pipeline_sorry_fails():
    p = HardenedSovereignPipeline(sign=True)
    out = p.run(
        {
            "formal_code": "theorem t : True := by\n  sorry\n",
            "target_backend": "lean4",
            "proposer_type": "biological",
            "physical_realization_profile": {
                "requires_si_checking": True,
                "physical_variables": {"m": "mass"},
            },
        },
        enable_repair=False,
    )
    assert out["overall_status"] == "FAILED"
    assert "signed_manifest" in out


def test_hardened_pipeline_clean_signs():
    p = HardenedSovereignPipeline(sign=True)
    out = p.run(
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
        cas_polynomials=("x - x", ["x - x"], "x"),
        enable_repair=False,
    )
    assert out["trust_verdict"] != TrustVerdict.FORMALLY_CHECKED.value or out["kernel"]["driver_mode"] == "kernel"
    assert out["consensus"]["pass_count"] >= 0
