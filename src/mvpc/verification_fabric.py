"""End-to-end claim verification orchestration.

This is intentionally conservative: backend output becomes evidence only after
its result is explicitly associated with a VerificationTarget. AI providers can
produce candidate proof artifacts, but they do not emit FORMALLY_CHECKED.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .claim_binding import ClaimBinding
from .formalization import FormalizationReview
from .proof_record import ProofRecord
from .trust_verdicts import TrustVerdict
from .verification_plan import VerificationPlan, VerificationResult


@dataclass(frozen=True)
class BackendExecution:
    backend: str
    kind: str
    run: Callable[[str], VerificationResult]


class VerificationFabric:
    """Execute a claim's explicit plan against available verification adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, Callable[..., VerificationResult]] = {}

    def register(
        self,
        backend: str,
        adapter: Callable[..., VerificationResult],
    ) -> None:
        key = backend.strip().lower()
        if not key:
            raise ValueError("backend must not be empty")
        self._adapters[key] = adapter

    def verify(
        self,
        *,
        binding: ClaimBinding,
        plan: VerificationPlan,
        formalization: FormalizationReview | None = None,
    ) -> ProofRecord:
        if binding.claim_id != plan.claim_id:
            raise ValueError("claim_id mismatch between binding and verification plan")
        if formalization is not None and formalization.claim_id != binding.claim_id:
            raise ValueError("claim_id mismatch between binding and formalization review")

        results: list[VerificationResult] = []
        for target in plan.targets:
            adapter = self._adapters.get(target.backend.lower())
            if adapter is None:
                results.append(
                    VerificationResult(
                        target_backend=target.backend,
                        kind=target.kind,
                        verdict=TrustVerdict.INCONCLUSIVE,
                        artifact_path=target.artifact_path,
                        foundation=target.foundation,
                        independent_group=target.independent_group,
                        message="Backend adapter unavailable; no verification authority asserted.",
                    )
                )
                continue
            if target.artifact_path is None:
                results.append(
                    VerificationResult(
                        target_backend=target.backend,
                        kind=target.kind,
                        verdict=TrustVerdict.INCONCLUSIVE,
                        foundation=target.foundation,
                        independent_group=target.independent_group,
                        message="Target has no artifact path for adapter execution.",
                    )
                )
                continue
            try:
                result = adapter(target=target, binding=binding, formalization=formalization)
            except Exception as exc:
                result = VerificationResult(
                    target_backend=target.backend,
                    kind=target.kind,
                    verdict=TrustVerdict.INCONCLUSIVE,
                    artifact_path=target.artifact_path,
                    foundation=target.foundation,
                    independent_group=target.independent_group,
                    message=f"Adapter error: {type(exc).__name__}: {exc}",
                )
            results.append(result)

        return ProofRecord(
            binding=binding,
            plan=plan,
            formalization=formalization,
            results=results,
        )


def file_sha256(path: str) -> str:
    """Hash a proof artifact for explicit claim/proof binding."""
    import hashlib

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
