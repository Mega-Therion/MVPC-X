from __future__ import annotations

from pathlib import Path

from mvpc.nexus.ast_normalizer import normalize_file
from mvpc.nexus.backend_array import LanguageAgnosticVerificationArray
from mvpc.nexus.cas_certificate import (
    PolynomialCertificate,
    verify_polynomial_certificate,
)
from mvpc.nexus.manifest_ledger import PermanentManifestLedger
from mvpc.nexus.policy import NexusVerdict
from mvpc.nexus.runtime import SovereignNexusRuntime


def test_cas_certificate_checks_exact_polynomial_residual() -> None:
    valid = PolynomialCertificate.from_dict(
        {
            "variables": ["x"],
            "target": "x^2 - 1",
            "generators": ["x - 1"],
            "coefficients": ["x + 1"],
        }
    )
    result = verify_polynomial_certificate(valid)
    assert result.available is True
    assert result.valid is True
    assert result.residual == "0"
    assert "not formal-kernel proof" in result.reason

    invalid = PolynomialCertificate.from_dict(
        {
            "variables": ["x"],
            "target": "x^2",
            "generators": ["x - 1"],
            "coefficients": ["x + 1"],
        }
    )
    assert verify_polynomial_certificate(invalid).valid is False


def test_array_does_not_send_informal_material_to_kernel_backend(
    tmp_path: Path,
) -> None:
    path = tmp_path / "claim.tex"
    path.write_text(r"\[ x^2 + y^2 = z^2 \]", encoding="utf-8")
    ast = normalize_file(path)
    receipt = LanguageAgnosticVerificationArray().audit(path, ast)
    assert receipt.backend == "none"
    assert receipt.native_completed is False
    assert "Formal artifact required" in receipt.coverage["trust_boundaries"]


def test_runtime_emits_orange_untranslated_manifest_and_verified_ledger(
    tmp_path: Path,
) -> None:
    path = tmp_path / "proposal.md"
    path.write_text("Every prime greater than two is odd.", encoding="utf-8")
    output = tmp_path / "manifests"
    result = SovereignNexusRuntime().verify(
        path,
        natural_language_plan="Formalize the elementary number-theory proposal.",
        ledger_directory=output,
    )
    assert result.final_verdict is NexusVerdict.UNTRANSLATED
    assert result.glassbox.traffic_light.value == "orange"
    assert result.manifest_pair is not None
    assert Path(result.manifest_pair.json_path).is_file()
    assert Path(result.manifest_pair.markdown_path).is_file()
    assert PermanentManifestLedger(output).verify() == []


def test_runtime_rejects_unsound_formal_placeholder_and_marks_red(
    tmp_path: Path,
) -> None:
    path = tmp_path / "hole.lean"
    path.write_text("theorem hole : True := by sorry\n", encoding="utf-8")
    result = SovereignNexusRuntime().verify(
        path, ledger_directory=tmp_path / "manifests"
    )
    assert result.final_verdict is NexusVerdict.REJECTED
    assert result.glassbox.traffic_light.value == "red"
    assert result.backend.native_completed is False


def test_formal_source_without_native_tool_is_never_green(tmp_path: Path) -> None:
    path = tmp_path / "identity.lean"
    path.write_text("theorem identity (x : Nat) : x = x := by rfl\n", encoding="utf-8")
    result = SovereignNexusRuntime().verify(
        path, ledger_directory=tmp_path / "manifests"
    )
    if result.backend.native_completed:
        assert result.glassbox.traffic_light.value == "green"
        assert result.final_verdict is NexusVerdict.FORMALLY_VERIFIED
    else:
        assert result.glassbox.traffic_light.value == "orange"
        assert result.final_verdict is NexusVerdict.CONDITIONAL


def test_nexus_scaffold_initializes_formal_intent_cas_and_ledger_layout(
    tmp_path: Path,
) -> None:
    from mvpc.scaffold import scaffold

    written = scaffold("nexus", str(tmp_path / "workspace"))
    workspace = tmp_path / "workspace"
    assert len(written) == 5
    assert (workspace / "intent.md").is_file()
    assert (workspace / "formal" / "Basic.lean").is_file()
    assert (workspace / "cas" / "certificate.json").is_file()
    ledger = PermanentManifestLedger(workspace / "ledger" / "manifests")
    assert ledger.verify() == []


def test_inspect_never_runs_native_backend(tmp_path: Path) -> None:
    path = tmp_path / "preview.lean"
    path.write_text("theorem preview (n : Nat) : n = n := by rfl\n", encoding="utf-8")
    document = SovereignNexusRuntime().inspect(
        path, natural_language_plan="Preview only."
    )
    assert document.backend_receipt["native_completed"] is False
    assert document.backend_receipt["static_completed"] is False
    assert "never launches it" in document.backend_receipt["notes"][0]
