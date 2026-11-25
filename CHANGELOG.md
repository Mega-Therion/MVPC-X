# Changelog

All notable changes to **MVPC-X** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **SAMO §8 Target 5 (BLK-1615) — mechanical witness feed:** new `mvpc.witness_feed` module projects sealed MVPC-X witnesses into the versioned feed document (`mvpc-x/samo-v-mech-feed/1`) that supplies `V_mech(x)`, the deterministic verification yield of the SAMO §4 artifact selection function `F(x) = V_hard · V_mech · B_bridge · H_local`. Fail-closed semantics: a witness whose self-hash does not verify, or that carries a VIOLATION finding, earns zero passed checks; checks that could not run count in the denominator and their names are always surfaced (`checks_unavailable` is never hidden). Exported as `mechanical_witness_feed` / `mechanical_witness_feed_json`; tests in `tests/test_witness_feed.py`.
- **Covenant §13 — Article V adopted:** Article V of the *Declaration of Interdependence*, as proposed in the S.A.M.O. Specification v2.0 §7, is adopted verbatim as COVENANT.md §13. Per the covenant's own §11 amendment rules this carries a covenant version bump (7.2 → 7.3), this changelog entry, and an explicit callout in the PR description. Adoption is additive; §§0–12 are unchanged and “never manufacture certainty” is not weakened.

---

## [7.3.0] - 2026-08-12

### Preflight, scaffold, and system self-integrity

#### Security
- **System self-fingerprint:** SHA-256 over installed `mvpc/**/*.py` captured **before** artifact ingest, checked **mid-run**, verified **after** processing. Mutation → `SYSTEM_INTEGRITY_FAILURE`.
- **Artifact pre/post hash** secondary tamper signal → `ARTIFACT_MUTATION`.
- **Intake guards:** max size, symlink policy, blocked executable extensions.
- CLI: `mvpc integrity`, `mvpc integrity --verify-twice`.

#### UX
- **`mvpc preflight`** — classify backend, probe tools, structure score, readiness enum.
- **`mvpc scaffold`** — lean / coq / isabelle / python-math / claim templates.
- **`docs/INPUT_CONTRACT.md`** — open ingest + structured upgrade path.
- SECURITY.md documents the self-seal threat model.

#### Tests
- `tests/test_security.py`, `tests/test_preflight.py`.

---

## [7.2.0] - 2026-08-12

### Lean gold standard, covenant constitution, real tests, golden demo

- Full Lean multi-engine backend; expanded COVENANT.md; golden demo; real primitive tests.

---

## [7.1.0] - 2026-08-12

### Isabelle, math claims, human attestation, explanations

---

## [7.0.0] - 2026-08-12

### Initial sovereign release
