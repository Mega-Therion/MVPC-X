"""Adapters from legacy verification backends to the claim-centric fabric."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .backends.registry import BackendRegistry, get_default_registry
from .claim_binding import ClaimBinding
from .verification_plan import VerificationResult, VerificationTarget
from .formalization import FormalizationReview
from .trust_verdicts import TrustVerdict
from .verification_plan import CheckKind


def registry_adapter(registry: BackendRegistry, backend_name: str):
    """Return a fabric adapter backed by an existing MVPC-X backend."""
    backend = None
    for candidate in registry.backends:
        if candidate.name().lower() == backend_name.lower():
            backend = candidate
            break
    if backend is None:
        raise KeyError(f"unknown backend: {backend_name}")

    def adapter(*, target: VerificationTarget, binding: ClaimBinding, formalization: FormalizationReview | None = None) -> VerificationResult:
        if not target.artifact_path:
            return VerificationResult(
                target_backend=target.backend,
                kind=target.kind,
                verdict=TrustVerdict.INCONCLUSIVE,
                foundation=target.foundation,
                independent_group=target.independent_group,
                message="artifact_path required for backend execution",
            )
        findings, evidence, coverage = backend.audit(target.artifact_path)
        violations = [f for f in findings if getattr(f.severity, "name", "") == "VIOLATION"]
        native = any(getattr(e.evidence_type, "name", "") == "NATIVE_VERIFICATION" for e in evidence)
        if target.kind is CheckKind.FORMAL and native and not violations:
            verdict = TrustVerdict.FORMALLY_CHECKED
        elif violations:
            verdict = TrustVerdict.REJECTED
        else:
            verdict = TrustVerdict.COMPUTATION_VERIFIED if evidence else TrustVerdict.INCONCLUSIVE
        artifact_hash = next((getattr(e, "artifact_hash", None) for e in evidence if getattr(e, "artifact_hash", None)), None)
        message = "; ".join(getattr(f, "message", str(f)) for f in findings)
        environment_id = None
        if evidence:
            environment_id = str(evidence[-1].metadata or {})
        return VerificationResult(
            target_backend=target.backend,
            kind=target.kind,
            verdict=verdict,
            artifact_hash=artifact_hash,
            artifact_path=target.artifact_path,
            foundation=target.foundation,
            independent_group=target.independent_group,
            declaration=binding.declaration,
            environment_id=environment_id,
            message=message or "Backend completed without findings.",
        )

    return adapter


def register_default_backends(fabric: Any, registry: BackendRegistry | None = None) -> Any:
    registry = registry or get_default_registry()
    for backend in registry.backends:
        fabric.register(backend.name(), registry_adapter(registry, backend.name()))
    return fabric
