# MVPC-X End-to-End Verification Protocol

## Governing rule

> AI proposes. Machines verify. Humans audit. Evidence persists.

MVPC-X treats a mathematical result as a chain of explicitly bound artifacts, not as a boolean `verified` flag.

## End-to-end chain

```text
human/AI intent
    |
    v
claim manifest
    |
    v
formalization review
    |
    +--> definitions
    +--> assumptions
    +--> semantic tests
    +--> divergences
    |
    v
claim binding digest
    |
    v
verification plan
    |
    +--> Lean / Mathlib
    +--> Rocq / Coq
    +--> Isabelle
    +--> deterministic computation
    +--> CAS / SMT / numerical checks
    +--> provenance / environment / signature checks
    |
    v
evidence graph / proof record
    |
    v
assurance derivation D0-D6
    |
    v
strict Ed25519 witness seal
    |
    v
offline independent verification
```

## The critical binding

For a formal result the witness must bind all of the following:

`natural statement -> formal statement -> exact declaration -> proof artifact hash -> verifier result`

A kernel-valid proof of a different proposition is not evidence for the claim.

## Formalization is a separate trust boundary

The system distinguishes proving the formal proposition from deciding whether the formal proposition faithfully captures the intended claim. Semantic tests, definitions, assumptions, and material divergences are recorded before a formal result can be treated as publication-grade evidence.

## Multi-prover semantics

Backends are selected from a claim's verification plan, not inferred solely from a file extension. Each target records its purpose, foundation, artifact, requiredness, and independence group. Missing or unexpected results are visible rather than silently ignored.

## Assurance

D0 Proposed

D1 Reproducibly Computed

D2 Formally Checked

D3 Hardened Formal Verification

D4 Independently Rechecked

D5 Cross-Foundation Verified

D6 Publication Grade

Higher levels require explicit evidence. AI confidence, majority vote, compilation of unrelated code, numerical sampling, or human approval alone never upgrades a claim to formal proof.

## Sealing

The strict witness-sealing path uses Ed25519 and canonical JSON. It refuses to silently downgrade to HMAC when the asymmetric crypto dependency is unavailable. The sealed payload contains its canonical content hash and public verification key, enabling offline verification.

## Failure is evidence

`INCONCLUSIVE`, `REJECTED`, `UNSAFE_TO_VERIFY`, `CONFLICTING_VERDICTS`, and formalization mismatches remain first-class recorded outcomes. Failed attempts are not erased simply because a later attempt succeeded.
