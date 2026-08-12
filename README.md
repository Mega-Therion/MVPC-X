# MVPC-X

<div align="center">

**Sovereign Claim-Verification Infrastructure & Reproducible Epistemic Engine**

[![CI](https://github.com/Mega-Therion/MVPC-X/actions/workflows/ci.yml/badge.svg)](https://github.com/Mega-Therion/MVPC-X/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Formal Verification](https://img.shields.io/badge/formal_verification-Lean4%20%7C%20Coq%20%7C%20Python-orange.svg)](#backends)
[![Zero Centralized Trust](https://img.shields.io/badge/trust_model-Sovereign%20%26%20Cryptographic-green.svg)](#the-sovereign-covenant)

> *"AI proposes. Machines verify. Humans audit. Evidence persists."*

</div>

---

## Table of Contents

- [The Epistemic Problem](#the-epistemic-problem)
- [What is MVPC-X?](#what-is-mvpc-x)
- [Why It Matters](#why-it-matters)
- [Why Free & Open Source is Non-Negotiable](#why-free--open-source-is-non-negotiable)
- [The Sovereign Covenant](#the-sovereign-covenant)
- [Core Primitives](#core-primitives)
- [Trust & Attestation Model](#trust--attestation-model)
- [Architecture & Verification Backends](#architecture--verification-backends)
- [Quickstart & Installation](#quickstart--installation)
- [CLI Reference](#cli-reference)
- [Witness Hash Chains & Verification](#witness-hash-chains--verification)
- [Contributing & Community Roadmap](#contributing--community-roadmap)
- [License](#license)

---

## The Epistemic Problem

Modern technology is facing a quiet but catastrophic epistemic failure. 

In research papers, software engineering, AI safety, and mathematical physics, the dominant mechanism for establishing truth has devolved into a fragile loop:
```text
Someone / AI asserts X  ──►  X sounds plausible  ──►  Fits existing assumptions  ──►  X is accepted as truth
```

When Large Language Models generate millions of lines of synthetic code and synthetic scientific manuscripts every hour, **plausibility is no longer a proxy for truth**. Hallucinations masquerade as theorems. Unchecked `sorry` tactics slip into formal proofs. Security vulnerabilities hide behind confident prose.

MVPC-X exists to enforce a fundamentally different equation:

$$\mathbf{Knowledge} = \mathbf{Claim} + \mathbf{Evidence} + \mathbf{Verification} + \mathbf{Provenance} + \mathbf{Reproducibility} + \mathbf{Explicit\ Uncertainty}$$

**Assertion is not knowledge. Absence of detected error is not proof of correctness.**

---

## What is MVPC-X?

**MVPC-X** (Minimum Viable Proof of Concept - Extended) is a sovereign, machine-verifiable claim audit system. 

Rather than treating source files or AI outputs as monoliths, MVPC-X treats the **`Claim`** as the atomic unit of truth. It decouples the *generation* of ideas (which AI does brilliantly) from the *verification* of truth (which formal proof engines and execution environments do deterministically), binding them together in cryptographically auditable **Witness chains**.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        AI / Human Artifact                             │
│                  (Lean 4, Coq, Python, Manifest)                       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          MVPC-X Router                                 │
│        (Provenance Extraction • Static Analysis • AST Audit)           │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
       ┌────────────────────────┐      ┌─────────────────────────┐
       │   Native Verifiers     │      │   Static Policy Engine  │
       │ (Lean 4, Coqc, etc.)   │      │ (Axiom audit, safety)   │
       └────────────┬───────────┘      └────────────┬────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Cryptographic Witness Generator                    │
│             (SHA-256 Hash Chain • Explicit Coverage Bounds)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                           Audited Claim                                │
│       [VERIFIED | CONDITIONAL | REJECTED | UNVERIFIED]                 │
│         (Proportional to what was actually checked by machine)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Why It Matters

1. **Never Manufacture Certainty:** If a theorem has not been compiled with a native proof assistant, MVPC-X refuses to declare it `VERIFIED`. It yields `CONDITIONAL` with explicit coverage limits.
2. **Deterministic Adversarial Audits:** Smuggled axioms (e.g., `axiom shortcut : False`), `sorry` escape hatches, `admit` stubs, unsafe system calls, and undeclared axioms are trapped and flagged immediately.
3. **Decoupled Verification:** You do not trust the entity asserting a claim. You trust the cryptographic witness stating *what environment, what toolchain, what hashes, and what axioms* were executed.
4. **Machine-Checked Epistemic Hygiene:** From AI research to aerospace codebases, every pipeline can enforce strict mathematical boundaries before deployment.

---

## Why Free & Open Source is Non-Negotiable

Truth cannot be a proprietary black box. 

If verification infrastructure is locked inside a closed commercial vendor:
- Verification becomes an act of deference to centralized authorities ("Trust us, our closed algorithm checked it").
- Independent reproducibility is destroyed.
- Biases, backdoors, or loosened check-standards cannot be audited by the scientific community.

**MVPC-X is 100% Free and Open Source under the MIT License because:**
- **Sovereign Verification:** Anyone in the world—from an independent researcher on an air-gapped machine to a university lab—must be able to independently audit claims without asking for permission or paying API gatekeepers.
- **Collective Epistemic Defense:** The software, mathematics, and AI communities need a shared, peer-reviewed standard for evidence chains.
- **Extensible Verification Ecosystem:** The open source community can add backends for Isabelle/HOL, Agda, Z3/SMT, TLA+, Rust Miri, and domain-specific physics kernels.

---

## The Sovereign Covenant

Every component of MVPC-X adheres to the **Five Inviolable Principles**:

1. **MVP-C must never manufacture certainty.**
2. **Absence of detected problems is not evidence of truth.**
3. **Every assurance claim must be strictly proportional to the verification actually performed.**
4. **Humans provide meaning. Machines provide mechanical assurance.**
5. **Neither is allowed to silently substitute for the other.**

---

## Core Primitives

MVPC-X organizes knowledge into five fundamental primitives:

| Primitive | Definition | Role in MVPC-X |
|:---|:---|:---|
| **Claim** | The fundamental object under evaluation. | Has an ID (`C-YYYY-XXXXXX`), formal statement, scope, assumptions, and attestation state. |
| **Evidence** | Deterministic artifacts generated during verification. | Type (`FORMAL_PROOF`, `COMPUTATION`, `STATIC_ANALYSIS`), SHA-256 hash, and timestamps. |
| **Verification** | The independent mechanism that evaluated the claim. | Native Lean compiler, Coq typechecker, Python AST auditor, or sandbox runner. |
| **Provenance** | The lineage and origin of the artifact. | Source type (`HUMAN`, `AI`, `MACHINE`, `LITERATURE`), AI model details, and prompt hashes. |
| **Witness** | The self-verifying cryptographic record of an audit. | Contains environment info, checks performed, checks unavailable, findings, and a root SHA-256 signature. |

---

## Trust & Attestation Model

Claims are evaluated against customizable **Policy Levels**:

```text
┌──────────────┐     Policy: PERMISSIVE ──► Static clean is sufficient ────► VERIFIED
│ Static AST   │
│ & Axiom Pass │     Policy: DEFAULT    ──► Native check present? ──Yes──► VERIFIED
└──────┬───────┘                                                   └──No──► CONDITIONAL
       │
       └───────────► Policy: STRICT     ──► Native check present? ──Yes──► VERIFIED
                                                                   └──No──► REJECTED
```

### Attestation States

- **`VERIFIED`**: Full mechanical verification occurred. All static rules passed, and the native proof engine/test suite compiled successfully without unapproved axioms or stubs.
- **`CONDITIONAL`**: Static analysis passed, but native verification toolchains were not present on the host (e.g. `lean` not installed). Explicitly notes what trust boundary remains unverified.
- **`REJECTED`**: A violation occurred (e.g., `sorry`, `admit`, unsafe shell execution, compilation error, or smuggled axioms under strict policy).
- **`UNVERIFIED`**: Generic or unsupported artifact without sufficient mechanical proof.

---

## Architecture & Verification Backends

MVPC-X includes a modular backend registry:

- **Lean 4 Backend (`mvpc.backends.lean`)**:
  - *Static:* Traps `sorry`, `admit`, `native_decide`, and unapproved `axiom` declarations.
  - *Native:* Invokes `lean` / `lake` compiler to guarantee proof closure.
- **Coq Backend (`mvpc.backends.coq`)**:
  - *Static:* Detects `Admitted`, unproven goals, and raw axioms.
  - *Native:* Executes `coqc` proof verification.
- **Python Backend (`mvpc.backends.python`)**:
  - *Static AST:* Traps unsafe execution vectors (`exec`, `eval`, `os.system`, shell injection).
  - *Native:* Executes sandboxed assertions and unit suites.
- **Generic Backend (`mvpc.backends.generic`)**:
  - Cryptographically hashes any arbitrary artifact, producing immutable evidence without pretending to understand its internal semantics.

---

## Quickstart & Installation

### Requirements
- Python 3.10+
- Optional: `lean` (Lean 4) or `coqc` (Coq) for native theorem proving.

### Installation

```bash
# Clone the repository
git clone https://github.com/Mega-Therion/MVPC-X.git
cd MVPC-X

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with development/test tooling
pip install -e ".[test]"
```

### Run Test Suite
```bash
pytest
```
*All 34 native & static tests execute in milliseconds using zero external dependencies.*

---

## CLI Reference

### 1. Audit a Single File
```bash
mvpc audit path/to/theorem.lean
```

Output:
```text
Claim ID: C-2026-B39580
Statement: Artifact clean.lean satisfies policy level DEFAULT
State: VERIFIED

Coverage:
  Checks Performed: Static Analysis, Native Verification

Note: This specific set of checks passed. The artifact is proportional to the verification actually performed.
```

### 2. Audit with Strict Policy
Enforce that native verification MUST succeed and no axioms are permitted:
```bash
mvpc audit path/to/theorem.lean --policy strict
```

### 3. Generate Machine-Readable JSON Witness
```bash
mvpc audit tests/fixtures/sorry.lean --json
```

### 4. Verify a Witness Hash Integrity
```bash
mvpc witness verify witness.json
```

---

## Witness Hash Chains & Verification

Every audit produces a deterministic SHA-256 hash calculated across all constituent fields:
- Artifact SHA-256 hash
- Environment metadata (OS, Python version, architecture)
- Policy configuration applied
- Checks performed vs. checks unavailable
- Findings & evidence items

If even a single byte of an audited proof, finding, or environment flag is altered, `verify_witness_hash()` detects the tampering immediately.

---

## Contributing & Community Roadmap

We warmly welcome contributions from mathematicians, software engineers, security researchers, and formal methods practitioners.

### Immediate Community Goals (v7.1 - v8.0)
- [ ] **New Backends:**
  - Isabelle/HOL (`.thy`)
  - Agda (`.agda`)
  - Z3 / SMT-LIB2 (`.smt2`)
  - Rust Formal Verification (Creusot / Kani / Miri)
  - TLA+ Specification Checker
- [ ] **Distributed Witness Registry:** Decentralized, content-addressable storage (IPFS/Git-notes) for published witnesses.
- [ ] **AI Model Guardrails:** Direct plug-in middleware for LLM inference engines (automatically piping LLM code/proof outputs through MVPC-X before returning responses).
- [ ] **GitHub Action:** Ready-to-use PR audit bot for open-source repositories.

See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

## License

MVPC-X is open-source software licensed under the [MIT License](LICENSE).

---

<div align="center">
Built with mathematical rigor by the Sovereign Physics Lab & the Global Open Source Community.
</div>
