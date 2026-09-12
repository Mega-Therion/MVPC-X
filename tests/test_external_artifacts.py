"""Tests for the external evidence artifact verifier (issue #8).

Covers: the two fixture-backed adapters (4Leibniz catalog, Res-Nova
Evidence Atlas), the registry's fail-closed unsupported-schema behavior,
canonical-hash and witness-bundle determinism, and the CLI surface.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from mvpc.external_artifacts.models import GateStatus
from mvpc.external_artifacts.registry import AdapterPolicy, UnsupportedArtifactError
from mvpc.external_artifacts.verify import (
    MalformedArtifactError,
    verify_artifact_file,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures", "external_artifacts")
ADV = os.path.join(FIXTURES, "adversarial")


def fx(name: str) -> str:
    return os.path.join(FIXTURES, name)


def adv(name: str) -> str:
    return os.path.join(ADV, f"{name}.json")


# ---------------------------------------------------------------------------
# Valid fixtures
# ---------------------------------------------------------------------------


def test_valid_4leibniz_catalog_passes():
    v = verify_artifact_file(fx("valid_4leibniz.json"))
    assert v.result.artifact_type == "4leibniz-formal-claims-catalog"
    assert v.result.verdict == GateStatus.PASSED
    assert v.result.provenance["repo"] == "Mega-Therion/4Leibniz"
    gate_names = {g.name for g in v.result.gates}
    assert "document_provenance" in gate_names
    assert "proved_claims_have_verification" in gate_names


def test_valid_resnova_atlas_passes():
    v = verify_artifact_file(fx("valid_resnova.json"))
    assert v.result.artifact_type == "resnova-evidence-atlas"
    assert v.result.verdict == GateStatus.PASSED
    # every declared epistemic status in the fixture must appear among the
    # per-status gates, and none may be silently excluded from the sealed
    # payload.
    statuses = {c["epistemic_status"] for c in v.raw["claims"]}
    assert statuses == {
        "derived",
        "empirically_supported",
        "conditional",
        "proposal",
        "open",
        "refuted",
    }
    preserved = v.bundle.witness.backend_result["claims_preserved"]
    assert {c["claim_id"] for c in preserved} == {
        c["claim_id"] for c in v.raw["claims"]
    }


# ---------------------------------------------------------------------------
# Adversarial case 1: unsupported schema version
# ---------------------------------------------------------------------------


def test_unsupported_schema_version_rejected():
    with pytest.raises(UnsupportedArtifactError):
        verify_artifact_file(adv("unsupported_schema_version"))


# Case 2: unsupported artifact type entirely


def test_unsupported_artifact_type_rejected():
    with pytest.raises(UnsupportedArtifactError):
        verify_artifact_file(adv("unsupported_artifact_type"))


# Case 3: missing document provenance


def test_missing_document_provenance_fails():
    v = verify_artifact_file(adv("missing_document_provenance"))
    prov_gate = next(g for g in v.result.gates if g.name == "document_provenance")
    assert prov_gate.status == GateStatus.FAILED
    assert v.result.verdict == GateStatus.FAILED
    # The claim-provenance-agreement gate's repo-comparison half never had
    # a document repo to compare against; it must report NOT_APPLICABLE,
    # never a silent PASSED, for the half that did not run.
    agreement = next(
        g for g in v.result.gates if g.name == "claim_provenance_agreement"
    )
    assert agreement.status == GateStatus.NOT_APPLICABLE


# Case 4: invalid commit SHA length/format


def test_invalid_commit_sha_fails():
    v = verify_artifact_file(adv("invalid_commit_sha"))
    prov_gate = next(g for g in v.result.gates if g.name == "document_provenance")
    assert prov_gate.status == GateStatus.FAILED
    assert "40-character hex" in prov_gate.detail


# Case 5: claim-level provenance mismatch


def test_claim_provenance_mismatch_fails():
    v = verify_artifact_file(adv("claim_provenance_mismatch"))
    gate = next(g for g in v.result.gates if g.name == "claim_provenance_agreement")
    assert gate.status == GateStatus.FAILED
    assert v.result.verdict == GateStatus.FAILED


# Case 6: tampered payload / hash mismatch


def test_tampered_payload_changes_canonical_hash():
    original = verify_artifact_file(adv("tamper_original"))
    modified = verify_artifact_file(adv("tamper_modified"))
    assert original.result.canonical_hash != modified.result.canonical_hash


def test_tamper_detected_against_sealed_witness(tmp_path):
    """The real tamper-detection scenario: seal a witness bundle for an
    artifact, then mutate the artifact on disk and re-verify. The
    previously sealed witness's claim_hash must no longer match the
    freshly recomputed canonical hash — this is how a consumer of a
    sealed bundle detects that the artifact underneath it changed."""
    original_path = tmp_path / "artifact.json"
    original_path.write_text(json.dumps(json.load(open(adv("tamper_original")))))

    sealed = verify_artifact_file(str(original_path))
    sealed_claim_hash = sealed.bundle.witness.claim_hash

    # Mutate the artifact on disk (simulating tampering after sealing).
    data = json.load(open(adv("tamper_modified")))
    original_path.write_text(json.dumps(data))

    recomputed = verify_artifact_file(str(original_path))

    assert sealed_claim_hash != recomputed.result.canonical_hash
    assert (
        sealed.bundle.witness.claim_hash == sealed_claim_hash
    )  # sealed record itself is immutable


# Case 7: missing source locator


def test_missing_source_locator_fails():
    v = verify_artifact_file(adv("missing_source_locator"))
    gate = next(g for g in v.result.gates if g.name == "source_locators_present")
    assert gate.status == GateStatus.FAILED
    assert v.result.verdict == GateStatus.FAILED


# Case 8: 4Leibniz proved claim lacking required verification record


def test_proved_lacking_verification_fails():
    v = verify_artifact_file(adv("proved_lacking_verification"))
    gate = next(
        g for g in v.result.gates if g.name == "proved_claims_have_verification"
    )
    assert gate.status == GateStatus.FAILED
    assert "verification record is empty/missing" in gate.detail


# Case 9: 4Leibniz proved claim with failed check incorrectly asserted passed


def test_proved_with_failed_check_fails():
    v = verify_artifact_file(adv("proved_with_failed_check"))
    gate = next(
        g for g in v.result.gates if g.name == "proved_claims_have_verification"
    )
    assert gate.status == GateStatus.FAILED
    assert v.result.verdict == GateStatus.FAILED


# Case 10: Res-Nova derived claim lacking required derivation evidence


def test_derived_lacking_evidence_fails():
    v = verify_artifact_file(adv("derived_lacking_evidence"))
    gate = next(
        g for g in v.result.gates if g.name == "derived_requires_derivation_evidence"
    )
    assert gate.status == GateStatus.FAILED


# Case 11: Res-Nova empirically_supported claim lacking test scope/result/data evidence


def test_empirically_supported_lacking_test_fails():
    v = verify_artifact_file(adv("empirically_supported_lacking_test"))
    gate = next(
        g
        for g in v.result.gates
        if g.name == "empirically_supported_requires_test_record"
    )
    assert gate.status == GateStatus.FAILED


# Case 12: an open claim retained without being promoted


def test_open_claim_not_promoted():
    v = verify_artifact_file(adv("open_claim_retained"))
    open_claims = [c for c in v.raw["claims"] if c["epistemic_status"] == "open"]
    assert open_claims, "fixture must contain an open claim"
    # the raw status is preserved verbatim; nothing rewrites it to derived/passed.
    preserved = v.bundle.witness.backend_result["claims_preserved"]
    preserved_open = [
        c for c in preserved if c["claim_id"] == open_claims[0]["claim_id"]
    ]
    assert preserved_open[0]["epistemic_status"] == "open"
    gate = next(
        g for g in v.result.gates if g.name == "open_identifies_unresolved_problem"
    )
    assert gate.status == GateStatus.PASSED


# Case 13: a refuted claim retained without being dropped


def test_refuted_claim_retained_not_dropped():
    v = verify_artifact_file(adv("refuted_claim_retained"))
    refuted = [c for c in v.raw["claims"] if c["epistemic_status"] == "refuted"]
    assert refuted, "fixture must contain a refuted claim"
    preserved_ids = {
        c["claim_id"] for c in v.bundle.witness.backend_result["claims_preserved"]
    }
    assert refuted[0]["claim_id"] in preserved_ids
    gate = next(g for g in v.result.gates if g.name == "refuted_retained_with_evidence")
    assert gate.status == GateStatus.PASSED


# Case 14: a skipped / not_applicable gate is never rendered as passed


def test_not_applicable_gate_never_rendered_as_passed(tmp_path):
    # A catalog with zero proved claims must show NOT_APPLICABLE, not
    # PASSED, for the proved-claims gate, and that must not silently flip
    # the overall verdict to failed either.
    with open(fx("valid_4leibniz.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    for c in data["claims"]:
        c["status"] = "informal"
        c["verification"] = {}
    artifact_path = tmp_path / "no_proved.json"
    artifact_path.write_text(json.dumps(data))

    v2 = verify_artifact_file(str(artifact_path))
    gate = next(
        g for g in v2.result.gates if g.name == "proved_claims_have_verification"
    )
    assert gate.status == GateStatus.NOT_APPLICABLE
    assert gate.status != GateStatus.PASSED
    assert (
        v2.result.verdict == GateStatus.PASSED
    )  # NOT_APPLICABLE here must not fail the artifact


# Case 15: deterministic canonical hash for semantically identical inputs


def test_canonical_hash_deterministic_across_key_order():
    v1 = verify_artifact_file(fx("valid_4leibniz.json"))
    v2 = verify_artifact_file(fx("valid_4leibniz_reordered.json"))
    assert v1.result.canonical_hash == v2.result.canonical_hash


# Case 16: deterministic witness bundle identity/results (timestamps aside)


def test_witness_bundle_deterministic_modulo_timestamps():
    """Two semantically identical inputs (same content, different JSON key
    order) must seal to byte-identical witness bundle identity: same
    witness_id (content-derived), same witness/tcb/policy hashes, and the
    same manifest_hash()/composite_hash(). This is the real determinism
    claim — not just "the two dicts are equal after we strip fields" but
    "the actual sealed identity hashes match"."""
    v1 = verify_artifact_file(fx("valid_4leibniz.json"))
    v2 = verify_artifact_file(fx("valid_4leibniz_reordered.json"))

    assert v1.result.canonical_hash == v2.result.canonical_hash
    assert v1.bundle.witness.witness_id == v2.bundle.witness.witness_id
    assert v1.bundle.witness.hash() == v2.bundle.witness.hash()
    assert v1.bundle.tcb.hash() == v2.bundle.tcb.hash()
    assert v1.bundle.policy.hash() == v2.bundle.policy.hash()
    assert v1.bundle.manifest_hash() == v2.bundle.manifest_hash()
    assert v1.bundle.composite_hash() == v2.bundle.composite_hash()
    assert v1.bundle.witness.to_dict() == v2.bundle.witness.to_dict()


# Case 17: CLI output and exit codes for both passing and failing cases


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


def test_cli_verify_artifact_passing_case(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    proc = _run_cli(
        [
            "verify",
            "artifact",
            fx("valid_4leibniz.json"),
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
    written = list(out_dir.iterdir())
    assert len(written) == 1


def test_cli_verify_artifact_failing_case(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    proc = _run_cli(
        [
            "verify",
            "artifact",
            adv("missing_document_provenance"),
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


def test_cli_verify_artifact_unsupported_schema_exit_code(tmp_path):
    proc = _run_cli(
        ["verify", "artifact", adv("unsupported_schema_version"), "--format", "json"],
        cwd=str(tmp_path),
    )
    assert proc.returncode == 2
    assert "unsupported artifact schema identity" in proc.stderr


def test_cli_does_not_overwrite_by_default(tmp_path):
    target = tmp_path / "existing.json"
    target.write_text("{}")
    proc = _run_cli(
        [
            "verify",
            "artifact",
            fx("valid_4leibniz.json"),
            "--format",
            "json",
            "--output",
            str(target),
        ],
        cwd=str(tmp_path),
    )
    # --output naming an existing, non-directory path directly must refuse
    # to clobber it without --overwrite.
    assert proc.returncode == 2, proc.stderr
    assert "already exists" in proc.stderr
    assert target.read_text() == "{}"  # untouched

    # Same guard again, this time via the --output-is-a-directory path:
    # run twice into the same directory and confirm the second run is
    # refused (since the deterministic filename collides for identical
    # input) unless --overwrite is passed.
    out_dir = tmp_path / "out2"
    out_dir.mkdir()
    proc1 = _run_cli(
        [
            "verify",
            "artifact",
            fx("valid_4leibniz.json"),
            "--format",
            "json",
            "--output",
            str(out_dir),
        ],
        cwd=str(tmp_path),
    )
    assert proc1.returncode == 0
    written = list(out_dir.iterdir())
    assert len(written) == 1
    existing_witness = written[0]

    # Re-running against the exact same file path (not a directory) must
    # refuse without --overwrite.
    proc2 = _run_cli(
        [
            "verify",
            "artifact",
            fx("valid_4leibniz.json"),
            "--format",
            "json",
            "--output",
            str(existing_witness),
        ],
        cwd=str(tmp_path),
    )
    assert proc2.returncode == 2
    assert "already exists" in proc2.stderr

    proc3 = _run_cli(
        [
            "verify",
            "artifact",
            fx("valid_4leibniz.json"),
            "--format",
            "json",
            "--output",
            str(existing_witness),
            "--overwrite",
        ],
        cwd=str(tmp_path),
    )
    assert proc3.returncode == 0


def test_malformed_json_rejected():
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write("{not valid json")
        path = f.name
    try:
        with pytest.raises(MalformedArtifactError):
            verify_artifact_file(path)
    finally:
        os.remove(path)


def test_policy_can_require_repo_match():
    policy = AdapterPolicy(
        expected_repos={"4leibniz-formal-claims-catalog": "Someone/Else"}
    )
    v = verify_artifact_file(fx("valid_4leibniz.json"), policy=policy)
    gate = next(g for g in v.result.gates if g.name == "document_provenance")
    assert gate.status == GateStatus.FAILED
