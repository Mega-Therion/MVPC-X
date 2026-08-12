"""Preflight readiness tests."""
from mvpc.preflight import run_preflight, Readiness, format_preflight_terminal
from mvpc.scaffold import scaffold, list_templates


def test_preflight_sorry_lean(fixtures_dir):
    r = run_preflight(str(fixtures_dir / "sorry.lean"))
    assert r.intake_allowed is True
    assert "Lean" in r.backend_name
    assert r.structure_score < 100
    assert any("sorry" in n.lower() for n in r.structure_notes)


def test_preflight_clean_lean(fixtures_dir):
    r = run_preflight(str(fixtures_dir / "clean.lean"))
    assert r.intake_allowed is True
    assert r.structure_score >= 40
    text = format_preflight_terminal(r)
    assert "PREFLIGHT" in text


def test_preflight_generic(fixtures_dir):
    r = run_preflight(str(fixtures_dir / "generic.txt"))
    assert r.readiness in {
        Readiness.GENERIC_ONLY,
        Readiness.TEMPLATE_SUGGESTED,
    }


def test_scaffold_lean(tmp_path):
    assert "lean" in list_templates()
    written = scaffold("lean", str(tmp_path / "out"))
    assert any(p.endswith("Basic.lean") for p in written)
    r = run_preflight(written[0])
    assert r.intake_allowed is True
