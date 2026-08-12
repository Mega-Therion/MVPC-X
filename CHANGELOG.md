# Changelog

All notable changes to **MVPC-X** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [7.2.0] - 2026-08-12

### Full works: Lean gold standard, covenant constitution, real tests, golden demo

#### Features
- **Lean backend gold standard:** Comment stripping; depth-aware theorem binder/statement scan; bare `axiom` / `unsafe` / tautology traps; env probe (lake/mathlib/version); native `lake env lean` / `lean` with `#print axioms`; kernel allowlist + `sorryAx` / `Lean.ofReduceBool`; optional Z3 vacuous-hypothesis and SymPy identity layers.
- **Covenant constitution:** `COVENANT.md` expanded into the full biomechanical human-AI standard (roles, attestation law, witness law, prohibited behaviors).
- **Golden witness demo:** `examples/golden/` with README + `extract_and_attest.py` end-to-end path.
- **Explanations:** New Lean codes (`LEAN_KERNEL_SORRY_AX`, `LEAN_AXIOM_SMUGGLE`, `LEAN_TAUTOLOGY`, `LEAN_Z3_VACUOUS`, `LEAN_SYMPY_MISMATCH`, `LEAN_KERNEL_NEVER_RAN`, `LEAN_NO_LAKE_PROJECT`, and related).

#### Tests
- Replaced stub tests in `test_claim`, `test_evidence`, `test_hashing`, `test_trust`, `test_witness` with real assertions (serialization, hash tamper detection, witness reseal on human attestation).
- Added fixtures `tautology.lean`, `vacuous.lean`.

---

## [7.1.0] - 2026-08-12

### Biomechanical and Multi-Prover Integration

#### Features
- **Isabelle/HOL Backend (`mvpc.backends.isabelle`)**
- **Inline Symbolic, SMT and Numeric Math Claim Engine** (`# MVPC-CLAIM` / `# BIOMECH-CLAIM`)
- **Human Attestation CLI Workflow (`mvpc attest`)**
- **Pedagogical Remediation Dictionary (`mvpc.explanations`)**
- **Enhanced Governance CLI Flags**
- **Timezone-aware UTC datetimes**

---

## [7.0.0] - 2026-08-12

### Initial Sovereign Release of MVPC-X

#### Features
- **Core Primitives:** Claim, Evidence, Verification, Provenance, and Witness
- **Trust and Attestation Model:** VERIFIED, CONDITIONAL, REJECTED, UNVERIFIED
- **Policy Engine:** PERMISSIVE, DEFAULT, STRICT
- **Multi-Backend Engine:** Lean 4, Coq, Python, Generic hasher
- **Cryptographic Witness Chains**
- **CLI:** `mvpc audit`, `mvpc witness verify`, directory scanning, JSON export
