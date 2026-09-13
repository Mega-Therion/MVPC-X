"""Adapter for a RYTT CLI verified-artifact ZIP bundle (issue #7 scope
item 3): tamper detection over the ZIP produced by
`src/rytt/interchange.py::export_bundle()`.

Schema ground truth (fetched, not assumed): `export_bundle()` in the real
RYTT repo (read at commit aaf77db4666c62c57878e7c7a5f11dbd1754cf5b)
writes a ZIP with these members:

    artifact.json     - the full envelope (see rytt_adapter.py)
    source.txt        - envelope["source_text"], raw bytes
    encoded.rytt       - envelope["encoded_display"], raw bytes
    trace.json        - json.dumps(envelope["tokens"])
    metrics.json      - json.dumps(envelope["metrics"])
    verification.json - json.dumps(envelope["verification"])
    README.md         - static text, not checked

There is no separate manifest/hash-list file in the real bundle — the
"internal hash manifest" issue #7 scope item 3 asks for is, in this real
format, cross-member consistency: every member's content must agree with
the corresponding field embedded in artifact.json. This adapter
implements exactly that (and nothing invented on top of it): each of
source.txt/encoded.rytt/trace.json/metrics.json/verification.json must
byte-for-byte (for source.txt/encoded.rytt) or structurally
(for the JSON members) match the corresponding artifact.json field.
Any divergence is the tamper signal this adapter exists to catch.

This is registered in the same adapter registry as the other two RYTT
adapters and both JSON adapters (schema identity "rytt-zip-bundle-v1"),
but is never reached through the normal JSON-schema_version dispatch
path in verify.py, since its input is a ZIP file, not a JSON document.
mvpc.external_artifacts.verify.verify_zip_bundle_file reads the archive,
builds the synthetic raw dict this adapter's run_gates() expects, then
calls get_adapter("rytt-zip-bundle-v1") explicitly so `list_supported()`
and CLI help stay accurate. See that module for the ZIP-safety handling
(path traversal / duplicate member guards, BadZipFile -> a specific
verify.py error).
"""

from __future__ import annotations

import json
from typing import Any

from mvpc.external_artifacts.models import Gate, GateStatus
from mvpc.external_artifacts.registry import AdapterPolicy, register_adapter

ARTIFACT_TYPE = "rytt-zip-bundle"
SUPPORTED_IDENTITIES = {"rytt-zip-bundle-v1"}

REQUIRED_MEMBERS = (
    "artifact.json",
    "source.txt",
    "encoded.rytt",
    "trace.json",
    "metrics.json",
    "verification.json",
)


