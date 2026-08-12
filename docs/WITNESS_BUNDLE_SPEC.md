# MVPC-X Witness Bundle Spec

## Format version

`1.0.0`

## Layout

```
claim.mvpcx/
  manifest.json
  claim.json
  claim.formal.*
  evidence/
  policy.json
  environment.lock
  prover-logs/
  witness.json
  attestations/
  sbom.cdx.json
  signatures/
  traceability.json
  failure-record.json   # only on failure
  tcb.json
```

## Canonical JSON

Sorted keys, compact separators, UTF-8, ISO-8601 UTC datetimes, SHA-256 hashes, Ed25519 signatures preferred.

## Integrity rules

1. Signed witnesses are immutable.
2. Failures create new failure records; they never rewrite witnesses.
3. Chains link via previous_witness_hash; forks are explicit.
4. Offline verify recomputes hashes and checks signatures before trusting a verdict.

```bash
mvpc verify-bundle claim.mvpcx --offline
```
