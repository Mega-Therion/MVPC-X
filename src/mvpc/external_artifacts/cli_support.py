"""`mvpc verify artifact <path>` command implementation.

Kept out of mvpc.cli to keep that module thin (Phase 1 design decision):
cli.py only parses args and routes; this module owns the actual
local-file verification workflow, output rendering, and exit-code
semantics for issue #8.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mvpc.external_artifacts.models import GateStatus
from mvpc.external_artifacts.registry import AdapterPolicy, UnsupportedArtifactError
from mvpc.external_artifacts.verify import (
    MalformedArtifactError,
    verify_artifact_file,
)


def _load_policy(policy_path: str | None) -> AdapterPolicy:
    if not policy_path:
        return AdapterPolicy()
    with open(policy_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return AdapterPolicy(
        expected_repos=data.get("expected_repos"),
        require_claim_provenance_match=data.get("require_claim_provenance_match", True),
        policy_version=data.get("policy_version", "external-artifacts-v1"),
    )


def _default_output_path(artifact_path: str, canonical_hash: str) -> str:
    """Deterministic default output path so a plain `mvpc verify artifact
    x.json` run never silently overwrites a *different* prior witness
    bundle, and re-running against byte-identical input reproduces the
    same path (Phase 6: "deterministic/unique safe path"). Derived from
    the artifact's own canonical hash rather than wall-clock time, so the
    name itself carries no non-reproducible metadata:
    <stem>.witness.<hash-prefix>.json."""
    stem = Path(artifact_path).stem
    return f"{stem}.witness.{canonical_hash[:16]}.json"


def _render_text(verification) -> str:
    result = verification.result
    lines = [
        "MVPC-X external artifact verification",
        "=" * 42,
        f"Artifact type    : {result.artifact_type}",
        f"Schema identity  : {result.schema_id}",
        f"Source path      : {result.source_path}",
        f"Canonical hash   : {result.canonical_hash}",
        f"Provenance       : repo={result.provenance.get('repo')} "
        f"commit={result.provenance.get('commit')} path={result.provenance.get('path')}",
        "",
        "Gates:",
    ]
    for g in result.gates:
        lines.append(f"  [{g.status.value:<14}] {g.name}: {g.detail}")
    lines += [
        "",
        f"Verdict          : {result.verdict.value}",
        f"Policy version   : {result.policy_version}",
    ]
    return "\n".join(lines)


def run_verify_artifact(args) -> int:
    policy = _load_policy(getattr(args, "policy", None))

    try:
        verification = verify_artifact_file(args.path, policy=policy)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except UnsupportedArtifactError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except MalformedArtifactError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = verification.result

    output_path = args.output
    default_name = _default_output_path(args.path, result.canonical_hash)
    if output_path and os.path.isdir(output_path):
        output_path = os.path.join(output_path, default_name)
    elif not output_path:
        output_path = default_name

    if os.path.exists(output_path) and not getattr(args, "overwrite", False):
        print(
            f"error: witness output path already exists ({output_path}); "
            "pass --overwrite to replace it, or omit --output for a fresh unique path",
            file=sys.stderr,
        )
        return 2

    # "generated_at" is wall-clock OUTPUT metadata about this run of the
    # CLI, kept strictly separate from the canonical verification
    # identity: manifest/witness/tcb/policy hashes never depend on it
    # (see mvpc.external_artifacts.verify._CANONICAL_IDENTITY_TIMESTAMP).
    bundle_payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest": verification.bundle.manifest(),
        "witness": verification.bundle.witness.to_dict(),
        "tcb": verification.bundle.tcb.to_dict(),
        "policy": verification.bundle.policy.to_dict(),
        "result": result.to_dict(),
    }
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(bundle_payload, fh, indent=2, sort_keys=True)
        fh.write("\n")

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(_render_text(verification))
        print(f"Witness bundle   : {output_path}")

    if result.verdict in (GateStatus.FAILED, GateStatus.UNAVAILABLE):
        return 1
    if result.verdict == GateStatus.NOT_APPLICABLE:
        return 1
    return 0
