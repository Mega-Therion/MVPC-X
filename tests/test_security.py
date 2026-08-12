"""System self-integrity and intake guards."""
import os
from pathlib import Path

from mvpc.security import (
    IntegritySession,
    compute_system_fingerprint,
    validate_intake,
    hash_file,
    diff_system_fingerprints,
)


def test_system_fingerprint_stable():
    a = compute_system_fingerprint()
    b = compute_system_fingerprint()
    assert a["system_fingerprint"] == b["system_fingerprint"]
    assert a["file_count"] > 0
    assert len(a["system_fingerprint"]) == 64


def test_integrity_session_roundtrip_no_artifact():
    s = IntegritySession.begin(None)
    assert s.check_mid() is True
    assert s.finalize() is True
    assert s.system_intact is True
    d = s.to_dict()
    assert d["system_ok_after"] is True


def test_integrity_session_artifact_stable(tmp_path: Path):
    p = tmp_path / "a.lean"
    p.write_text("theorem t : True := by trivial\n", encoding="utf-8")
    s = IntegritySession.begin(str(p))
    assert s.artifact_hash_before == hash_file(str(p))
    s.check_mid()
    assert s.finalize() is True
    assert s.artifact_ok is True


def test_artifact_mutation_detected(tmp_path: Path):
    p = tmp_path / "a.lean"
    p.write_text("theorem t : True := by trivial\n", encoding="utf-8")
    s = IntegritySession.begin(str(p))
    p.write_text("theorem t : True := by sorry\n", encoding="utf-8")
    s.finalize()
    assert s.artifact_ok is False


def test_intake_rejects_missing():
    d = validate_intake("/no/such/path/mvpc_test_xyz")
    assert d.allowed is False


def test_intake_allows_normal_file(tmp_path: Path):
    p = tmp_path / "ok.lean"
    p.write_text("-- hi\n", encoding="utf-8")
    d = validate_intake(str(p))
    assert d.allowed is True


def test_intake_blocks_exe(tmp_path: Path):
    p = tmp_path / "evil.exe"
    p.write_bytes(b"MZ")
    d = validate_intake(str(p))
    assert d.allowed is False
    assert any("Blocked extension" in r for r in d.reasons)


def test_diff_fingerprints_detects_change():
    before = {
        "files": [{"path": "a.py", "sha256": "11"}, {"path": "b.py", "sha256": "22"}]
    }
    after = {
        "files": [{"path": "a.py", "sha256": "99"}, {"path": "b.py", "sha256": "22"}]
    }
    msgs = diff_system_fingerprints(before, after)
    assert any("MODIFIED a.py" in m for m in msgs)
