"""Adapter for a RYTT versioned envelope artifact (issue #7).

Schema ground truth (unlike the 4Leibniz adapter, this one IS fetched
from a real, read file, not reasoned from a description): read directly
from src/rytt/interchange.py in the RYTT-Sovereign-Semiotics repo at
commit aaf77db4666c62c57878e7c7a5f11dbd1754cf5b (main, as checked out
locally when this adapter was written; NOT independently verified
against the short hash "c963830" cited in issue #7's own text — that
hash was not confirmed to resolve to the same or a different commit).
`build_envelope()` there produces:

    {
      "format": "rytt",
      "format_version": "0.1",
      "spec_version": "0.1",
      "vocabulary_sha256": <64-hex-char SHA-256 of spec/vocabulary.json,
                            or the literal string "unavailable" if that
                            file was missing when the envelope was built>,
      "source_encoding": "utf-8",
      "source_text": <str>,
      "encoded_display": <str>,
      "tokens": [ {index, source, kind, plane, codepoint, codepoint_int,
                   is_chord, passthrough}, ... ],
      "metrics": {source_characters, rytt_tokens, source_utf8_bytes,
                  encoded_utf8_bytes, chord_tokens,
                  character_reduction_pct},
      "verification": {"round_trip_exact": bool, "decoded_text": str},
    }

Ground-truth-vs-issue-text discrepancy (documented per the same
precedent as resnova_adapter.py's discrepancy note): issue #7 describes
"BLAKE3 envelope hashes"; the artifact RYTT actually emits hashes with
plain hashlib.sha256 under the field name `vocabulary_sha256`. This
adapter verifies what RYTT actually writes (SHA-256), not the
hypothetical BLAKE3 the issue text assumed. No `blake3` dependency is
introduced anywhere in MVPC-X for this reason.

This adapter never imports or runs RYTT's own compiler/grammar (the
`rytt.compiler.RyttCompiler` used by `verify_envelope()` upstream). Per
the RYTT repo's own stated contract ("Downstream crates consume [the
JSON-first portable API]; they do not fork the grammar"), MVPC-X only
checks structural self-consistency of the *declared* envelope fields:
whether the declared `round_trip_exact` flag agrees with a plain string
comparison of the envelope's own `source_text` and
`verification.decoded_text` fields, and whether the declared
`vocabulary_sha256` matches an operator-configured expected value. It
never re-encodes or re-decodes `source_text` itself.
"""

from __future__ import annotations

from typing import Any

from mvpc.external_artifacts.models import Gate, GateStatus
from mvpc.external_artifacts.provenance_checks import is_valid_sha256_hex
from mvpc.external_artifacts.registry import AdapterPolicy, register_adapter

ARTIFACT_TYPE = "rytt-envelope"
SUPPORTED_IDENTITIES = {"rytt-envelope-v1"}

# The only (format_version, spec_version) pair this adapter was written
# against. A future RYTT bump to either must fall through to
# UnsupportedArtifactError, never be silently graded by v1 rules — see
# _resolve_schema_identity in verify.py, which only mints the
# "rytt-envelope-v1" identity when both of these match exactly.
SUPPORTED_FORMAT_VERSION = "0.1"
SUPPORTED_SPEC_VERSION = "0.1"

_REQUIRED_TOKEN_FIELDS = (
    "index",
    "source",
    "kind",
    "is_chord",
    "passthrough",
)
_CONTROLLED_TOKEN_KINDS = {"chord", "glyph", "passthrough"}


