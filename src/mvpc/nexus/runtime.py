"""End-to-end local Sovereign Nexus verification runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from mvpc.core.fingerprint import FingerprintSession

from .ast_normalizer import NormalizedAst, normalize_file
from .backend_array import BackendReceipt, LanguageAgnosticVerificationArray
from .glassbox import GlassBoxDocument, build_glassbox
from .intake import (
    BinaryTrustReport,
    DependencyParityReport,
    dependency_parity,
    validate_mvpc_bin,
)
from .manifest_ledger import ManifestPair, PermanentManifestLedger
from .policy import (
    NexusVerdict,
    PolicyDecision,
    derive_native_verdict,
    evaluate_source_policy,
)


@dataclass(frozen=True)
class NexusRunResult:
    ast: NormalizedAst
    policy: PolicyDecision
    backend: BackendReceipt
    binary_trust: BinaryTrustReport
    dependency_parity: DependencyParityReport
    fingerprints: dict[str, Any]
    final_verdict: NexusVerdict
    glassbox: GlassBoxDocument
    manifest_pair: ManifestPair | None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["ast"] = self.ast.to_dict()
        value["policy"] = self.policy.to_dict()
        value["backend"] = self.backend.to_dict()
        value["binary_trust"] = self.binary_trust.to_dict()
        value["dependency_parity"] = self.dependency_parity.to_dict()
        value["final_verdict"] = self.final_verdict.value
        value["glassbox"] = self.glassbox.to_dict()
        value["manifest_pair"] = (
            self.manifest_pair.to_dict() if self.manifest_pair else None
        )
        return value


class SovereignNexusRuntime:
    """Local-only orchestrator for normalized, evidence-backed verification."""

    def __init__(self, array: LanguageAgnosticVerificationArray | None = None) -> None:
        self.array = array or LanguageAgnosticVerificationArray()

    def inspect(
        self, path: str | Path, *, natural_language_plan: str = ""
    ) -> GlassBoxDocument:
        resolved = Path(path).resolve(strict=True)
        source = resolved.read_text(encoding="utf-8", errors="replace")
        ast = normalize_file(resolved)
        policy = evaluate_source_policy(ast, source)
        backend = self.array.inspect(ast)
        final = derive_native_verdict(
            policy,
            native_completed=False,
            backend_blockers=backend.blockers,
            integrity_intact=True,
        )
        return build_glassbox(
            natural_language_plan=natural_language_plan,
            formal_source=source,
            ast=ast,
            policy=policy,
            backend=backend,
            final_verdict=final,
        )

    def verify(
        self,
        path: str | Path,
        *,
        natural_language_plan: str = "",
        ledger_directory: str | Path | None = None,
        strict_external_binary: bool = False,
        expected_dependency_digest: str | None = None,
    ) -> NexusRunResult:
        """Verify a source locally and emit a linked permanent manifest.

        This method does not invoke network services. A caller-provided formal
        backend may execute only through MVPC-X's existing local backend wrappers.
        """
        resolved = Path(path).resolve(strict=True)
        source = resolved.read_text(encoding="utf-8", errors="replace")
        ast = normalize_file(resolved)
        policy = evaluate_source_policy(ast, source)
        binary_trust = validate_mvpc_bin(strict=strict_external_binary)
        parity = dependency_parity(expected_digest=expected_dependency_digest)
        extra_binaries = (
            [binary_trust.resolved_path] if binary_trust.resolved_path else []
        )
        session = FingerprintSession(extra_binaries=extra_binaries)
        session.capture_pre()

        # Invalid structural source and untranslated material are deliberately
        # not handed to an executable backend. This prevents the audit pathway
        # from treating a rejected proposal as an executable proof candidate.
        backend = self.array.audit(resolved, ast)
        session.capture_mid()
        session.capture_post()
        fingerprints = session.report()

        environment_blockers: list[str] = []
        if not binary_trust.allowed:
            environment_blockers.extend(binary_trust.reasons)
        if not parity.matched:
            environment_blockers.extend(parity.reasons)
        blockers = tuple(environment_blockers) + tuple(backend.blockers)
        final = derive_native_verdict(
            policy,
            native_completed=backend.native_completed and not environment_blockers,
            backend_blockers=blockers,
            integrity_intact=not session.voided,
        )
        glassbox = build_glassbox(
            natural_language_plan=natural_language_plan,
            formal_source=source,
            ast=ast,
            policy=policy,
            backend=backend,
            final_verdict=final,
        )
        ledger_dir = (
            Path(ledger_directory)
            if ledger_directory
            else resolved.parent / ".mvpc-nexus-ledger"
        )
        payload = {
            "language": ast.language.value,
            "policy_verdict": policy.verdict.value,
            "final_verdict": final.value,
            "native_completed": backend.native_completed,
            "integrity_intact": not session.voided,
            "binary_trust": binary_trust.to_dict(),
            "dependency_parity": parity.to_dict(),
            "fingerprints": fingerprints,
            "backend_receipt": backend.to_dict(),
            "policy": policy.to_dict(),
            "glassbox_traffic_light": glassbox.traffic_light.value,
        }
        pair = PermanentManifestLedger(ledger_dir).append(
            status=final.value,
            source_hash=ast.source_hash,
            payload=payload,
        )
        return NexusRunResult(
            ast=ast,
            policy=policy,
            backend=backend,
            binary_trust=binary_trust,
            dependency_parity=parity,
            fingerprints=fingerprints,
            final_verdict=final,
            glassbox=glassbox,
            manifest_pair=pair,
        )
