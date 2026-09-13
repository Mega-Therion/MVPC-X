# External Evidence Artifacts (issue #8)

`mvpc.external_artifacts` verifies claim/evidence artifacts produced by
*other* repositories — 4Leibniz's formal-claims catalog and Res-Nova's
Evidence Atlas / claim ledger — against local, versioned schema and
provenance rules.

## What a passing verdict means, and what it never means

A passing MVPC-X verdict on an external artifact means exactly this:

> This artifact satisfied the configured schema, integrity, provenance,
> and evidence-linkage gates.

It never means:

> The underlying theorem/physics claim is independently proven true.

MVPC-X, through this module, verifies artifact shape/version, canonical
content identity, declared source provenance, required evidence fields,
declared check/gate outcomes, and witness-bundle integrity. It is never
the source of truth for Lean theorem truth, scientific/physical truth,
RYTT grammar, Res-Nova epistemic interpretation, or AEON governance
policy. Upstream statuses (`proved`, `conditional`, `open`, `refuted`,
`proposal`, `derived`, `empirically_supported`, ...) are always preserved
verbatim; nothing here promotes or rewrites them.

## Four things this is not the same as

| Layer | What it is | Where it lives |
|---|---|---|
| Lean toolchain run | An actual `lake build` / `lean` invocation checking a proof | 4Leibniz's own CI, never MVPC-X |
| Upstream declared verification record | A JSON field (`verification.project_check`, `falsifiability.current_result`, ...) that *claims* a check happened | Inside the artifact file itself |
| MVPC-X integrity verdict | "This declared record is internally consistent, complete, and provenance-bound" | This module's `Gate`/`ArtifactVerificationResult` |
| Empirical/reproducibility claim | "This matches the physical universe" | Never asserted by MVPC-X |

MVPC-X never runs Lean (or any other checker) in v1. It only checks that
a catalog's *declared* evidence is complete, internally consistent, and
correctly bound to a provenance record — the same fail-closed posture the
rest of MVPC-X takes toward "never manufacture certainty" (see
`COVENANT.md` §1).

## Supported v1 artifact types and versions

The registry (`mvpc.external_artifacts.registry`) is keyed by a schema
identity string. For the 4Leibniz and Res-Nova adapters that identity is
the artifact's own declared top-level `schema_version` string, used
verbatim. RYTT's own envelope format (see below) has no `schema_version`
field at all — its identity is a `("format", "format_version",
"spec_version")` triple instead — so
`mvpc.external_artifacts.verify._resolve_schema_identity` synthesizes the
equivalent dispatch key for that one shape, without changing how any
`schema_version`-bearing artifact resolves:

| Dispatch identity | Artifact type | Adapter |
|---|---|---|
| `4leibniz-formal-claims-catalog-v1` | `4leibniz-formal-claims-catalog` | `leibniz_adapter.LeibnizCatalogAdapter` |
| `res-nova-claim-ledger-v1` | `resnova-evidence-atlas` | `resnova_adapter.ResNovaAtlasAdapter` |
| `rytt-envelope-v1` (synthesized from `format=="rytt"`, `format_version=="0.1"`, `spec_version=="0.1"`) | `rytt-envelope` | `rytt_adapter.RyttEnvelopeAdapter` |
| `rytt-conformance-run-v1` | `rytt-conformance-run` | `rytt_conformance_adapter.RyttConformanceRunAdapter` |
| `rytt-zip-bundle-v1` (reached only via `verify_zip_bundle_file`, never through JSON dispatch) | `rytt-zip-bundle` | `rytt_bundle_adapter.RyttZipBundleAdapter` |

Any other identity — or a missing/malformed one — raises
`UnsupportedArtifactError`. There is no generic success fallback: an
unrecognized artifact is a specific, distinct failure mode, never a pass.
A future RYTT `format_version`/`spec_version` bump (e.g. `"0.2"`) is
deliberately **not** absorbed by the v1 adapter — it falls straight
through to `UnsupportedArtifactError` rather than being silently graded
by rules written for a different version.

