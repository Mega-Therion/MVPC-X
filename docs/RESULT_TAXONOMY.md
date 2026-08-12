# MVPC-X Result Taxonomy

## Atomic verdicts

1. **FORMALLY_CHECKED** — Formal checker accepted a theorem under captured assumptions.
2. **COMPUTATION_VERIFIED** — Deterministic computation/identity passed under a specified environment.
3. **EXECUTION_OBSERVED** — Controlled execution emitted recorded output; not proof.
4. **EVIDENCE_SUPPORTED** — Evidence met policy threshold; not proof.
5. **HUMAN_ATTESTED** — Scoped signed statement; not proof.
6. **INCONCLUSIVE** — Insufficient evidence, formalization, or resources.
7. **REJECTED** — Policy, integrity, or backend rejected the artifact.
8. **UNSAFE_TO_VERIFY** — Intake, sandbox, dependency, or integrity requirements unmet.
9. **CONFLICTING_VERDICTS** — Independent backends/runs disagree.

## Rendering rules

- Always show the full verdict label and description.
- Never emit a bare "verified" badge for non-truth-implying verdicts.
- Truth-implying results must include assumptions and limitations.

## Legacy migration

| Legacy | New |
|---|---|
| VERIFIED | FORMALLY_CHECKED |
| CONDITIONAL | EVIDENCE_SUPPORTED |
| REJECTED | REJECTED |
| UNVERIFIED | INCONCLUSIVE |
