"""Tests for the RYTT adapters (issue #7): envelope, conformance-run
replay, and CLI ZIP bundle. Mirrors the depth of
tests/test_external_artifacts.py (4Leibniz/Res-Nova, issue #8).

Explicitly OUT of scope here and everywhere in mvpc.external_artifacts:
any Supabase connection, any network call, any live read of
rytt_traces/rytt_conformance_runs/rytt_benchmark_metrics. Every fixture
in this file is a local file; every test asserts local-file-only
behavior.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile

import pytest

from mvpc.external_artifacts.models import GateStatus
from mvpc.external_artifacts.registry import AdapterPolicy, UnsupportedArtifactError
from mvpc.external_artifacts.verify import (
    MalformedArtifactError,
    ZipArtifactError,
    verify_artifact_file,
    verify_zip_bundle_file,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "external_artifacts")
ADV = os.path.join(FIXTURES, "adversarial")


def fx(name: str) -> str:
    return os.path.join(FIXTURES, name)


def adv(name: str) -> str:
    return os.path.join(ADV, f"{name}.json")


def adv_zip(name: str) -> str:
    return os.path.join(ADV, f"{name}.zip")


# ---------------------------------------------------------------------------
# 1. Envelope adapter — valid case
# ---------------------------------------------------------------------------


def test_valid_rytt_envelope_passes():
    v = verify_artifact_file(fx("valid_rytt_envelope.json"))
    assert v.result.artifact_type == "rytt-envelope"
    assert v.result.schema_id == "rytt-envelope-v1"
    gate_names = {g.name for g in v.result.gates}
    assert {
        "schema_shape",
        "required_fields",
        "token_shape",
        "metrics_consistency",
        "round_trip_consistency",
        "vocabulary_hash",
    } <= gate_names
    # No expected_vocabulary_sha256 configured -> genuinely unchecked,
    # so the overall artifact cannot be a clean PASSED even though every
    # other gate passes.
    voc = next(g for g in v.result.gates if g.name == "vocabulary_hash")
    assert voc.status == GateStatus.UNAVAILABLE
    assert v.result.verdict == GateStatus.UNAVAILABLE


def test_valid_rytt_envelope_passes_with_configured_vocabulary_hash():
    with open(fx("valid_rytt_envelope.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    expected = data["vocabulary_sha256"]
    policy = AdapterPolicy(expected_vocabulary_sha256={"rytt-envelope": expected})
    v = verify_artifact_file(fx("valid_rytt_envelope.json"), policy=policy)
    voc = next(g for g in v.result.gates if g.name == "vocabulary_hash")
    assert voc.status == GateStatus.PASSED
    assert v.result.verdict == GateStatus.PASSED


# ---------------------------------------------------------------------------
# Adversarial: envelope
# ---------------------------------------------------------------------------


def test_rytt_unsupported_format_version_rejected():
    # format_version 0.2 must never resolve to the v1 identity at all.
    with pytest.raises(UnsupportedArtifactError):
        verify_artifact_file(adv("rytt_unsupported_format_version"))


def test_rytt_vocabulary_hash_unavailable_sentinel_never_passes():
    policy = AdapterPolicy(expected_vocabulary_sha256={"rytt-envelope": "a" * 64})
    v = verify_artifact_file(adv("rytt_vocabulary_hash_unavailable"), policy=policy)
    gate = next(g for g in v.result.gates if g.name == "vocabulary_hash")
    assert gate.status == GateStatus.UNAVAILABLE
    assert "unavailable" in gate.detail
    assert v.result.verdict != GateStatus.PASSED


def test_rytt_round_trip_mismatch_fails():
    v = verify_artifact_file(adv("rytt_round_trip_mismatch"))
    gate = next(g for g in v.result.gates if g.name == "round_trip_consistency")
    assert gate.status == GateStatus.FAILED
    assert v.result.verdict == GateStatus.FAILED


def test_rytt_metrics_mismatch_fails():
    v = verify_artifact_file(adv("rytt_metrics_mismatch"))
    gate = next(g for g in v.result.gates if g.name == "metrics_consistency")
    assert gate.status == GateStatus.FAILED
    assert v.result.verdict == GateStatus.FAILED


# ---------------------------------------------------------------------------
# 2. Conformance-run adapter — valid case
# ---------------------------------------------------------------------------


def test_valid_rytt_conformance_run_passes():
    v = verify_artifact_file(fx("valid_rytt_conformance_run.json"))
    assert v.result.artifact_type == "rytt-conformance-run"
    gate_names = {g.name for g in v.result.gates}
    assert {
        "schema_shape",
        "document_provenance",
        "vectors_reference_resolves",
        "vector_coverage",
        "declared_replay_matches_reference",
        "passed_flag_consistency",
        "summary_consistency",
    } <= gate_names
    assert v.result.verdict == GateStatus.PASSED
    resolves = next(g for g in v.result.gates if g.name == "vectors_reference_resolves")
    assert "7 vector(s)" in resolves.detail


# ---------------------------------------------------------------------------
# Adversarial: conformance run
# ---------------------------------------------------------------------------


def test_rytt_conformance_replay_mismatch_fails():
    """A declared-passed replay whose encoded_display doesn't actually
    match conformance/vectors.json must be caught, not trusted."""
    v = verify_artifact_file(adv("rytt_conformance_replay_mismatch"))
    gate = next(
        g for g in v.result.gates if g.name == "declared_replay_matches_reference"
    )
    assert gate.status == GateStatus.FAILED
    assert "symbols" in gate.detail
    assert v.result.verdict == GateStatus.FAILED


def test_rytt_conformance_missing_vector_fails_coverage():
    v = verify_artifact_file(adv("rytt_conformance_missing_vector"))
    gate = next(g for g in v.result.gates if g.name == "vector_coverage")
    assert gate.status == GateStatus.FAILED
    assert "whitespace" in gate.detail
    assert v.result.verdict == GateStatus.FAILED


def test_rytt_conformance_summary_mismatch_fails():
    v = verify_artifact_file(adv("rytt_conformance_summary_mismatch"))
    gate = next(g for g in v.result.gates if g.name == "summary_consistency")
    assert gate.status == GateStatus.FAILED
    assert v.result.verdict == GateStatus.FAILED


def test_rytt_conformance_passed_flag_lie_fails():
    v = verify_artifact_file(adv("rytt_conformance_passed_flag_lie"))
    gate = next(g for g in v.result.gates if g.name == "passed_flag_consistency")
    assert gate.status == GateStatus.FAILED
    assert "chord_rich" in gate.detail
    assert v.result.verdict == GateStatus.FAILED


def test_rytt_conformance_vectors_hash_mismatch_fails():
    v = verify_artifact_file(adv("rytt_conformance_vectors_hash_mismatch"))
    gate = next(g for g in v.result.gates if g.name == "vectors_reference_resolves")
    assert gate.status == GateStatus.FAILED
    assert "sha256" in gate.detail
    assert v.result.verdict == GateStatus.FAILED


# ---------------------------------------------------------------------------
# 3. ZIP bundle adapter — valid case
# ---------------------------------------------------------------------------


def test_valid_rytt_zip_bundle_passes():
    v = verify_zip_bundle_file(fx("valid_rytt_bundle.zip"))
    assert v.result.artifact_type == "rytt-zip-bundle"
    assert v.result.schema_id == "rytt-zip-bundle-v1"
    gate_names = {g.name for g in v.result.gates}
    assert {
        "required_members",
        "artifact_json_parses",
        "member_cross_consistency",
        "round_trip_consistency",
    } <= gate_names
    assert v.result.verdict == GateStatus.PASSED


# ---------------------------------------------------------------------------
# Adversarial: ZIP bundle (tamper detection)
# ---------------------------------------------------------------------------


def test_rytt_zip_tamper_pair_have_different_canonical_hash():
    """Mirrors test_tampered_payload_changes_canonical_hash for the JSON
    adapters: the original/modified ZIP pair must seal to different
    canonical hashes."""
    original = verify_zip_bundle_file(adv_zip("rytt_bundle_tamper_original"))
    modified = verify_zip_bundle_file(adv_zip("rytt_bundle_tamper_modified"))
    assert original.result.canonical_hash != modified.result.canonical_hash
    assert original.result.verdict == GateStatus.PASSED
    assert modified.result.verdict == GateStatus.FAILED
    gate = next(
        g for g in modified.result.gates if g.name == "member_cross_consistency"
    )
    assert gate.status == GateStatus.FAILED
    assert "trace.json" in gate.detail


def test_rytt_zip_missing_member_fails():
    v = verify_zip_bundle_file(adv_zip("rytt_bundle_missing_member"))
    gate = next(g for g in v.result.gates if g.name == "required_members")
    assert gate.status == GateStatus.FAILED
    assert "metrics.json" in gate.detail
    assert v.result.verdict == GateStatus.FAILED


def test_rytt_zip_duplicate_member_fails():
    v = verify_zip_bundle_file(adv_zip("rytt_bundle_duplicate_member"))
    gate = next(g for g in v.result.gates if g.name == "required_members")
    assert gate.status == GateStatus.FAILED
    assert "duplicate" in gate.detail.lower()
    assert v.result.verdict == GateStatus.FAILED


def test_rytt_zip_not_a_zip_raises_specific_error():
    with pytest.raises(ZipArtifactError):
        verify_zip_bundle_file(adv_zip("rytt_bundle_not_a_zip"))


def test_rytt_zip_path_traversal_member_rejected(tmp_path):
    evil = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr("../../etc/passwd", "not actually passwd")
        zf.writestr("artifact.json", "{}")
    with pytest.raises(ZipArtifactError):
        verify_zip_bundle_file(str(evil))


def test_rytt_zip_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        verify_zip_bundle_file(os.path.join(ADV, "does_not_exist.zip"))


# ---------------------------------------------------------------------------
# Registry / CLI auto-detection
# ---------------------------------------------------------------------------


def test_rytt_adapters_listed_in_registry():
    from mvpc.external_artifacts.registry import list_supported

    supported = list_supported()
    assert supported["rytt-envelope-v1"] == "rytt-envelope"
    assert supported["rytt-conformance-run-v1"] == "rytt-conformance-run"
    assert supported["rytt-zip-bundle-v1"] == "rytt-zip-bundle"


def _run_cli(args, cwd):
    env = dict(os.environ)
    src_root = os.path.join(os.path.dirname(__file__), "..", "src")
    env["PYTHONPATH"] = src_root + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "mvpc.cli", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def test_cli_auto_detects_zip_bundle(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    proc = _run_cli(
        [
            "verify",
            "artifact",
            fx("valid_rytt_bundle.zip"),
            "--format",
            "json",
            "--output",
            str(out_dir),
        ],
        cwd=str(tmp_path),
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == "passed"
    assert payload["artifact"]["type"] == "rytt-zip-bundle"


def test_cli_reports_zip_tamper_as_failure(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    proc = _run_cli(
        [
            "verify",
            "artifact",
            adv_zip("rytt_bundle_tamper_modified"),
            "--format",
            "json",
            "--output",
            str(out_dir),
        ],
        cwd=str(tmp_path),
    )
    assert proc.returncode == 1, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == "failed"


def test_cli_rytt_conformance_run_json_path(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    proc = _run_cli(
        [
            "verify",
            "artifact",
            fx("valid_rytt_conformance_run.json"),
            "--format",
            "json",
            "--output",
            str(out_dir),
        ],
        cwd=str(tmp_path),
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == "passed"
    assert payload["artifact"]["type"] == "rytt-conformance-run"


def test_existing_adapters_still_dispatch_after_resolve_identity_change():
    """Guard against the registry-level change in verify.py
    (_resolve_schema_identity) regressing the two issue #8 adapters."""
    v = verify_artifact_file(fx("valid_4leibniz.json"))
    assert v.result.artifact_type == "4leibniz-formal-claims-catalog"
    assert v.result.verdict == GateStatus.PASSED
    v2 = verify_artifact_file(fx("valid_resnova.json"))
    assert v2.result.artifact_type == "resnova-evidence-atlas"
    assert v2.result.verdict == GateStatus.PASSED