### 4Leibniz formal-claims catalog v1

Schema shape (per issue #8's documented convention; 4Leibniz issue #11
was not fetchable while this adapter was written, so this is an explicit
assumption, not a confirmed fact):

```json
{
  "schema_version": "4leibniz-formal-claims-catalog-v1",
  "document_provenance": {"repo": "...", "commit": "<40-hex>", "path": "..."},
  "claims": [
    {
      "claim_id": "...",
      "module": "...",
      "declaration": "...",
      "status": "proved | conditional | informal | open_problem",
      "proof_source": {"repo": "...", "commit": "<40-hex>", "path": "..."},
      "verification": {
        "lean_toolchain": "...",
        "project_check": "passed | failed | unavailable | not_applicable",
        "declaration_check": "passed | failed | unavailable | not_applicable",
        "sorry_count": 0,
        "axiom_dependencies": [],
        "checked_at": "..."
      }
    }
  ]
}
```

Gates: `schema_shape`, `document_provenance`, `claim_ids`,
`claim_required_fields`, `claim_provenance_agreement`,
`proved_claims_have_verification`. A claim labelled `proved` with an
empty/missing verification record, or with `project_check`/
`declaration_check` in `failed`/`unavailable`, fails the artifact.

### Res-Nova Evidence Atlas / claim ledger v1

Schema shape matches the real delivered reference file
(`evidence/v1/claim-ledger.json`, not yet merged to Res-Nova main at the
time this adapter was written): a top-level `schema_version` string
(`res-nova-claim-ledger-v1`), a `generation` block, and per-claim
`epistemic_status`, `source_locators`, `evidence_references`,
`falsifiability`, `assumptions`, and `provenance` fields. **Discrepancy
note:** the real file has no top-level `document_provenance` object —
only per-claim `provenance: {repository, commit_sha}` and a
`generation.source_commit_sha`. This adapter accepts an explicit
`document_provenance` object when present (used by this repo's own
fixtures) and otherwise falls back to `generation.source_commit_sha` plus
the majority per-claim `provenance.repository`, flagging the fallback in
the gate detail string rather than silently treating it as equivalent to
an explicit declaration.

Controlled `epistemic_status` values: `derived`, `empirically_supported`,
`conditional`, `proposal`, `open`, `refuted`. Only `derived`, `conditional`,
`open`, and `refuted` were observed in the real reference file;
`empirically_supported` and `proposal` are supported per the documented
six-way vocabulary but were not observed there.

Status-specific gates (each `NOT_APPLICABLE`, not silently `PASSED`, when
no claim of that status is present):

- `derived_requires_derivation_evidence`
- `empirically_supported_requires_test_record`
- `conditional_names_conditions`
- `proposal_not_overclaimed`
- `open_identifies_unresolved_problem`
- `refuted_retained_with_evidence`

Every claim — including `open` and `refuted` ones — is carried through
verbatim into the sealed witness bundle's `backend_result.claims_preserved`
list. Nothing is silently dropped or promoted.

## Local-file-only policy (v1)

No network fetch, no GitHub API call, no database write, no automatic
artifact download. `mvpc verify artifact <path>` only ever reads a local
file at `<path>`. Passing a URL is rejected the same way any other
malformed local path is (the file will not exist locally).

## CLI usage

```
mvpc verify artifact <path> [--format text|json] [--output <dir-or-file>] [--overwrite] [--policy <path>]
```

- `--format text` (default) prints artifact type/version, canonical hash,
  provenance, gate-by-gate status, verdict, and the witness bundle path.
- `--format json` prints the full structured `ArtifactVerificationResult`
  (see schema below) to stdout.
- `--output <dir>` writes the sealed witness bundle into that directory
  under a deterministic filename `<stem>.witness.<hash-prefix>.json`
  derived from the artifact's own canonical hash — re-running against
  byte-identical input reproduces the same filename, and running against
  different input never collides with a prior bundle for different
  content. `--output <file>` writes to that exact path.
