import pytest
import subprocess
import sys
import json
import os
from pathlib import Path


def test_cli_audit_clean_lean(fixtures_dir):
    """Test CLI audit on clean.lean."""
    res = subprocess.run(
        [sys.executable, "-m", "mvpc.cli", "audit", str(fixtures_dir / "clean.lean")],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "MVPC-X CLAIM ATTESTATION" in res.stdout
    assert "clean.lean" in res.stdout


def test_cli_audit_sorry_lean(fixtures_dir):
    """Test CLI audit on sorry.lean."""
    res = subprocess.run(
        [sys.executable, "-m", "mvpc.cli", "audit", str(fixtures_dir / "sorry.lean")],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "LEAN_SORRY" in res.stdout


def test_cli_audit_json(fixtures_dir):
    """Test CLI audit with JSON output."""
    res = subprocess.run(
        [sys.executable, "-m", "mvpc.cli", "audit", str(fixtures_dir / "clean.lean"), "--json"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert "id" in data
    assert "attestation_state" in data
    assert "coverage" in data


def test_cli_attest_workflow(tmp_path, fixtures_dir):
    """Test the complete human attestation workflow via CLI."""
    # 1. First audit and save JSON output to a witness file
    witness_path = tmp_path / "test_witness.json"
    audit_res = subprocess.run(
        [sys.executable, "-m", "mvpc.cli", "audit", str(fixtures_dir / "clean.py"), "--json"],
        capture_output=True,
        text=True
    )
    assert audit_res.returncode == 0
    claim_dict = json.loads(audit_res.stdout)
    witness_dict = claim_dict.get("provenance", {}).get("metadata", {}).get("witness", {})
    
    with open(witness_path, "w", encoding="utf-8") as f:
        json.dump(witness_dict, f, indent=2)

    # 2. Attach human attestation
    attest_res = subprocess.run(
        [
            sys.executable, "-m", "mvpc.cli", "attest", str(witness_path),
            "--signer", "Dr. Sovereign Reviewer",
            "--notes", "Formally reviewed and approved"
        ],
        capture_output=True,
        text=True
    )
    assert attest_res.returncode == 0
    assert "HUMAN ATTESTATION SEALED" in attest_res.stdout
    assert "Dr. Sovereign Reviewer" in attest_res.stdout

    # 3. Verify witness integrity
    verify_res = subprocess.run(
        [sys.executable, "-m", "mvpc.cli", "witness", "verify", str(witness_path)],
        capture_output=True,
        text=True
    )
    assert verify_res.returncode == 0
    assert "VALID" in verify_res.stdout


def test_cli_ci_mode_violation_exits_one(fixtures_dir):
    """In CI mode, violations should exit code 1."""
    res = subprocess.run(
        [sys.executable, "-m", "mvpc.cli", "audit", str(fixtures_dir / "sorry.lean"), "--ci-mode"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 1
