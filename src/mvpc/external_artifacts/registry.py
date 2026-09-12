"""Explicit artifact adapter registry.

Design note (Phase 1): this is the schema/version adapter registry asked
for in issue #8. It is a small, explicit dict keyed by the artifact's own
declared identity string (its "schema_version" field, which in both
supported artifact families doubles as a combined schema-id+version
string, e.g. "res-nova-claim-ledger-v1"). There is deliberately no
generic success fallback: `get_adapter` raises UnsupportedArtifactError
for any schema identity it does not recognize, and callers must render
that as a specific unsupported-artifact verdict, never as a pass.
"""

from __future__ import annotations

from typing import Any, Protocol

from mvpc.external_artifacts.models import Gate


class UnsupportedArtifactError(ValueError):
    """Raised when an artifact declares a schema identity/version this
    registry does not carry an adapter for. Always fail closed on this;
    never fall back to a generic/best-effort verifier."""

    def __init__(self, schema_identity: Any) -> None:
        self.schema_identity = schema_identity
        super().__init__(
            f"unsupported artifact schema identity: {schema_identity!r} "
            "(no adapter registered; artifact must be rejected, not guessed at)"
        )


class ArtifactAdapter(Protocol):
    """Contract every adapter in this registry must satisfy."""

    #: The artifact type name surfaced in verification output, e.g.
    #: "4leibniz-formal-claims-catalog" or "resnova-evidence-atlas".
    artifact_type: str

    #: Set of exact schema identity strings (as found in the artifact's
    #: own "schema_version" field) this adapter accepts.
    supported_schema_identities: set[str]

    def parse(self, raw: dict[str, Any]) -> Any:
        """Parse raw JSON into an adapter-internal representation.
        Must not run any external tool (no Lean, no network)."""
        ...

    def document_provenance(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Return the declared document-level provenance dict:
        {"repo": ..., "commit": ..., "path": ...}."""
        ...

    def run_gates(self, raw: dict[str, Any], *, policy: "AdapterPolicy") -> list[Gate]:
        """Run all schema/provenance/evidence/gate checks and return the
        full ordered list of Gate results. Never omit a gate silently;
        an inapplicable check must appear with status not_applicable."""
        ...


class AdapterPolicy:
    """Minimal, explicit policy knobs an adapter consults so behavior is
    configurable without inventing a second policy subsystem. Wraps the
    project's existing PolicyManifest-style values relevant to external
    artifacts."""

    def __init__(
        self,
        *,
        expected_repos: dict[str, str] | None = None,
        require_claim_provenance_match: bool = True,
        policy_version: str = "external-artifacts-v1",
    ) -> None:
        # artifact_type -> expected repo (e.g. "4leibniz-formal-claims-catalog"
        # -> "Mega-Therion/4Leibniz"). None/absent means "accept any
        # syntactically valid repo string" (still must pass shape checks).
        self.expected_repos = expected_repos or {}
        self.require_claim_provenance_match = require_claim_provenance_match
        self.policy_version = policy_version


_REGISTRY: dict[str, ArtifactAdapter] = {}


def register_adapter(adapter: ArtifactAdapter) -> None:
    for identity in adapter.supported_schema_identities:
        _REGISTRY[identity] = adapter


def get_adapter(schema_identity: str) -> ArtifactAdapter:
    adapter = _REGISTRY.get(schema_identity)
    if adapter is None:
        raise UnsupportedArtifactError(schema_identity)
    return adapter


def list_supported() -> dict[str, str]:
    """Map of supported schema identity -> artifact_type, for docs/CLI help."""
    return {identity: adapter.artifact_type for identity, adapter in _REGISTRY.items()}
