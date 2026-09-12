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

The registry (`mvpc.external_artifacts.registry`) is keyed by an
artifact's own declared `schema_version` string, which doubles as a
combined schema-id+version identity:

| `schema_version` value | Artifact type | Adapter |
|---|---|---|
| `4leibniz-formal-claims-catalog-v1` | `4leibniz-formal-claims-catalog` | `leibniz_adapter.LeibnizCatalogAdapter` |
| `res-nova-claim-ledger-v1` | `resnova-evidence-atlas` | `resnova_adapter.ResNovaAtlasAdapter` |

Any other `schema_version` value — or a missing/malformed one — raises
`UnsupportedArtifactError`. There is no generic success fallback: an
unrecognized artifact is a specific, distinct failure mode, never a pass.

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
  `require_claim_provenance_match` (bool), and `policy_version` (string).

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

## How a future RYTT adapter (issue #7) plugs into this registry

Issue #7 covers RYTT envelope/replay auditing as its own consumer
adapter, and explicitly must not be merged into or duplicated by this
module (RYTT owns its own grammar). If a RYTT artifact adapter is later
built against this same registry, it follows the same three-step pattern
as `leibniz_adapter.py` / `resnova_adapter.py`:

1. Implement the `ArtifactAdapter` protocol (`mvpc.external_artifacts.registry`):
   `artifact_type`, `supported_schema_identities`, `parse`,
   `document_provenance`, `run_gates`.
2. Call `register_adapter(YourAdapter())` at module import time.
3. Import that module for its registration side effect from
   `mvpc/external_artifacts/__init__.py`, exactly as the two existing
   adapters are imported there.

No changes to `mvpc.external_artifacts.verify`, `cli_support.py`, or
`mvpc.cli` are needed — `verify_artifact_file` dispatches purely on the
artifact's own declared `schema_version` string, so a new adapter is a
strict, additive registration, never a modification of RYTT's existing
issue #7 surface or of the other two adapters.