- The command never overwrites an existing witness bundle file unless
  `--overwrite` is passed explicitly.
- Exit codes: `0` on a `passed` verdict; `1` on `failed`/`unavailable`/
  `not_applicable` overall verdicts; `2` on a missing file, malformed
  JSON, or an unsupported schema identity (a distinct failure mode from
  "verified and failed").
- `--policy <path>` points at a JSON file with `expected_repos` (map of
  artifact type to the exact repo string required),
  `require_claim_provenance_match` (bool), `policy_version` (string), and
  `expected_vocabulary_sha256` (map of artifact type — currently only
  `rytt-envelope` — to the required 64-hex-char SHA-256 digest of
  `spec/vocabulary.json`; with no entry configured the `vocabulary_hash`
  gate reports `unavailable`, never `passed`).
- `<path>` ending in `.zip` is auto-detected as a RYTT CLI verified
  artifact bundle (`verify_zip_bundle_file`) rather than a JSON document;
  every other extension goes through the JSON path.

## Inspecting a witness bundle

The written witness bundle file is JSON with five top-level keys:

- `generated_at`: wall-clock **output metadata** for this CLI run only.
  Never part of the canonical identity.
- `manifest` / `witness` / `tcb` / `policy`: MVPC-X's existing witness
  bundle primitives (`mvpc.witness_bundle.WitnessBundle`), reused as-is.
  `witness.backend_result` carries the full gate list, provenance, and
  every preserved claim (including `open`/`refuted` ones).
- `result`: the deterministic machine-readable verification record (see
  schema below).

Two runs over semantically identical artifact content (same values,
different JSON key order) produce byte-identical `canonical_hash`,
`witness.witness_id`, `witness` hash, `tcb` hash, `policy` hash, and
bundle `manifest_hash()`/`composite_hash()`. This is achieved by pinning
`created_at` on the TCB/policy/witness/bundle objects to a fixed sentinel
(`1970-01-01T00:00:00Z`) rather than wall-clock time — that sentinel is
canonical identity plumbing, not a claim about when anything happened;
the real wall-clock time of a CLI run lives only in the output file's
`generated_at` field.

## Deterministic result schema

```json
{
  "verifier": {"name": "mvpc-x", "version": "<package version>"},
  "artifact": {
    "type": "<adapter artifact_type>",
    "schema_id": "<schema_version string>",
    "schema_version": "<schema_version string>",
    "source_path": "<local input path>",
    "canonical_hash": "<sha256 over canonical JSON of the raw artifact>",
    "provenance": {"repo": "...", "commit": "...", "path": "..."}
  },
  "gates": [{"name": "...", "status": "passed|failed|unavailable|not_applicable", "detail": "..."}],
  "verdict": "passed|failed|unavailable|not_applicable",
  "policy_version": "external-artifacts-v1"
}
```

## Failure semantics

- **Unsupported schema/artifact type**: `UnsupportedArtifactError`, CLI
  exit code `2`. Never rendered as a pass.
- **Malformed JSON / non-object top level**: `MalformedArtifactError`,
  exit code `2`.
- **Any gate `FAILED`**: overall verdict `failed`, exit code `1`.
- **Any gate `UNAVAILABLE`** (declared-but-unchecked evidence): overall
  verdict `unavailable`, exit code `1`. Never treated as passed.
- **All gates `NOT_APPLICABLE`** (nothing in the artifact triggered any
  check): overall verdict `not_applicable`, exit code `1`. An artifact
  that checked nothing does not get to claim it passed something.
- **Every other case** (all gates `passed` or a legitimate mix of
  `passed`/`not_applicable`): overall verdict `passed`, exit code `0`.

## RYTT adapters (issue #7)

