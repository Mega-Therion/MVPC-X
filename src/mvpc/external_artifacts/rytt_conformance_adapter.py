"""Adapter for a declared RYTT conformance/vectors.json replay run
(issue #7, scope item 2).

Schema note (this schema is DESIGNED here, not fetched — flagged exactly
like the 4Leibniz adapter's documented assumption): the real RYTT repo
(read at commit aaf77db4666c62c57878e7c7a5f11dbd1754cf5b) has
`conformance/vectors.json` (7 reference vectors, `format:
"rytt-conformance"`, `version: "0.1"`) and `scripts/verify_conformance.py`
which replays every vector and prints pass/fail — but persists no
structured report artifact anywhere. This adapter defines the schema for
a *hypothetical* persisted replay-report artifact an operator/CI job
could emit, of the shape:

    {
      "schema_version": "rytt-conformance-run-v1",
      "document_provenance": {"repo": ..., "commit": ..., "path": ...},
      "spec_version": "0.1",
      "vectors_reference": {
        "repo": ..., "commit": ..., "path": "conformance/vectors.json",
        "format": "rytt-conformance", "version": "0.1",
        "sha256": <SHA-256 hex of the exact local vectors.json bytes used>
      },
      "results": [
        {"id": ..., "source": ..., "encoded_display": ..., "decoded": ...,
         "token_count": N, "passed": bool},
        ...
      ],
      "summary": {"total": N, "passed": N, "failed": N}
    }

Ground-truth-wins design decision (explicit per issue #7 scope item 2):
this adapter CANNOT re-run RYTT's encode/decode without forking its
grammar, which is out of scope by the RYTT repo's own stated contract.
It therefore implements "option B" from the issue brief: verify the
DECLARED replay result's internal consistency and hash-binding against a
local copy of the real conformance/vectors.json, rather than
re-executing the encoding. Concretely: every declared `results[i]` entry
must reproduce, byte-for-byte, the `source`/`encoded_display`/`decoded`/
`token_count` fields of the vector with the same `id` in the local
reference file (this catches a declared-passed replay that does not
actually match the vectors file); every declared `passed` flag is
recomputed from the declared fields and compared, never trusted as a
bare boolean; vector coverage is checked (no vector skipped, none
invented); and the local reference file's own SHA-256 is recorded in the
gate detail and, if the run artifact declares one, compared against it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from mvpc.external_artifacts.models import Gate, GateStatus
from mvpc.external_artifacts.provenance_checks import (
    extract_repo_commit_path,
    is_valid_sha256_hex,
)
from mvpc.external_artifacts.registry import AdapterPolicy, register_adapter

ARTIFACT_TYPE = "rytt-conformance-run"
SUPPORTED_IDENTITIES = {"rytt-conformance-run-v1"}

SUPPORTED_SPEC_VERSION = "0.1"
EXPECTED_VECTORS_FORMAT = "rytt-conformance"
EXPECTED_VECTORS_VERSION = "0.1"


class RyttConformanceRunAdapter:
    artifact_type = ARTIFACT_TYPE
    supported_schema_identities = SUPPORTED_IDENTITIES

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def document_provenance(self, raw: dict[str, Any]) -> dict[str, Any]:
        repo, commit, path = extract_repo_commit_path(raw.get("document_provenance"))
        return {"repo": repo, "commit": commit, "path": path}

    def _load_reference_vectors(
        self, raw: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, str | None, list[str]]:
        """Returns (parsed_vectors_doc, local_file_sha256, problems)."""
        vref = raw.get("vectors_reference")
        problems: list[str] = []
        if not isinstance(vref, dict):
            return None, None, ["vectors_reference object is missing"]
        local_path = vref.get("local_copy_path")
        if not local_path or not isinstance(local_path, str):
            return (
                None,
                None,
                [
                    "vectors_reference.local_copy_path is missing (this adapter "
                    "is local-file-only and never fetches conformance/vectors.json "
                    "over the network)"
                ],
            )
        p = Path(local_path)
        if not p.is_file():
            return (
                None,
                None,
                [f"vectors_reference.local_copy_path {local_path!r} does not exist"],
            )
        content = p.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        try:
            doc = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return None, digest, [f"local vectors file is not valid JSON: {exc}"]
        if not isinstance(doc, dict) or not isinstance(doc.get("vectors"), list):
            return (
                None,
                digest,
                ["local vectors file does not have a top-level 'vectors' array"],
            )
        if doc.get("format") != EXPECTED_VECTORS_FORMAT:
            problems.append(
                f"local vectors file format {doc.get('format')!r} != "
                f"{EXPECTED_VECTORS_FORMAT!r}"
            )
        if doc.get("version") != EXPECTED_VECTORS_VERSION:
            problems.append(
                f"local vectors file version {doc.get('version')!r} != "
                f"{EXPECTED_VECTORS_VERSION!r}"
            )
        declared_sha = vref.get("sha256")
        if declared_sha is not None:
            if not is_valid_sha256_hex(declared_sha):
                problems.append(
                    f"vectors_reference.sha256 {declared_sha!r} is not a "
                    "64-hex-char SHA-256 digest"
                )
            elif declared_sha != digest:
                problems.append(
                    f"vectors_reference.sha256={declared_sha} does not match "
                    f"the local file's actual SHA-256={digest}"
                )
        return doc, digest, problems

    def run_gates(self, raw: dict[str, Any], *, policy: AdapterPolicy) -> list[Gate]:
        gates: list[Gate] = []

        results = raw.get("results")
        if raw.get("spec_version") != SUPPORTED_SPEC_VERSION or not isinstance(
            results, list
        ):
            problems = []
            if raw.get("spec_version") != SUPPORTED_SPEC_VERSION:
                problems.append(
                    f"spec_version {raw.get('spec_version')!r} != "
                    f"{SUPPORTED_SPEC_VERSION!r}"
                )
            if not isinstance(results, list):
                problems.append("top-level 'results' array is missing or not a list")
            gates.append(Gate("schema_shape", GateStatus.FAILED, "; ".join(problems)))
            return gates
        gates.append(
            Gate(
                "schema_shape", GateStatus.PASSED, f"{len(results)} declared result(s)"
            )
        )

        gates.append(self._document_provenance_gate(raw, policy))

        ref_doc, ref_sha, ref_problems = self._load_reference_vectors(raw)
        if ref_problems or ref_doc is None:
            detail = "; ".join(ref_problems) if ref_problems else "unknown error"
            if ref_sha:
                detail += f" (local file sha256={ref_sha})"
            gates.append(Gate("vectors_reference_resolves", GateStatus.FAILED, detail))
            # Nothing downstream can be checked without a resolved reference.
            gates.append(
                Gate(
                    "vector_coverage",
                    GateStatus.UNAVAILABLE,
                    "reference vectors file did not resolve",
                )
            )
            gates.append(
                Gate(
                    "declared_replay_matches_reference",
                    GateStatus.UNAVAILABLE,
                    "reference vectors file did not resolve",
                )
            )
            gates.append(
                Gate(
                    "passed_flag_consistency",
                    GateStatus.UNAVAILABLE,
                    "reference vectors file did not resolve",
                )
            )
            gates.append(self._summary_consistency_gate(raw, results))
            return gates
        gates.append(
            Gate(
                "vectors_reference_resolves",
                GateStatus.PASSED,
                f"local reference file resolved, sha256={ref_sha}, "
                f"{len(ref_doc['vectors'])} vector(s)",
            )
        )

        ref_by_id = {
            v["id"]: v
            for v in ref_doc["vectors"]
            if isinstance(v, dict) and isinstance(v.get("id"), str)
        }
        declared_by_id = {
            r["id"]: r
            for r in results
            if isinstance(r, dict) and isinstance(r.get("id"), str)
        }

        gates.append(self._coverage_gate(ref_by_id, declared_by_id, results))
        gates.append(self._replay_match_gate(ref_by_id, declared_by_id))
        gates.append(self._passed_flag_gate(ref_by_id, declared_by_id))
        gates.append(self._summary_consistency_gate(raw, results))

        return gates

    # -- individual gates -------------------------------------------------

    def _document_provenance_gate(
        self, raw: dict[str, Any], policy: AdapterPolicy
    ) -> Gate:
        doc_prov = raw.get("document_provenance")
        if not isinstance(doc_prov, dict):
            return Gate(
                "document_provenance",
                GateStatus.FAILED,
                "document_provenance object is missing",
            )
        repo, commit, _path = extract_repo_commit_path(doc_prov)
        problems = []
        if not repo:
            problems.append("repo is missing")
        expected_repo = policy.expected_repos.get(self.artifact_type)
        if expected_repo and repo != expected_repo:
            problems.append(
                f"repo {repo!r} does not match policy-configured {expected_repo!r}"
            )
        if not commit:
            problems.append("commit is missing")
        if problems:
            return Gate("document_provenance", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "document_provenance", GateStatus.PASSED, f"repo={repo} commit={commit}"
        )

    def _coverage_gate(
        self,
        ref_by_id: dict[str, Any],
        declared_by_id: dict[str, Any],
        results: list[Any],
    ) -> Gate:
        problems = []
        malformed = [
            r
            for r in results
            if not isinstance(r, dict) or not isinstance(r.get("id"), str)
        ]
        if malformed:
            problems.append(f"{len(malformed)} result entry(ies) missing a string 'id'")
        dupes = {
            rid
            for rid in declared_by_id
            if list(r.get("id") for r in results if isinstance(r, dict)).count(rid) > 1
        }
        if dupes:
            problems.append(f"duplicate declared result id(s): {sorted(dupes)}")
        missing = set(ref_by_id) - set(declared_by_id)
        if missing:
            problems.append(
                f"reference vector id(s) never declared in results: {sorted(missing)}"
            )
        extra = set(declared_by_id) - set(ref_by_id)
        if extra:
            problems.append(
                f"declared result id(s) not present in the reference file: {sorted(extra)}"
            )
        if problems:
            return Gate("vector_coverage", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "vector_coverage",
            GateStatus.PASSED,
            f"all {len(ref_by_id)} reference vector(s) are declared exactly once, no extras",
        )

    def _replay_match_gate(
        self, ref_by_id: dict[str, Any], declared_by_id: dict[str, Any]
    ) -> Gate:
        problems = []
        for vid, ref in ref_by_id.items():
            decl = declared_by_id.get(vid)
            if not isinstance(decl, dict):
                continue  # already flagged by vector_coverage
            for field_name in ("source", "encoded_display", "decoded", "token_count"):
                if decl.get(field_name) != ref.get(field_name):
                    problems.append(
                        f"{vid}: declared {field_name}={decl.get(field_name)!r} "
                        f"!= reference {field_name}={ref.get(field_name)!r}"
                    )
        if problems:
            return Gate(
                "declared_replay_matches_reference",
                GateStatus.FAILED,
                "; ".join(problems),
            )
        return Gate(
            "declared_replay_matches_reference",
            GateStatus.PASSED,
            f"all {len(ref_by_id)} declared result(s) reproduce the reference "
            "file's source/encoded_display/decoded/token_count verbatim",
        )

    def _passed_flag_gate(
        self, ref_by_id: dict[str, Any], declared_by_id: dict[str, Any]
    ) -> Gate:
        problems = []
        for vid, ref in ref_by_id.items():
            decl = declared_by_id.get(vid)
            if not isinstance(decl, dict):
                continue
            recomputed = (
                decl.get("source") == ref.get("source")
                and decl.get("encoded_display") == ref.get("encoded_display")
                and decl.get("decoded") == ref.get("decoded")
                and decl.get("token_count") == ref.get("token_count")
                and decl.get("decoded") == decl.get("source")
            )
            declared_flag = decl.get("passed")
            if declared_flag is not recomputed:
                problems.append(
                    f"{vid}: declared passed={declared_flag!r} but recomputing "
                    f"from the declared fields gives {recomputed} (never trust "
                    "a bare passed boolean)"
                )
        if problems:
            return Gate(
                "passed_flag_consistency", GateStatus.FAILED, "; ".join(problems)
            )
        return Gate(
            "passed_flag_consistency",
            GateStatus.PASSED,
            "every declared 'passed' flag matches a recomputation from that "
            "same result's own declared fields",
        )

    def _summary_consistency_gate(
        self, raw: dict[str, Any], results: list[Any]
    ) -> Gate:
        summary = raw.get("summary")
        if not isinstance(summary, dict):
            return Gate(
                "summary_consistency", GateStatus.FAILED, "summary object is missing"
            )
        valid_results = [r for r in results if isinstance(r, dict)]
        actual_total = len(valid_results)
        actual_passed = sum(1 for r in valid_results if r.get("passed") is True)
        actual_failed = sum(1 for r in valid_results if r.get("passed") is False)
        problems = []
        if summary.get("total") != actual_total:
            problems.append(
                f"summary.total={summary.get('total')!r} != counted {actual_total}"
            )
        if summary.get("passed") != actual_passed:
            problems.append(
                f"summary.passed={summary.get('passed')!r} != counted {actual_passed}"
            )
        if summary.get("failed") != actual_failed:
            problems.append(
                f"summary.failed={summary.get('failed')!r} != counted {actual_failed}"
            )
        if problems:
            return Gate("summary_consistency", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "summary_consistency",
            GateStatus.PASSED,
            f"summary (total={actual_total} passed={actual_passed} "
            f"failed={actual_failed}) matches the declared results array",
        )


register_adapter(RyttConformanceRunAdapter())
