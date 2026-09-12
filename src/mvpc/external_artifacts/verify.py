"""Orchestration: load a local artifact file, pick its adapter, run gates,
build the deterministic result record, and seal it into an MVPC-X witness
bundle. This module is the only place issue #8's CLI command talks to.

Design note (Phase 1): reuses mvpc.canonical for the canonical hash
(hash_canonical over the parsed JSON), mvpc.witness_bundle /
mvpc.trust_verdicts / mvpc.tcb / mvpc.policy_manifest for the seal instead
of inventing a second sealing model, and mvpc.version for the verifier
version string. No network access, no subprocess, no file write other
than the explicit --output path the caller supplies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mvpc.canonical import hash_canonical
from mvpc.external_artifacts.models import ArtifactVerificationResult, GateStatus
from mvpc.external_artifacts.registry import (
    AdapterPolicy,
    UnsupportedArtifactError,
    get_adapter,
)
from mvpc.policy_manifest import PolicyLevel, PolicyManifest
from mvpc.tcb import BackendTCB, TCBDeclaration
from mvpc.trust_verdicts import TrustVerdict
from mvpc.version import __version__
from mvpc.witness_bundle import WitnessBundle, WitnessEntry

VERIFIER_NAME = "mvpc-x"
EXTERNAL_ARTIFACT_POLICY_ID = "external-artifacts-v1"

# Canonical identity vs output metadata (Phase 5): TCBDeclaration,
# PolicyManifest, WitnessEntry, and WitnessBundle all stamp a wall-clock
# created_at by default, and WitnessEntry mints a random witness_id. Both
# would make manifest_hash()/composite_hash()/witness.hash() differ on
# every run of *semantically identical* input, which fails the
# determinism requirement (Phase 5, adversarial case 16). We pin all of
# them to this fixed sentinel and derive witness_id from the artifact's
# own canonical hash instead, so the sealed bundle's identity hashes are
# a pure function of artifact content. A real wall-clock timestamp is
# still recorded, but only in the CLI's output file wrapper
# (mvpc.external_artifacts.cli_support), clearly separated from this
# canonical identity.
_CANONICAL_IDENTITY_TIMESTAMP = "1970-01-01T00:00:00Z"

_GATE_TO_TRUST_VERDICT = {
    GateStatus.PASSED: TrustVerdict.EVIDENCE_SUPPORTED,
    GateStatus.FAILED: TrustVerdict.REJECTED,
    GateStatus.UNAVAILABLE: TrustVerdict.INCONCLUSIVE,
    GateStatus.NOT_APPLICABLE: TrustVerdict.INCONCLUSIVE,
}


class MalformedArtifactError(ValueError):
    """The input file is not valid JSON, or is not a JSON object."""


@dataclass
class ExternalArtifactVerification:
    result: ArtifactVerificationResult
    bundle: WitnessBundle
    raw: dict[str, Any]

    def result_dict(self) -> dict[str, Any]:
        return self.result.to_dict()

    def exit_code(self) -> int:
        return 0 if self.result.verdict == GateStatus.PASSED else 1


def load_artifact_json(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"artifact path is not a local file: {path}")
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise MalformedArtifactError(f"could not read {path}: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise MalformedArtifactError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise MalformedArtifactError(
            f"{path} must contain a JSON object at the top level"
        )
    return data


def verify_artifact_file(
    path: str,
    *,
    policy: AdapterPolicy | None = None,
) -> ExternalArtifactVerification:
    """Local-file-only entry point. Never fetches a URL. Raises
    UnsupportedArtifactError for unrecognized schema identities and
    MalformedArtifactError for unparsable input — both are distinct,
    specific failure modes, never a generic success fallback."""
    policy = policy or AdapterPolicy()
    raw = load_artifact_json(path)

    schema_identity = raw.get("schema_version")
    if not schema_identity or not isinstance(schema_identity, str):
        raise UnsupportedArtifactError(schema_identity)

    adapter = get_adapter(schema_identity)  # raises UnsupportedArtifactError if unknown
    parsed = adapter.parse(raw)
    gates = adapter.run_gates(parsed, policy=policy)
    provenance = adapter.document_provenance(parsed)

    canonical_hash = hash_canonical(raw)

    result = ArtifactVerificationResult(
        verifier_name=VERIFIER_NAME,
        verifier_version=__version__,
        artifact_type=adapter.artifact_type,
        schema_id=schema_identity,
        schema_version=schema_identity,
        source_path=str(Path(path)),
        canonical_hash=canonical_hash,
        provenance=provenance,
        gates=gates,
        policy_version=policy.policy_version,
    )

    bundle = _build_witness_bundle(result, raw)
    return ExternalArtifactVerification(result=result, bundle=bundle, raw=raw)


def _build_witness_bundle(
    result: ArtifactVerificationResult, raw: dict[str, Any]
) -> WitnessBundle:
    verdict = _GATE_TO_TRUST_VERDICT[result.verdict]

    policy_manifest = PolicyManifest(
        policy_id=EXTERNAL_ARTIFACT_POLICY_ID,
        version="1.0.0",
        level=PolicyLevel.DEFAULT,
        minimum_verdict=TrustVerdict.EVIDENCE_SUPPORTED,
        require_human_attestation=False,
        require_ai_provenance_label=False,
        require_signed_witness=False,
        reject_on_inconclusive=False,
        reject_on_timeout=False,
        allowed_backends=["external-artifact-verifier"],
        description=(
            "External evidence artifact verification (issue #8): schema, "
            "provenance, and declared-evidence gate checks over a local "
            "claim/evidence artifact file. Never runs Lean or any external "
            "toolchain; never asserts scientific/physical truth."
        ),
        created_at=_CANONICAL_IDENTITY_TIMESTAMP,
    )

    tcb = TCBDeclaration(
        mvpc_version=__version__,
        backends=[
            BackendTCB(
                name="external-artifact-verifier", version=__version__, command=[]
            )
        ],
        assumptions=[
            "The artifact's declared schema_version, provenance, and evidence "
            "fields are taken at face value; this verifier does not re-derive "
            "or re-run any upstream check.",
        ],
        limitations=[
            "Does not execute a Lean toolchain or any other formal-proof checker.",
            "Does not assess scientific/physical truth of any claim.",
            "Does not interpret Res-Nova epistemic status beyond declared schema rules.",
            "Does not evaluate RYTT grammar or AEON governance policy.",
            "Hashes and gates establish declared-artifact integrity/consistency, "
            "not abstract truth of the underlying claims.",
        ],
        created_at=_CANONICAL_IDENTITY_TIMESTAMP,
    )

    # Bind every gate result and the full raw claims payload into the
    # witness entry's backend_result so nothing (including refuted/open
    # claims) is silently excluded from the sealed record.
    backend_result = {
        "artifact_type": result.artifact_type,
        "schema_id": result.schema_id,
        "schema_version": result.schema_version,
        "provenance": result.provenance,
        "gates": [g.to_dict() for g in result.gates],
        "verdict": result.verdict.value,
        "claims_preserved": raw.get("claims", []),
    }

    witness = WitnessEntry(
        verdict=verdict,
        claim_hash=result.canonical_hash,
        policy_hash=policy_manifest.hash(),
        tcb_hash=tcb.hash(),
        backend_name="external-artifact-verifier",
        backend_result=backend_result,
        evidence_hashes=[hash_canonical(g.to_dict()) for g in result.gates],
        witness_id=f"w-{result.canonical_hash[:24]}",
        created_at=_CANONICAL_IDENTITY_TIMESTAMP,
    )

    return WitnessBundle(
        witness=witness,
        tcb=tcb,
        policy=policy_manifest,
        created_at=_CANONICAL_IDENTITY_TIMESTAMP,
    )
