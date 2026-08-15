"""Newton Architect is the source authority: no verification path may bypass it.

The engine/policy path enforced Newton, but the nexus -> hardened pipeline did
not import it at all. That made the "high-assurance multi-prover" path the
weakest one: an artifact blocked by mvpc.policy could still reach
EVIDENCE_SUPPORTED through nexus. These tests pin the gate shut.
"""

import mvpc.nexus_pipeline as nexus
from mvpc.newton_architect import AUTHORITY, scan_artifact_text
from mvpc.nexus_pipeline import SovereignNexusPipeline

# Each of these trips exactly one Newton rule.
VACUOUS_LEAN = "theorem modularity : True := trivial\n"
A0_OVERCLAIM = "[P] a0 = c * H0 / (2 * pi) is derived exactly.\n"


def _run(code: str):
    # run_pipeline ingests the raw dict itself.
    return SovereignNexusPipeline().run_pipeline(
        {"formal_code": code, "target_backend": "lean4"}
    )


def test_newton_actually_fires_on_these_fixtures():
    # Guard the guard: if the rules stop matching, the tests below would pass
    # vacuously and we'd never know the gate had come open.
    assert scan_artifact_text(VACUOUS_LEAN), "vacuous-proof rule stopped matching"
    assert scan_artifact_text(A0_OVERCLAIM), "a0 overclaim rule stopped matching"


def test_nexus_pipeline_imports_newton():
    assert hasattr(nexus, "scan_artifact_text"), "nexus lost its Newton import"


def test_vacuous_lean_placeholder_cannot_pass_nexus():
    result = _run(VACUOUS_LEAN)
    assert not result["verification_result"]["heuristic_pass"]
    assert "NEWTON_VACUOUS_PROOF" in result["verification_result"]["axioms_used"]


def test_a0_overclaim_cannot_pass_nexus():
    result = _run(A0_OVERCLAIM)
    assert not result["verification_result"]["heuristic_pass"]
    assert "NEWTON_A0_OVERCLAIM" in result["verification_result"]["axioms_used"]


def test_manifest_records_the_governing_authority():
    result = _run("theorem t (h : 1 = 1) : 1 = 1 := h\n")
    assert result["immutable_evidence_manifest"]["newton_authority"] == AUTHORITY
