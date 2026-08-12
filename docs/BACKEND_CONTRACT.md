# MVPC-X Backend Contract

Backends implement four phases. None emits a product-level "VERIFIED" label; the kernel derives the verdict after policy validation.

1. **prepare** — normalize claim/evidence; label AI_PROPOSED formalizations; no prover execution.
2. **execute** — sandboxed run, no network by default, resource limits, full logs, binary hash capture; timeout => INCONCLUSIVE.
3. **validate** — map raw output to taxonomy; detect sorry/admit/axioms/vacuity/unsound options.
4. **attest** — signed backend record with version, binary hash, log hash, resource profile.

## Categories

| Category | Examples | Max verdict |
|---|---|---|
| Mechanical | Lean, Coq, Isabelle | FORMALLY_CHECKED |
| Computation | SymPy, Z3, NumPy | COMPUTATION_VERIFIED |
| Execution observation | generic/bash | EXECUTION_OBSERVED |

## Sandbox minimums

No network, read-only inputs, ephemeral workspace, no secret inheritance, allowlisted binaries, argv arrays only (never shell=True), captured stdout/stderr/exit/signal/resources.
