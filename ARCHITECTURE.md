# MVPC-X Architecture Specification

## Overview

MVPC-X is architected around a fundamental principle: **The Claim is the atomic unit of truth, not the source file.**

```text
┌─────────────────────────────────────────────────────────────┐
│                          CLAIM                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ID: C-2026-XXXXXX                                       │ │
│ │ Statement: "..."                                        │ │
│ │ Provenance: SourceType + AI Lineage + Origin Hash       │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Evidence: [Formal Proof, Static AST, Sandbox Execution] │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Findings: [Violations, Warnings, Info]                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Coverage: [Checks Performed, Checks Unavailable]        │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Attestation: VERIFIED | CONDITIONAL | REJECTED          │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Witness: Root SHA-256 Signature of the Entire State     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. The Five Primitives

### 1.1 Claim (`mvpc.claim`)
Represents an assertion undergoing evaluation.
- `id`: Auto-generated unique identifier in `C-YYYY-NNNNNN` format.
- `statement`: Textual or mathematical proposition.
- `origin`: `SourceType` (HUMAN, AI, MACHINE, MEASUREMENT, DATABASE, LITERATURE, MIXED, UNKNOWN).
- `provenance`: Detailed ancestry, including AI model parameters, prompt hashes, and revision chain.
- `evidence`: List of deterministic evidentiary items.
- `findings`: List of static or dynamic analysis findings.
- `coverage`: Explicit report of executed vs. skipped verifications.
- `attestation_state`: Final evaluated state.

### 1.2 Evidence (`mvpc.evidence`)
Deterministic verification artifacts:
- `evidence_type`: `FORMAL_PROOF`, `COMPUTATION`, `STATIC_ANALYSIS`, `NATIVE_VERIFICATION`, `STATISTICAL_TEST`, `DATA_INTEGRITY`, `REPRODUCTION`, `SOURCE_DOCUMENT`, `EXPERT_REVIEW`.
- `artifact_path` & `artifact_hash`: SHA-256 of the source file.
- `timestamp`: ISO-8601 UTC timestamp.

### 1.3 Verification Backends (`mvpc.backends.base`)
The abstract contract `VerificationBackend` defines:
```python
class VerificationBackend(ABC):
    def name(self) -> str: ...
    def supported_extensions(self) -> List[str]: ...
    def supports(self, path: str) -> bool: ...
    def check_native_available(self) -> bool: ...
    def run_static_analysis(self, path: str) -> Tuple[List[Finding], List[Evidence]]: ...
    def run_native_verification(self, path: str) -> Tuple[List[Finding], List[Evidence]]: ...
    def audit(self, path: str) -> Tuple[List[Finding], List[Evidence], CoverageReport]: ...
```

### 1.4 Policy Engine (`mvpc.policy`)
Evaluates Findings + Coverage against defined rules:
- **`PERMISSIVE`**: Static analysis pass is sufficient for `VERIFIED`.
- **`DEFAULT`**: Requires native compilation for `VERIFIED`. Falls back to `CONDITIONAL` if host lacks toolchains.
- **`STRICT`**: Requires native compilation and forbids axioms/stubs. Absence of native compiler yields `REJECTED`.

### 1.5 Witness Engine (`mvpc.witness`)
Produces a cryptographically signed receipt of verification:
- `witness_id`: Unique receipt ID `W-XXXXXX`.
- `witness_hash`: Root SHA-256 computed across all normalized fields.
- `verify_integrity()`: Validates that the witness has not been modified after generation.

---

## 2. Directory Layout

```text
mvpc/
├── src/
│   └── mvpc/
│       ├── __init__.py          # Version & package exports
│       ├── claim.py             # Claim primitive & serialization
│       ├── evidence.py          # Evidence primitive & enums
│       ├── trust.py             # AttestationState, Finding, Coverage
│       ├── provenance.py        # Lineage & AI source metadata
│       ├── policy.py            # Policy evaluation & rules
│       ├── hashing.py           # SHA-256 cryptographic hashing
│       ├── witness.py           # Witness receipt generation & verification
│       ├── engine.py            # Verification orchestrator
│       ├── auditor.py           # Directory & repo batch scanner
│       ├── report.py            # Markdown, JSON, and Terminal formatters
│       ├── cli.py               # Command line interface
│       └── backends/
│           ├── __init__.py
│           ├── base.py          # Abstract base backend
│           ├── lean.py          # Lean 4 theorem proving backend
│           ├── coq.py           # Coq proof assistant backend
│           ├── python.py        # Python static & sandboxed execution
│           ├── generic.py       # General file hasher fallback
│           └── registry.py      # Backend discovery & dispatch
├── tests/
│   ├── conftest.py              # Test fixtures & paths
│   ├── fixtures/                # Clean & adversarial test files
│   ├── test_claim.py
│   ├── test_evidence.py
│   ├── test_trust.py
│   ├── test_policy.py
│   ├── test_hashing.py
│   ├── test_witness.py
│   ├── test_backends.py
│   ├── test_engine.py
│   └── test_cli.py
├── ARCHITECTURE.md
├── COVENANT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── ROADMAP.md
├── CHANGELOG.md
├── LICENSE
└── pyproject.toml
```
