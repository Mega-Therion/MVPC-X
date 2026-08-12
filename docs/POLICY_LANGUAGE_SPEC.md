# MVPC-X Policy Language Spec

Policies are declarative JSON manifests, not executable plugins.

## Required fields

- policy_id, version, level
- minimum_verdict
- require_human_attestation
- require_ai_provenance_label
- reject_on_inconclusive, reject_on_timeout
- require_signed_witness
- allowed_backends
- max_timeout_seconds, max_memory_mb, max_file_size_mb, max_process_count
- network_allowed (default false)
- optional signing_key_id / signature

## Levels

- **PERMISSIVE** — minimum EXECUTION_OBSERVED
- **DEFAULT** — minimum EVIDENCE_SUPPORTED; signed witness; AI provenance
- **STRICT** — minimum FORMALLY_CHECKED; human attestation; formal backends only
- **CUSTOM** — validated user values

Policy content is hash-addressed (signature excluded) and recorded in every witness.
