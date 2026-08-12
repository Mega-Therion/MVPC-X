# Changelog

All notable changes to **MVPC-X** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
