# Changelog

All notable changes to **MVPC-X** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [7.1.0] - 2026-08-12

### Biomechanical & Multi-Prover Integration

#### Features
- **Isabelle/HOL Backend (`mvpc.backends.isabelle`):** Full integration with Isabelle theory (`.thy`) and session (`ROOT`) build auditing with static AST traps for `sorry`, `oops`, and `axiomatization`.
- **Inline Symbolic, SMT & Numeric Math Claim Engine:** Enhanced Python backend to parse inline `# MVPC-CLAIM` / `# BIOMECH-CLAIM` directives:
  - `identity: <LHS> == <RHS>` (Algebraic simplification via SymPy CAS).
  - `constraint: <expr>` (Satisfiability / non-contradiction via Z3 SMT solver).
  - `numeric: <expr> samples=x:...` (Numerical point sampling via NumPy).
- **Human Attestation CLI Workflow (`mvpc attest`):** Interactive subcommand to rehydrate machine witnesses, attach human review signatures/notes, and cryptographically seal updated witness hash chains.
- **Pedagogical Remediation Dictionary (`mvpc.explanations`):** Built-in "Why this failed & How to fix it" guidance for every error code, embedded into terminal and markdown reports.
- **Enhanced Governance CLI Flags:** Added `--ai-prompt-file`, `--ai-model`, `--require-ai-provenance`, and `--require-human` flags to `mvpc audit`.
- **Zero-Dep Timezone-Aware Datetimes:** Completely migrated internal timestamps to standard `datetime.now(timezone.utc)`.

---

## [7.0.0] - 2026-08-12

### Initial Sovereign Release of MVPC-X

#### Features
- **Core Primitives:** Introduced atomic `Claim`, `Evidence`, `Verification`, `Provenance`, and `Witness` data structures.
- **Trust & Attestation Model:** Evaluates claims into `VERIFIED`, `CONDITIONAL`, `REJECTED`, and `UNVERIFIED` states proportional to verified mechanical checks.
- **Policy Engine:** Supports `PERMISSIVE`, `DEFAULT`, and `STRICT` policy levels with customizable axiom allowlists and pattern blocking.
- **Multi-Backend Engine:** Lean 4, Coq, Python static/dynamic, and Generic cryptographic file hasher.
- **Cryptographic Witness Chains:** Generates self-verifying SHA-256 witness records.
- **CLI Interface:** Provides `mvpc audit`, `mvpc witness verify`, directory scanning, and JSON export.