MVPC-X stays standalone claim-verification infrastructure: RYTT is never
merged into this repo, and none of the three adapters below import,
fork, or re-execute RYTT's own grammar/compiler
(`rytt.compiler.RyttCompiler`). Per RYTT's own stated contract ("RYTT
publishes the JSON-first portable API. Downstream crates consume it;
they do not fork the grammar"), every gate below is either a structural/
schema check or a plain-data cross-check (string/JSON equality, SHA-256
of local bytes) — never a re-derivation of RYTT's encode/decode.

Schema ground truth for all three adapters was read directly from the
RYTT-Sovereign-Semiotics repo at commit
`aaf77db4666c62c57878e7c7a5f11dbd1754cf5b` (the `main` branch HEAD as
checked out locally when these adapters were written). This was **not**
independently confirmed to be the same commit as the short hash
`c963830` cited in issue #7's own text — that identifier was never
resolved locally, so its relationship to `aaf77db...` is unverified, not
assumed equal.

**Ground-truth-vs-issue-text correction:** issue #7 asks for "declared
BLAKE3 envelope hashes." The real artifact format
(`src/rytt/interchange.py::build_envelope()`/`vocabulary_hash()`) hashes
with plain `hashlib.sha256` under the field name `vocabulary_sha256`.
No `blake3` dependency exists anywhere in MVPC-X, and none was added —
these adapters verify what RYTT actually writes (SHA-256), following the
same "ground truth overrides an unverified issue-text assumption"
precedent as the Res-Nova adapter's own documented schema discrepancy.

### RYTT envelope v1 (`rytt-envelope-v1`)