class RyttEnvelopeAdapter:
    artifact_type = ARTIFACT_TYPE
    supported_schema_identities = SUPPORTED_IDENTITIES

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def document_provenance(self, raw: dict[str, Any]) -> dict[str, Any]:
        # A bare RYTT envelope (unlike the 4Leibniz/Res-Nova artifacts)
        # carries no repo/commit provenance object of its own in the
        # real interchange.py shape read above — it is a local compiler
        # output, not a claim ledger entry. Callers that need document
        # provenance binding must wrap the envelope in a
        # document_provenance object explicitly (checked below); when
        # absent, this reports the absence rather than inventing one.
        doc_prov = raw.get("document_provenance")
        if isinstance(doc_prov, dict):
            return {
                "repo": doc_prov.get("repo") or doc_prov.get("repository"),
                "commit": doc_prov.get("commit") or doc_prov.get("commit_sha"),
                "path": doc_prov.get("path"),
            }
        return {"repo": None, "commit": None, "path": None}

    def run_gates(self, raw: dict[str, Any], *, policy: AdapterPolicy) -> list[Gate]:
        gates: list[Gate] = []

        gates.append(self._schema_shape_gate(raw))
        gates.append(self._required_fields_gate(raw))
        gates.append(self._token_shape_gate(raw))
        gates.append(self._metrics_consistency_gate(raw))
        gates.append(self._round_trip_consistency_gate(raw))
        gates.append(self._vocabulary_hash_gate(raw, policy))

        return gates

    # -- individual gates -------------------------------------------------

    def _schema_shape_gate(self, raw: dict[str, Any]) -> Gate:
        problems = []
        if raw.get("format") != "rytt":
            problems.append(f"format {raw.get('format')!r} is not 'rytt'")
        if raw.get("format_version") != SUPPORTED_FORMAT_VERSION:
            problems.append(
                f"format_version {raw.get('format_version')!r} != "
                f"{SUPPORTED_FORMAT_VERSION!r} (this adapter's supported version)"
            )
        if raw.get("spec_version") != SUPPORTED_SPEC_VERSION:
            problems.append(
                f"spec_version {raw.get('spec_version')!r} != "
                f"{SUPPORTED_SPEC_VERSION!r} (this adapter's supported version)"
            )
        if problems:
            return Gate("schema_shape", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "schema_shape",
            GateStatus.PASSED,
            f"format=rytt format_version={SUPPORTED_FORMAT_VERSION} "
            f"spec_version={SUPPORTED_SPEC_VERSION}",
        )

    def _required_fields_gate(self, raw: dict[str, Any]) -> Gate:
        problems = []
        for field_name in ("source_text", "encoded_display"):
            if not isinstance(raw.get(field_name), str):
                problems.append(f"missing or non-string field '{field_name}'")
        if not isinstance(raw.get("tokens"), list):
            problems.append("missing or non-list field 'tokens'")
        if not isinstance(raw.get("metrics"), dict):
            problems.append("missing or non-object field 'metrics'")
        if not isinstance(raw.get("verification"), dict):
            problems.append("missing or non-object field 'verification'")
        if problems:
            return Gate("required_fields", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "required_fields",
            GateStatus.PASSED,
            "source_text, encoded_display, tokens, metrics, verification all present",
        )

    def _token_shape_gate(self, raw: dict[str, Any]) -> Gate:
        tokens = raw.get("tokens")
        if not isinstance(tokens, list):
            return Gate(
                "token_shape",
                GateStatus.NOT_APPLICABLE,
                "no tokens list to check (already flagged by required_fields)",
            )
        problems = []
        for tok in tokens:
            if not isinstance(tok, dict):
                problems.append("token entry is not an object")
                continue
            idx = tok.get("index", "<unknown>")
            for field_name in _REQUIRED_TOKEN_FIELDS:
                if field_name not in tok:
                    problems.append(f"token[{idx}]: missing field '{field_name}'")
            kind = tok.get("kind")
            if kind is not None and kind not in _CONTROLLED_TOKEN_KINDS:
                problems.append(f"token[{idx}]: kind {kind!r} is not a controlled kind")
        if problems:
            return Gate("token_shape", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "token_shape",
            GateStatus.PASSED,
            f"{len(tokens)} token(s) all carry required fields and controlled kind",
        )

    def _metrics_consistency_gate(self, raw: dict[str, Any]) -> Gate:
        metrics = raw.get("metrics")
        tokens = raw.get("tokens")
        source_text = raw.get("source_text")
        if not isinstance(metrics, dict) or not isinstance(tokens, list):
            return Gate(
                "metrics_consistency",
                GateStatus.NOT_APPLICABLE,
                "metrics or tokens missing (already flagged by required_fields)",
            )
        problems = []
        declared_tokens = metrics.get("rytt_tokens")
        if declared_tokens != len(tokens):
            problems.append(
                f"metrics.rytt_tokens={declared_tokens!r} != len(tokens)={len(tokens)}"
            )
        declared_chords = metrics.get("chord_tokens")
        actual_chords = sum(
            1 for t in tokens if isinstance(t, dict) and t.get("is_chord")
        )
        if declared_chords != actual_chords:
            problems.append(
                f"metrics.chord_tokens={declared_chords!r} != counted {actual_chords}"
            )
        if isinstance(source_text, str):
            declared_chars = metrics.get("source_characters")
            if declared_chars != len(source_text):
                problems.append(
                    f"metrics.source_characters={declared_chars!r} != "
                    f"len(source_text)={len(source_text)}"
                )
            declared_bytes = metrics.get("source_utf8_bytes")
            actual_bytes = len(source_text.encode("utf-8"))
            if declared_bytes != actual_bytes:
                problems.append(
                    f"metrics.source_utf8_bytes={declared_bytes!r} != "
                    f"actual {actual_bytes}"
                )
        if problems:
            return Gate("metrics_consistency", GateStatus.FAILED, "; ".join(problems))
        return Gate(
            "metrics_consistency",
            GateStatus.PASSED,
            "declared metrics recomputed and matched from the envelope's own "
            "source_text/tokens (no RYTT grammar invoked)",
        )

    def _round_trip_consistency_gate(self, raw: dict[str, Any]) -> Gate:
        verification = raw.get("verification")
        source_text = raw.get("source_text")
        if not isinstance(verification, dict) or not isinstance(source_text, str):
            return Gate(
                "round_trip_consistency",
                GateStatus.NOT_APPLICABLE,
                "verification or source_text missing (already flagged by required_fields)",
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
                f"(actual equality={actual_match}); this is a data-only check, "
                "no RYTT grammar was invoked to re-derive decoded_text",
            )
        return Gate(
            "round_trip_consistency",
            GateStatus.PASSED,
            f"declared round_trip_exact={declared_flag} matches plain string "
            "comparison of source_text vs verification.decoded_text",
        )

    def _vocabulary_hash_gate(self, raw: dict[str, Any], policy: AdapterPolicy) -> Gate:
        declared = raw.get("vocabulary_sha256")
        expected = policy.expected_vocabulary_sha256.get(self.artifact_type)
        if declared == "unavailable":
            # This is RYTT's own upstream sentinel for "spec/vocabulary.json
            # was missing when the envelope was built" (interchange.py:
            # vocabulary_hash()). Never treat it as a pass — it declares
            # that no hash could even be computed upstream.
            return Gate(
                "vocabulary_hash",
                GateStatus.UNAVAILABLE,
                "vocabulary_sha256 is the literal 'unavailable' sentinel "
                "(spec/vocabulary.json was missing when RYTT built this "
                "envelope); no vocabulary integrity could be checked",
            )
        if not is_valid_sha256_hex(declared):
            return Gate(
                "vocabulary_hash",
                GateStatus.FAILED,
                f"vocabulary_sha256 {declared!r} is not a 64-hex-char SHA-256 digest",
            )
        if not expected:
            return Gate(
                "vocabulary_hash",
                GateStatus.UNAVAILABLE,
                f"vocabulary_sha256={declared} is a syntactically valid digest "
                "but no expected value is configured in policy "
                "(expected_vocabulary_sha256); nothing was actually verified "
                "against a reference spec/vocabulary.json",
            )
        if declared != expected:
            return Gate(
                "vocabulary_hash",
                GateStatus.FAILED,
                f"vocabulary_sha256={declared} does not match policy-configured "
                f"expected value {expected}",
            )
        return Gate(
            "vocabulary_hash",
            GateStatus.PASSED,
            f"vocabulary_sha256={declared} matches policy-configured expected value",
        )


register_adapter(RyttEnvelopeAdapter())
