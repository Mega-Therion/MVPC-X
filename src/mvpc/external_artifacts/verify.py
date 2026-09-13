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
import zipfile
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


def _resolve_schema_identity(raw: dict[str, Any]) -> Any:
    """Most artifacts (4Leibniz, Res-Nova) declare a single top-level
    "schema_version" string used verbatim as the registry dispatch key.
    RYTT's own envelope/interchange format (issue #7) has no such field
    at all — it declares identity via a ("format", "format_version",
    "spec_version") triple instead (see src/rytt/interchange.py:
    build_envelope(), read directly from the RYTT repo). This function
    synthesizes the equivalent dispatch key for that shape, WITHOUT ever
    widening what an existing "schema_version"-bearing artifact resolves
    to (that branch is checked first and returned unchanged).

    Version-pinned on purpose: only the exact (format_version,
    spec_version) pair this adapter was written against resolves to a
    known identity. A future RYTT format/spec bump must fall through to
    UnsupportedArtifactError, never be silently graded by v1 rules — see
    rytt_adapter.SUPPORTED_FORMAT_VERSION /
    SUPPORTED_SPEC_VERSION and rytt_conformance_adapter.
    SUPPORTED_SPEC_VERSION."""
    schema_identity = raw.get("schema_version")
    if isinstance(schema_identity, str) and schema_identity:
        return schema_identity

    if (
        raw.get("format") == "rytt"
        and raw.get("format_version") == "0.1"
        and raw.get("spec_version") == "0.1"
    ):
        return "rytt-envelope-v1"

    return schema_identity


class ZipArtifactError(ValueError):
    """The input path is not a readable, well-formed ZIP archive, or its
    member listing violates a ZIP-safety invariant (path traversal,
    duplicate member names). Distinct from MalformedArtifactError so
    callers can tell "not JSON" apart from "not a valid ZIP", but the CLI
    treats both as the same exit-code-2 class of input error."""


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

    schema_identity = _resolve_schema_identity(raw)
    if not schema_identity or not isinstance(schema_identity, str):
        raise UnsupportedArtifactError(schema_identity)

    return _verify_resolved(schema_identity, raw, path, policy)


def _verify_resolved(
    schema_identity: str,
    raw: dict[str, Any],
    path: str,
    policy: AdapterPolicy,
) -> ExternalArtifactVerification:
    """Shared tail end of verification once a schema identity and a raw
    dict (parsed JSON, or a synthetic dict built from a ZIP's members —
    see verify_zip_bundle_file) are both in hand."""
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


_ZIP_JSON_MEMBERS = ("artifact.json", "trace.json", "metrics.json", "verification.json")
_ZIP_TEXT_MEMBERS = ("source.txt", "encoded.rytt")


def load_zip_bundle(path: str) -> dict[str, Any]:
    """Read a RYTT CLI ZIP artifact into the synthetic raw dict shape
    rytt_bundle_adapter.RyttZipBundleAdapter expects: {"_member_names":
    [...], "_members": {name: parsed_json_or_text_or_None}}. Never writes
    to disk, never re-zips, never trusts a member name outside the
    archive root (path traversal guard) or a duplicate member name
    (each is itself a tamper vector for a ZIP-based artifact)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"artifact path is not a local file: {path}")
    try:
        with zipfile.ZipFile(p, "r") as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            for name in names:
                normalized = Path(name)
                if normalized.is_absolute() or ".." in normalized.parts:
                    raise ZipArtifactError(
                        f"ZIP member name {name!r} is unsafe (absolute path or "
                        "'..' traversal component); refusing to read this bundle"
                    )
            members: dict[str, Any] = {}
            for name in set(names):
                # zipfile.read() on a duplicate-name archive returns the
                # LAST entry; report every distinct name once, but the
                # duplicate itself is still flagged by the adapter's
                # required_members gate via _member_names below.
                raw_bytes = archive.read(name)
                if name in _ZIP_JSON_MEMBERS:
                    try:
                        members[name] = json.loads(raw_bytes.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        members[name] = None
                elif name in _ZIP_TEXT_MEMBERS:
                    try:
                        members[name] = raw_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        members[name] = None
                # Unrecognized members (e.g. README.md) are intentionally
                # not parsed/stored; the adapter never checks them.
    except zipfile.BadZipFile as exc:
        raise ZipArtifactError(f"{path} is not a valid ZIP archive: {exc}") from exc

    return {"_member_names": names, "_members": members}


def verify_zip_bundle_file(
    path: str,
    *,
    policy: AdapterPolicy | None = None,
) -> ExternalArtifactVerification:
    """Local-file-only entry point for a RYTT CLI ZIP artifact (issue #7
    scope item 3). Never fetches a URL, never re-runs RYTT's compiler.
    Dispatches through the same adapter registry as
    verify_artifact_file, using the fixed identity "rytt-zip-bundle-v1"
    (there is only one bundle-shape adapter registered; a future bundle
    format revision would need its own identity and its own detection
    rule here, mirroring _resolve_schema_identity)."""
    policy = policy or AdapterPolicy()
    raw = load_zip_bundle(path)
    return _verify_resolved("rytt-zip-bundle-v1", raw, path, policy)


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
