"""Tests for all verification backends."""
import pytest
from pathlib import Path
from mvpc.backends.lean import LeanBackend
from mvpc.backends.coq import CoqBackend
from mvpc.backends.isabelle import IsabelleBackend
from mvpc.backends.python import PythonBackend
from mvpc.backends.generic import GenericBackend
from mvpc.trust import Severity
from mvpc.explanations import get_explanation


def test_lean_backend_clean(fixtures_dir):
    """Clean Lean file should produce no VIOLATION findings from static analysis."""
    backend = LeanBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "clean.lean"))
    violations = [f for f in findings if f.severity == Severity.VIOLATION]
    assert len(violations) == 0
    assert len(evidence) > 0  # Should have static analysis evidence


def test_lean_backend_sorry(fixtures_dir):
    """Lean file with sorry should be flagged as VIOLATION."""
    backend = LeanBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "sorry.lean"))
    violations = [f for f in findings if f.severity == Severity.VIOLATION]
    assert len(violations) > 0
    assert any("SORRY" in f.code for f in violations)


def test_lean_backend_axiom_smuggle(fixtures_dir):
    """Lean file with axiom smuggling should be flagged."""
    backend = LeanBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "axiom_smuggle.lean"))
    assert len(findings) > 0
    assert any("AXIOM" in f.code for f in findings)


def test_lean_backend_audit(fixtures_dir):
    """Full audit should return findings, evidence, and coverage."""
    backend = LeanBackend()
    findings, evidence, coverage = backend.audit(str(fixtures_dir / "sorry.lean"))
    assert len(findings) > 0
    assert "Static Analysis" in coverage.checks_performed


def test_lean_backend_native_unavailable():
    """Method should execute without crashing."""
    backend = LeanBackend()
    native_available = backend.check_native_available()
    assert isinstance(native_available, bool)


def test_coq_backend_clean(fixtures_dir):
    """Clean Coq file should produce no VIOLATION findings."""
    backend = CoqBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "clean.v"))
    violations = [f for f in findings if f.severity == Severity.VIOLATION]
    assert len(violations) == 0


def test_coq_backend_admit(fixtures_dir):
    """Coq file with Admitted should be flagged."""
    backend = CoqBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "admit.v"))
    assert len(findings) > 0


def test_isabelle_backend_clean(fixtures_dir):
    """Clean Isabelle theory should produce no VIOLATION findings."""
    backend = IsabelleBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "clean.thy"))
    violations = [f for f in findings if f.severity == Severity.VIOLATION]
    assert len(violations) == 0


def test_isabelle_backend_sorry(fixtures_dir):
    """Isabelle theory with sorry should be flagged as VIOLATION."""
    backend = IsabelleBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "sorry.thy"))
    violations = [f for f in findings if f.severity == Severity.VIOLATION]
    assert len(violations) > 0
    assert any(f.code == "ISABELLE_SORRY" for f in violations)


def test_python_backend_clean(fixtures_dir):
    """Clean Python file should have no findings."""
    backend = PythonBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "clean.py"))
    violations = [f for f in findings if f.severity == Severity.VIOLATION]
    assert len(violations) == 0


def test_python_backend_unsafe(fixtures_dir):
    """Unsafe Python file with exec/eval should be flagged."""
    backend = PythonBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "unsafe.py"))
    assert len(findings) > 0


def test_python_backend_math_claims(fixtures_dir):
    """Math claims file should parse and verify without violations."""
    backend = PythonBackend()
    findings, evidence = backend.run_static_analysis(str(fixtures_dir / "math_claims.py"))
    violations = [f for f in findings if f.severity == Severity.VIOLATION]
    assert len(violations) == 0


def test_generic_backend(fixtures_dir):
    """Generic backend should hash and return evidence for any file."""
    backend = GenericBackend()
    findings, evidence, coverage = backend.audit(str(fixtures_dir / "generic.txt"))
    assert len(evidence) > 0
    assert evidence[0].artifact_hash is not None
    assert len(coverage.checks_unavailable) > 0


def test_backend_supports():
    """Backends should correctly identify supported file types."""
    lean = LeanBackend()
    coq = CoqBackend()
    isa = IsabelleBackend()
    py = PythonBackend()
    generic = GenericBackend()

    assert lean.supports("test.lean") is True
    assert lean.supports("test.py") is False
    assert coq.supports("test.v") is True
    assert coq.supports("test.lean") is False
    assert isa.supports("test.thy") is True
    assert isa.supports("ROOT") is True
    assert py.supports("test.py") is True
    assert py.supports("test.biomech") is True
    assert generic.supports("anything.txt") is True


def test_explanations_lookup():
    """All standard error codes should have explanation metadata."""
    codes = ["LEAN_SORRY", "COQ_ADMIT", "ISABELLE_SORRY", "PY_EXEC", "GENERIC_PLACEHOLDER"]
    for code in codes:
        exp = get_explanation(code)
        assert "title" in exp
        assert "explanation" in exp
        assert "action" in exp
