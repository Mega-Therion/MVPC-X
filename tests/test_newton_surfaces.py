"""Newton Architect coverage on the remaining surfaces.

Companion to test_newton_is_centerpiece.py (which pins the verification
pipeline). Five modules were audited for Newton gaps; two were real:

  preflight.py  — scored artifacts for readiness without checking for vacuous
                  proofs, so a file of `theorem X : True := trivial` was rated
                  READY_DEEP.
  witness.py    — dropped Policy.newton_enforced from the hashed policy record,
                  so witnesses that differed in whether Newton gated them were
                  hash-identical.

report.py (pure formatting of findings computed upstream), tcb.py (a
declaration surface), and scaffold.py (no verification logic — but its
templates must not themselves violate the protocol) needed no code change.
"""

from pathlib import Path

from mvpc.newton_architect import scan_artifact_text
from mvpc.policy import PolicyLevel, get_policy
from mvpc.preflight import Readiness, _score_lean, run_preflight
from mvpc.scaffold import list_templates, scaffold

VACUOUS_LEAN = "import Mathlib\n\ntheorem modularity_theorem : True := trivial\n"


# --- preflight ---------------------------------------------------------


def test_vacuous_lean_cannot_be_rated_ready_for_deep_audit(tmp_path):
    # Before the fix this scored 40 + 20 (has theorem) + 25 (lake) = 85.
    (tmp_path / "lakefile.lean").write_text("-- lake project\n")
    f = tmp_path / "Vacuous.lean"
    f.write_text(VACUOUS_LEAN)

    score, notes, recs = _score_lean(f, VACUOUS_LEAN)

    assert score < 60, f"score {score} still reaches READY_DEEP threshold"
    assert any("NEWTON_VACUOUS_PROOF" in n for n in notes)
    assert recs, "a violation must carry remediation advice"

    report = run_preflight(str(f))
    assert report.readiness is not Readiness.READY_DEEP


def test_clean_lean_file_is_not_penalised(tmp_path):
    # Guard against the penalty firing on everything.
    (tmp_path / "lakefile.lean").write_text("-- lake project\n")
    clean = "import Mathlib\n\ntheorem t (h : 1 = 1) : 1 = 1 := h\n"
    f = tmp_path / "Clean.lean"
    f.write_text(clean)

    score, notes, _ = _score_lean(f, clean)

    assert score >= 60
    assert not any("Newton" in n for n in notes)


# --- witness -----------------------------------------------------------


def test_witness_hash_distinguishes_newton_enforcement():
    strict = get_policy(PolicyLevel.DEFAULT)
    relaxed = get_policy(PolicyLevel.DEFAULT)
    relaxed.newton_enforced = False

    from mvpc.claim import create_claim
    from mvpc.provenance import Provenance, SourceType
    from mvpc.witness import generate_witness

    def w(policy):
        claim = create_claim(
            "test claim",
            origin=SourceType.MACHINE,
            scope="unit-test",
            definitions={},
            provenance=Provenance(
                source_type=SourceType.MACHINE,
                origin_description="test",
                timestamp="1970-01-01T00:00:00Z",
            ),
        )
        # Pin the id so the two witnesses differ only in Newton enforcement.
        claim.id = "CLAIM-FIXED"
        return generate_witness(claim, policy, environment={"host": "test"})

    a, b = w(strict), w(relaxed)

    assert a.policy["newton_enforced"] is True
    assert b.policy["newton_enforced"] is False

    # witness_id and timestamp are unique per witness, so raw hashes always
    # differ and would make this test pass even with the bug present. Null
    # both out so Newton enforcement is the ONLY remaining difference.
    for x in (a, b):
        x.witness_id = "W-FIXED"
        x.timestamp = "1970-01-01T00:00:00+00:00"
        x.recompute_hash()

    assert a.witness_hash != b.witness_hash, (
        "witness hash does not reflect newton_enforced — the self-verifying "
        "record cannot distinguish a gated run from an ungated one"
    )
    assert a.verify_integrity() and b.verify_integrity()

    # And prove the normalisation is what isolates it: with newton_enforced
    # forced equal, the two witnesses collide exactly.
    b.policy["newton_enforced"] = True
    b.recompute_hash()
    assert a.witness_hash == b.witness_hash


# --- scaffold ----------------------------------------------------------


def test_scaffolded_templates_do_not_violate_newton(tmp_path):
    # Templates are what users start from; shipping one that trips the
    # protocol would teach the violation. Checked against the live rules, so
    # a rule added later retroactively covers every template.
    for kind in list_templates():
        dest = tmp_path / kind
        for written in scaffold(kind, str(dest), force=True):
            p = Path(written)
            if not p.is_file():
                continue
            findings = scan_artifact_text(p.read_text(errors="replace"))
            assert not findings, (
                f"template {kind!r} file {p.name} violates Newton: "
                f"{[f.code for f in findings]}"
            )