class RyttZipBundleAdapter:
    artifact_type = ARTIFACT_TYPE
    supported_schema_identities = SUPPORTED_IDENTITIES

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def document_provenance(self, raw: dict[str, Any]) -> dict[str, Any]:
        artifact = raw.get("_members", {}).get("artifact.json")
        doc_prov = (
            artifact.get("document_provenance") if isinstance(artifact, dict) else None
        )
        if isinstance(doc_prov, dict):
            return {
                "repo": doc_prov.get("repo") or doc_prov.get("repository"),
                "commit": doc_prov.get("commit") or doc_prov.get("commit_sha"),
                "path": doc_prov.get("path"),
            }
        return {"repo": None, "commit": None, "path": None}

    def run_gates(self, raw: dict[str, Any], *, policy: AdapterPolicy) -> list[Gate]:
        gates: list[Gate] = []

        member_names = raw.get("_member_names")
        if not isinstance(member_names, list):
            gates.append(
                Gate(
                    "bundle_shape",
                    GateStatus.FAILED,
                    "no ZIP member listing was provided",
                )
            )
            return gates

        gates.append(self._required_members_gate(member_names))

        members = raw.get("_members", {})
        artifact = members.get("artifact.json")
        if not isinstance(artifact, dict):
            gates.append(
                Gate(
                    "artifact_json_parses",
                    GateStatus.FAILED,
                    "artifact.json is missing or is not a JSON object",
                )
            )
            return gates
        gates.append(
            Gate(
                "artifact_json_parses",
                GateStatus.PASSED,
                "artifact.json parsed as a JSON object",
            )
        )

        gates.append(self._member_cross_consistency_gate(members))
        gates.append(self._round_trip_consistency_gate(artifact))

        return gates

    # -- individual gates -------------------------------------------------

    def _required_members_gate(self, member_names: list[str]) -> Gate:
        names_set = set(member_names)
        dupes = {n for n in member_names if member_names.count(n) > 1}
        problems = []
        missing = [m for m in REQUIRED_MEMBERS if m not in names_set]
        if missing:
            problems.append(f"missing required member(s): {missing}")
        if dupes:
            problems.append(
                f"duplicate ZIP member name(s) present (tamper vector): {sorted(dupes)}"
            )
        if problems:
            return Gate("required_members", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "required_members",
            GateStatus.PASSED,
            f"all {len(REQUIRED_MEMBERS)} required member(s) present exactly once",
        )

    def _member_cross_consistency_gate(self, members: dict[str, Any]) -> Gate:
        artifact = members.get("artifact.json")
        problems = []

        def _text_member(name: str) -> str | None:
            v = members.get(name)
            return v if isinstance(v, str) else None

        def _json_member(name: str) -> Any:
            return members.get(name)

        if not isinstance(artifact, dict):
            return Gate(
                "member_cross_consistency",
                GateStatus.UNAVAILABLE,
                "artifact.json did not parse; cannot cross-check members",
            )

        source_txt = _text_member("source.txt")
        if source_txt is None:
            problems.append("source.txt is missing or not decodable as text")
        elif source_txt != artifact.get("source_text"):
            problems.append("source.txt content != artifact.json['source_text']")

        encoded_rytt = _text_member("encoded.rytt")
        if encoded_rytt is None:
            problems.append("encoded.rytt is missing or not decodable as text")
        elif encoded_rytt != artifact.get("encoded_display"):
            problems.append("encoded.rytt content != artifact.json['encoded_display']")

        trace = _json_member("trace.json")
        if trace is None:
            problems.append("trace.json is missing or not valid JSON")
        elif trace != artifact.get("tokens"):
            problems.append("trace.json content != artifact.json['tokens']")

        metrics = _json_member("metrics.json")
        if metrics is None:
            problems.append("metrics.json is missing or not valid JSON")
        elif metrics != artifact.get("metrics"):
            problems.append("metrics.json content != artifact.json['metrics']")

        verification = _json_member("verification.json")
        if verification is None:
            problems.append("verification.json is missing or not valid JSON")
        elif verification != artifact.get("verification"):
            problems.append(
                "verification.json content != artifact.json['verification']"
            )

        if problems:
            return Gate(
                "member_cross_consistency", GateStatus.FAILED, "; ".join(problems)
            )
        return Gate(
            "member_cross_consistency",
            GateStatus.PASSED,
            "source.txt, encoded.rytt, trace.json, metrics.json, verification.json "
            "all agree byte-for-byte/structurally with artifact.json",
        )

    def _round_trip_consistency_gate(self, artifact: dict[str, Any]) -> Gate:
        verification = artifact.get("verification")
        source_text = artifact.get("source_text")
        if not isinstance(verification, dict) or not isinstance(source_text, str):
            return Gate(
                "round_trip_consistency",
                GateStatus.UNAVAILABLE,
                "artifact.json verification/source_text missing",
            )
        decoded_text = verification.get("decoded_text")
        declared_flag = verification.get("round_trip_exact")
        if not isinstance(decoded_text, str):
            return Gate(
                "round_trip_consistency",
                GateStatus.FAILED,
                "verification.decoded_text is missing or not a string",
            )
        actual_match = decoded_text == source_text
        if declared_flag is not actual_match:
            return Gate(
                "round_trip_consistency",
                GateStatus.FAILED,
                f"verification.round_trip_exact={declared_flag!r} disagrees with "
                f"plain string comparison of source_text vs decoded_text "
                f"(actual equality={actual_match})",
            )
        return Gate(
            "round_trip_consistency",
            GateStatus.PASSED,
            f"declared round_trip_exact={declared_flag} matches plain string "
            "comparison inside the bundle's own artifact.json",
        )


register_adapter(RyttZipBundleAdapter())
