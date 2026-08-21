from __future__ import annotations

import json
from pathlib import Path

from mvpc.nexus.ast_normalizer import SourceLanguage, normalize_source
from mvpc.nexus.intake import dependency_parity, validate_mvpc_bin
from mvpc.nexus.manifest_ledger import PermanentManifestLedger
from mvpc.nexus.policy import (
    NexusVerdict,
    derive_native_verdict,
    evaluate_source_policy,
)

LEAN_SOURCE = """theorem identity (x : Nat) : x = x := by rfl
"""


def test_normalizer_preserves_formal_boundary_and_extracts_declaration() -> None:
    ast = normalize_source(LEAN_SOURCE, path="Identity.lean")
    assert ast.language is SourceLanguage.LEAN
    assert ast.translation_required is False
    assert ast.delimiter_balanced is True
    assert [node.name for node in ast.nodes] == ["identity"]

    informal = normalize_source("Every finite set has a cardinality.", path="claim.md")
    assert informal.language is SourceLanguage.NATURAL_LANGUAGE
    assert informal.translation_required is True
    decision = evaluate_source_policy(informal, "Every finite set has a cardinality.")
    assert decision.verdict is NexusVerdict.UNTRANSLATED


def test_pani_decision_does_not_depend_on_proposer_identity() -> None:
    # Proposer identity is intentionally absent from the policy API. Equivalent
    # source therefore yields the same result for a human, AI, or joint submitter.
    ast = normalize_source(LEAN_SOURCE, path="Identity.lean")
    human = evaluate_source_policy(ast, LEAN_SOURCE)
    synthetic = evaluate_source_policy(ast, LEAN_SOURCE)
    assert human == synthetic
    assert (
        derive_native_verdict(
            human, native_completed=True, backend_blockers=(), integrity_intact=True
        )
        is NexusVerdict.FORMALLY_VERIFIED
    )


def test_policy_rejects_placeholder_and_unbalanced_zone_markers() -> None:
    source = "theorem hole : True := by sorry\n-- EVOLVE-BLOCK-BEGIN helper\n"
    ast = normalize_source(source, path="Hole.lean")
    decision = evaluate_source_policy(ast, source)
    assert decision.verdict is NexusVerdict.REJECTED
    assert decision.zero_axiom_clean is False


def test_strict_mvpc_bin_requires_trusted_absolute_pinned_executable(
    tmp_path: Path,
) -> None:
    binary = tmp_path / "mvpc"
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o700)
    report = validate_mvpc_bin(str(binary), strict=True, trusted_roots=[tmp_path])
    assert report.allowed is False
    assert any("requires MVPC_BIN_SHA256" in reason for reason in report.reasons)

    pinned = validate_mvpc_bin(
        str(binary),
        strict=True,
        expected_sha256=report.sha256,
        trusted_roots=[tmp_path],
    )
    assert pinned.allowed is True
    assert pinned.hash_pinned is True


def test_mvpc_bin_rejects_symlink_and_dependency_parity_tracks_manifest_hashes(
    tmp_path: Path,
) -> None:
    target = tmp_path / "real-mvpc"
    target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    target.chmod(0o700)
    alias = tmp_path / "mvpc-link"
    alias.symlink_to(target)
    report = validate_mvpc_bin(str(alias), strict=False, trusted_roots=[tmp_path])
    assert report.allowed is False
    assert any("must not be a symlink" in reason for reason in report.reasons)

    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "DEPENDENCIES.md").write_text("stdlib only\n", encoding="utf-8")
    observed = dependency_parity(tmp_path)
    assert observed.matched is True
    pinned = dependency_parity(tmp_path, expected_digest=observed.digest)
    assert pinned.matched is True
    mismatch = dependency_parity(tmp_path, expected_digest="0" * 64)
    assert mismatch.matched is False


def test_permanent_ledger_links_pairs_and_detects_json_tampering(
    tmp_path: Path,
) -> None:
    ledger = PermanentManifestLedger(tmp_path / "ledger")
    first = ledger.append(
        status="CONDITIONAL",
        source_hash="a" * 64,
        payload={"language": "lean", "policy_verdict": "CONDITIONAL"},
    )
    second = ledger.append(
        status="FORMALLY_VERIFIED",
        source_hash="b" * 64,
        payload={"language": "lean", "native_completed": True},
    )
    assert second.manifest.previous_manifest_hash == first.manifest.manifest_hash
    assert ledger.verify() == []

    data = json.loads(Path(second.json_path).read_text(encoding="utf-8"))
    data["status"] = "REJECTED"
    Path(second.json_path).write_text(json.dumps(data), encoding="utf-8")
    assert any("manifest hash mismatch" in error for error in ledger.verify())