Verifies a single compiled RYTT envelope
(`format`/`format_version`/`spec_version`/`vocabulary_sha256`/
`source_text`/`encoded_display`/`tokens`/`metrics`/`verification`, per
`build_envelope()`). Gates: `schema_shape`, `required_fields`,
`token_shape`, `metrics_consistency` (recomputes `rytt_tokens`,
`chord_tokens`, `source_characters`, `source_utf8_bytes` from the
envelope's own `source_text`/`tokens` and compares), `round_trip_consistency`
(compares the declared `verification.round_trip_exact` flag against a
plain string comparison of `source_text` vs `verification.decoded_text`
— no grammar invoked), and `vocabulary_hash`.

The `vocabulary_hash` gate is the one place upstream RYTT silently
degrades: `vocabulary_hash()` in `interchange.py` writes the literal
string `"unavailable"` when `spec/vocabulary.json` is missing at build
time, and RYTT's own `verify_envelope()` accepts that sentinel as valid.
This adapter does not inherit that: `vocabulary_sha256 == "unavailable"`
is `GateStatus.UNAVAILABLE`, and a syntactically valid digest with no
matching value configured in `AdapterPolicy.expected_vocabulary_sha256`
is *also* `GateStatus.UNAVAILABLE` (nothing was actually checked against
a reference file), never `PASSED`. Only a digest matching a configured
`expected_vocabulary_sha256[artifact_type]` value passes.

### RYTT conformance-run v1 (`rytt-conformance-run-v1`)

**This schema is designed here, not fetched** — flagged exactly like the
4Leibniz adapter's own documented assumption. The real RYTT repo has
`conformance/vectors.json` (7 reference vectors) and
`scripts/verify_conformance.py`, which replays every vector and prints
pass/fail, but persists no structured report artifact anywhere. This
adapter defines the schema for a *hypothetical* persisted replay report
an operator/CI job could emit: `document_provenance`, `spec_version`,
`vectors_reference` (`repo`/`commit`/`path`/`local_copy_path`/`format`/
`version`/`sha256`), `results` (per-vector `id`/`source`/
`encoded_display`/`decoded`/`token_count`/`passed`), and `summary`
(`total`/`passed`/`failed`).

Per issue #7 scope item 2, MVPC-X cannot re-run RYTT's encode/decode
without forking its grammar, which is explicitly out of scope. This
adapter therefore implements the issue's named alternative
("verify the DECLARED replay result's internal consistency and
hash-binding instead of re-executing the encoding"): it loads a local
copy of `conformance/vectors.json` (path given by
`vectors_reference.local_copy_path`, never fetched over the network),
records/checks its SHA-256, and requires every declared `results[i]`
entry to reproduce that vector's `source`/`encoded_display`/`decoded`/
`token_count` byte-for-byte (`declared_replay_matches_reference`);
requires full, non-duplicated vector coverage (`vector_coverage`);
recomputes each `passed` flag from that same entry's own declared fields
rather than trusting the boolean (`passed_flag_consistency`); and checks
`summary` arithmetic against the `results` array
(`summary_consistency`).

### RYTT CLI ZIP bundle v1 (`rytt-zip-bundle-v1`)

Schema ground truth, fetched: `export_bundle()` in `interchange.py`
writes a ZIP with `artifact.json`, `source.txt`, `encoded.rytt`,
`trace.json`, `metrics.json`, `verification.json`, `README.md` — there
is no separate manifest/hash-list file in the real format. The "internal
hash manifest" self-consistency issue #7 scope item 3 asks for is, in
this real shape, cross-member consistency: `member_cross_consistency`
checks that `source.txt`/`encoded.rytt`/`trace.json`/`metrics.json`/
`verification.json` each agree byte-for-byte (text members) or
structurally (JSON members) with the corresponding field embedded in
`artifact.json`. `required_members` checks all six required members are
present exactly once (a duplicate member name is itself flagged as a
tamper vector, since `zipfile.ZipFile.read()` silently returns only the
last entry for a duplicate name). `round_trip_consistency` repeats the
envelope adapter's plain-string round-trip check against the bundled
`artifact.json`.

This is the one place the existing registry needed a **minimal,
documented extension**, since a ZIP is not a JSON document and cannot go
through `verify_artifact_file`'s `json.loads()` path at all:

- `mvpc.external_artifacts.verify.load_zip_bundle()` reads the archive
  into a synthetic `{"_member_names": [...], "_members": {...}}` dict
  (guarding against absolute/`..` member-name path traversal, and
  surfacing a corrupt/non-ZIP file as `ZipArtifactError`, a new
  exception distinct from `MalformedArtifactError` so callers can tell
  "not JSON" apart from "not a valid ZIP").
- `verify_zip_bundle_file()` calls that, then dispatches through the
  *same* `get_adapter("rytt-zip-bundle-v1")` registry lookup and the
  same `_verify_resolved()` tail (canonical hash, witness sealing) as
  every other adapter — so `list_supported()` and CLI help stay
  accurate, and this adapter is not a disconnected bolt-on.
- `cli_support.run_verify_artifact` auto-detects `.zip` vs `.json` by
  file extension and routes to `verify_zip_bundle_file` or
  `verify_artifact_file` accordingly; `ZipArtifactError` is caught
  alongside the three pre-existing input-error exceptions and reported
  as CLI exit code `2`, the same class as a malformed/unsupported JSON
  artifact.

### Explicitly deferred: Supabase (`rytt_traces`, `rytt_conformance_runs`, `rytt_benchmark_metrics`)

Issue #7's full text names three Supabase tables on
`supabase-bisque-ball` as part of its audit surface. **None of that is
implemented in this pass, on purpose.** No adapter, CLI path, or test in
`mvpc.external_artifacts` makes a network call, opens a database
connection, imports a Supabase client library, or reads any
credential/token/`.env` value. This mirrors the same "local-file-only in
v1" boundary the 4Leibniz and Res-Nova adapters already drew for their
own upstream repos.

Reaching those three tables requires live Supabase credentials and is a
separate, explicit approval decision — not something this module should
acquire silently as a side effect of adding local-file RYTT support. A
future phase would need, at minimum: a read-only Supabase service
role/anon key scoped to those three tables, a decision on how a live DB
row's provenance is bound into the existing `ArtifactVerificationResult`/
witness-bundle shape (the current model assumes a `source_path` on local
disk), and a policy decision on whether a live query result can ever
carry the same evidentiary weight as a sealed local-file witness bundle
given it can change out from under a later re-verification. None of that
is decided here.
