# Changelog

All notable changes to **MVPC-X** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [7.0.0] - 2026-08-12

### Initial Sovereign Release of MVPC-X

#### Features
- **Core Primitives:** Introduced atomic `Claim`, `Evidence`, `Verification`, `Provenance`, and `Witness` data structures.
- **Trust & Attestation Model:** Evaluates claims into `VERIFIED`, `CONDITIONAL`, `REJECTED`, and `UNVERIFIED` states proportional to verified mechanical checks.
- **Policy Engine:** Supports `PERMISSIVE`, `DEFAULT`, and `STRICT` policy levels with customizable axiom allowlists and pattern blocking.
- **Multi-Backend Engine:**
  - **Lean 4 Backend:** Static pattern analysis for `sorry`, `admit`, `native_decide`, and `axiom`, plus native compilation support.
  - **Coq Backend:** Static analysis for `admit`, `Admitted`, and native `coqc` compilation.
  - **Python Backend:** AST-based safety checker for unsafe execution (`exec`, `eval`, shell injection) and sandboxed execution.
  - **Generic Backend:** Fallback cryptographic hasher for arbitrary unstructured files.
- **Cryptographic Witness Chains:** Generates self-verifying SHA-256 witness records detailing exact environment, policy, checks performed, and evidence.
- **CLI Interface:** Provides `mvpc audit`, `mvpc witness verify`, directory scanning, and JSON export.
- **Zero-Dependency Core:** Entire core library built on standard Python 3.10+ stdlib.

#### Documentation & Governance
- Added **The Sovereign Covenant** (`COVENANT.md`).
- Added comprehensive Architecture Specification (`ARCHITECTURE.md`).
- Added Threat Model and Security Guidelines (`SECURITY.md`).
- Added Community Contribution Guide (`CONTRIBUTING.md`).
- Added Development Roadmap (`ROADMAP.md`).
