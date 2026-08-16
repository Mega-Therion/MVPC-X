# MVPC-X Diamond Assurance Profile

## Purpose

MVPC-X is a verification and provenance protocol for human/AI collaboration. It does not treat an AI model, a single prover, a symbolic engine, or a human assertion as sufficient authority by itself.

The governing principle is:

> AI proposes. Machines verify. Humans audit. Evidence persists.

A claim may move through multiple assurance levels. A higher level never silently upgrades a lower level, and a failed or conflicting check is preserved as evidence.

## Assurance levels

### D0 — Proposed

A human or AI has proposed a claim, conjecture, formalization, proof strategy, or computational result. No authoritative verification has occurred.

### D1 — Reproducibly Computed

The result has been produced by a deterministic or controlled computational procedure with captured inputs, code identity, relevant parameters, and environment information.

D1 is computational evidence, not a formal proof.

### D2 — Formally Checked

A trusted formal kernel has checked a proof object for the exact formal proposition recorded in the claim manifest.

The evidence bundle MUST identify:

- formal proposition
- theorem/declaration
- proof artifact
- prover and kernel version
- dependency/toolchain identity
- admitted axioms or trusted assumptions
- verification result

### D3 — Hardened Formal Verification

D2 plus integrity and provenance controls:

- canonical claim identity
- content hashes
- immutable evidence references
- environment fingerprint
- dependency manifest
- axiom manifest
- explicit policy
- no hidden `sorry`/`admit`/unsafe escape path where prohibited by policy
- signed witness or equivalent authenticated provenance
- offline verification capability

### D4 — Independently Rechecked

D3 plus a materially independent verification path. Examples include an isolated second invocation, an independently implemented witness verifier, or a separate proof-checking process.

Independence MUST be recorded rather than inferred from the word `verified`.

### D5 — Cross-Foundation Verified

D4 plus independent formal verification of the same mathematical claim in another suitable logical foundation, when practical.

Examples include Lean/Mathlib plus Rocq, Isabelle, or Metamath. Cross-foundation verification is optional and claim-dependent; it is not required for every theorem.

### D6 — Publication Grade

D5 plus explicit human semantic review of:

- intended natural-language statement
- formal statement
- definitions
- assumptions
- scope
- material divergences between informal and formal statements
- interpretation of the result

The public evidence bundle MUST be reproducible and independently inspectable.

## Orthogonal dimensions

Assurance level is not a single universal truth score. MVPC-X records separate dimensions for:

- formal proof status
- computational evidence
- human attestation
- semantic/formalization review
- provenance integrity
- independence
- cross-foundation agreement
- reproducibility

A claim may therefore be, for example, D3 with strong computational corroboration but without cross-foundation verification.

## Forbidden shortcuts

The following MUST NOT upgrade assurance:

- model confidence
- majority vote among AI agents
- successful compilation of an unrelated artifact
- passing tests that do not exercise the claimed proposition
- a CAS simplification presented as a kernel proof
- a numerical experiment presented as a formal theorem
- a human signature without a defined review scope
- a prover's textual statement that a proof is complete

## Claim identity

Every authoritative result must bind together:

`natural claim -> formal proposition -> declaration/proof artifact -> verification environment -> evidence -> witness`

A valid proof of a different proposition is not evidence for the claim.

## Failure semantics

MVPC-X treats the following as first-class outcomes:

- `INCONCLUSIVE`
- `REJECTED`
- `UNSAFE_TO_VERIFY`
- `CONFLICTING_VERDICTS`
- `FORMALIZATION_MISMATCH`
- `ENVIRONMENT_MISMATCH`

Failed proof attempts and conflicting evidence SHOULD remain available as provenance rather than being discarded.

## Reference architecture

```text
Human intent
    |
    v
Claim manifest
    |
    +--> Formalization + semantic tests
    |
    +--> AI proof/search agents
    |
    +--> Deterministic provers
    |       +--> Lean / Mathlib
    |       +--> Rocq
    |       +--> Isabelle
    |       +--> Metamath
    |       +--> SMT / CAS / numerical engines
    |
    v
Evidence graph
    |
    v
Signed witness
    |
    v
Independent verification
    |
    v
Human interpretation / publication
```

## Design commitment

MVPC-X is intentionally prover-agnostic and model-agnostic. Lean/Mathlib is a flagship mathematical backend, not the definition of the protocol. AI systems are collaborators and search engines, never final authorities.
