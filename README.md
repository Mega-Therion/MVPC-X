# MVPC-X

Sovereign claim-verification infrastructure. Turns claims into auditable evidence chains.

![MVPC-X Artifact Verification Lifecycle](docs/visuals/witness-bundle-lifecycle.svg)

## System Role

MVPC-X operates as an independent external auditor across the Chyren constellation. It validates artifact integrity, computes canonical content hashes, evaluates declared validation gates, and issues tamper-evident witness bundles.

MVPC-X does **not** evaluate substantive truth:
- It does not verify the truth of physical hypotheses in Res-Nova.
- It does not replace Lean 4 compilation in 4Leibniz.
- It does not own or modify the RYTT token grammar.
- A verdict of `passed` certifies only that configured artifact gates and provenance checks succeeded fail-closed.

## Active Workstreams

- **Issue #8**: External evidence artifacts v1 — fixture-backed verification adapters for 4Leibniz formal-claim catalogs and Res-Nova Evidence Atlas ledgers with deterministic witness bundles.
- **Issue #7**: External audit and replay verification for RYTT v0.2.0 envelopes and conformance vectors (`conformance/vectors.json`).

## Architecture

```
Artifact Ingest ──► Schema Check ──► Canonicalization ──► Gate Evaluation ──► Witness Bundle
 (JSON / Path)      (v1 Schemas)       (BLAKE3 Hash)       (Pass/Fail/Unavail)   (Signed Seal)
```

1. **Ingest**: Consumes local versioned artifacts without silent network fetching.
2. **Canonicalize**: Normalizes payload representation to produce deterministic hashes.
3. **Gates**: Evaluates provenance, required locators, and verification records. Missing or unparseable fields fail closed.
4. **Witness**: Packages gate results, verifier version, and input hash into a sealed, replayable bundle.

## Cross-Repository Contracts

- **4Leibniz**: Consumes `artifacts/v1/formal-claims.json`. Requires immutable commit SHA, module path, and Lean toolchain verification record for any `proved` claim.
- **Res-Nova**: Consumes `evidence/v1/claim-ledger.json`. Enforces status-specific evidence rules for `derived` and `empirically_supported` entries.
- **RYTT**: Audits conformance vectors and PUA stream round-trips via `integration/4leibniz_bridge.json`.

## Quick Start

```bash
# Run test suite
pytest

# Verify an artifact locally
python -m mvpc.cli verify artifact <path-to-artifact.json>
```

## Standards

- **Fail-closed**: Any unknown, skipped, or unparseable check is marked `unavailable` or `failed`, never `passed`.
- **Standalone**: No runtime dependency on upstream compiler toolchains.
- **No status inflation**: Upstream statuses (`conditional`, `proposal`, `open`, `refuted`) are preserved verbatim.
