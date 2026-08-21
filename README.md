<div align="center">

# 🛡️ MVPC-X
### Multi-Variant Proof-Chain & Sovereign Claim-Verification Infrastructure
**Deterministic Multi-Prover Auditing, Cryptographic Witness Seals & Kernel Assurance**

---

[![CI](https://img.shields.io/badge/CI-Passing_(117_Tests)-00C781.svg?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/Mega-Therion/MVPC-X/actions)
[![Version](https://img.shields.io/badge/Version-v1.0.0-0052FF.svg?style=for-the-badge&logo=pypi&logoColor=white)](https://github.com/Mega-Therion/MVPC-X/releases/tag/v1.0.0)
[![Epistemic Covenant](https://img.shields.io/badge/Epistemic_Covenant-Enforced-D4AF37.svg?style=for-the-badge)](COVENANT.md)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](pyproject.toml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge)](LICENSE)

<br/>

> *“AI proposes. Machines verify. Humans audit. Evidence persists.”*

[**Architecture 🏛️**](ARCHITECTURE.md) &nbsp;•&nbsp; [**The Epistemic Covenant 📜**](COVENANT.md) &nbsp;•&nbsp; [**Security Policy 🔒**](SECURITY.md) &nbsp;•&nbsp; [**Contributing 🤝**](CONTRIBUTING.md)

</div>

---

## ⚡ Overview

**MVPC-X** is an open-source, high-assurance mechanical claim-verification framework. It bridges theoretical propositions, formal interactive theorem provers (Lean 4, Coq, Isabelle/HOL), symbolic CAS engines (SymPy/Z3), and empirical datasets into tamper-evident, cryptographically signed **Proof-Witness Chains**.

```
              ┌─────────────────────────────────────────────────────────┐
              │           Unverified Claim / Theorem / Script           │
              └────────────────────────────┬────────────────────────────┘
                                           │
                                           ▼
              ┌─────────────────────────────────────────────────────────┐
              │           MVPC-X Multi-Prover Intake Guard              │
              │     Policy Engine • Sandbox Guard • TCB Isolator        │
              └──────┬─────────────────────┬─────────────────────┬──────┘
                     │                     │                     │
      Lean 4 Kernel  ▼        SymPy / CAS  ▼      Empirical Hash ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ Lean 4 / Mathlib │  │ Symbolic Calculus│  │ SHA-256 Dataset  │
    │  #print axioms   │  │  Z3 SMT Solver   │  │ Residual Audits  │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   │
                                   ▼
              ┌─────────────────────────────────────────────────────────┐
              │          Cryptographic Witness Bundle (.json)           │
              │  SHA-256 State Fingerprint • Merkle Proof • Epistemic Seal│
              └─────────────────────────────────────────────────────────┘
```

---

## 🏛️ Verification Architecture

### Multi-Prover Backends
* **Formal Proof Kernels:** Native validation in Lean 4 (`lake env lean`), Coq (`coqc`), and Isabelle/HOL. Checks for missing proofs, `sorry` placeholders, and axiom leakage.
* **Symbolic CAS Verification:** Python / SymPy / Z3 symbolic equivalence proofs, tensor contraction verification, and dimensional consistency checks.
* **Empirical Data Audits:** Hashed dataset reproduction pipelines, bounding out-of-sample residuals, $\chi^2$ data-residual separations, and MAP regularization checks.

### Verifier Anti-Tampering & Self-Fingerprint
MVPC-X executes a three-phase system self-fingerprint (Before / Mid / After audit) to ensure zero host-state mutations, environment tampering, or cached-output substitution during verification runs.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Mega-Therion/MVPC-X.git
cd MVPC-X

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e ".[all]"
```

### 2. Verify Your First Formal Claim

```bash
# Verify system integrity & anti-tamper fingerprinting
mvpc integrity --verify-twice

# Preflight check a Lean 4 theorem file
mvpc preflight path/to/Theorem.lean

# Run a strict audit against the Sovereign Covenant policy
mvpc audit path/to/Theorem.lean --policy strict

# Generate a standalone witness bundle
mvpc witness export path/to/Theorem.lean --out witness.json
```

---

## Sovereign Nexus Control Plane

The **Sovereign Nexus** adds source-agnostic structural intake, PANI-neutral policy gates, local backend receipts, permanent linked manifests, and a Glass Box presentation contract. It is additive: existing `mvpc audit`, `mvpc preflight`, and `mvpc integrity` workflows remain unchanged.

```bash
# Create a workspace with human intent, formal source, CAS certificate, and linked ledger metadata
mvpc scaffold nexus ./nexus-workspace

# Non-executing preview: normalize source and render Glass Box data
mvpc nexus inspect ./nexus-workspace/formal/Basic.lean --plan "$(cat ./nexus-workspace/intent.md)"

# Local verification with pre/mid/post fingerprints and paired JSON/Markdown manifests
mvpc nexus verify ./nexus-workspace/formal/Basic.lean \
  --plan "$(cat ./nexus-workspace/intent.md)" \
  --ledger-dir ./nexus-workspace/ledger/manifests

# Exact polynomial-certificate check; this remains CAS evidence, not kernel proof
mvpc nexus cas-verify ./nexus-workspace/cas/certificate.json
```

The Nexus preserves the distinction between proposal and proof. Natural-language and LaTeX material are normalized as `UNTRANSLATED`; a Green Glass Box state requires a qualifying native local backend receipt. Detailed activation, integrity constraints, and verdict rules are in [`docs/SOVEREIGN_NEXUS.md`](docs/SOVEREIGN_NEXUS.md).

---

## 🔬 The Epistemic Taxonomy

All audited claims are tagged with their exact mechanical epistemic classification:

$$\begin{aligned}
\mathbf{[P]} & \quad \textbf{Proved / Kernel Verified:} \text{ Verified by a mechanical proof kernel (Lean 4, Coq) with audited axioms.} \\
\mathbf{[D]} & \quad \textbf{Direct Empirical / Computed:} \text{ Evaluated from raw, cryptographically hashed datasets via reproducible code.} \\
\mathbf{[C]} & \quad \textbf{Cited Literature:} \text{ Authentic peer-reviewed external baselines.} \\
\mathbf{[O]} & \quad \textbf{Open Problem / Conjectured Boundary:} \text{ Phenomenological bridge hypotheses quarantined from proof claims.}
\end{aligned}$$

---

## 📂 Repository Layout

```
MVPC-X/
├── src/mvpc/
│   ├── engine.py              # Core multi-prover orchestration engine
│   ├── policy.py              # Policy manifests (strict, default, permissive)
│   ├── witness.py             # Cryptographic witness generation & Merkle trees
│   ├── backends/              # Lean 4, Coq, Isabelle, SymPy, Python backends
│   ├── traceability.py        # Provenance, lineage tracking & git attribution
│   └── cli.py                 # Command-line interface
├── tests/                     # 117 unit and integration tests (100% pass rate)
├── docs/                      # Specification, guidelines, and formal policies
├── ARCHITECTURE.md            # In-depth technical architecture document
├── COVENANT.md                # Sovereign Epistemic Covenant definition
├── pyproject.toml             # Python build and package manifest
└── LICENSE                    # Apache-2.0 License
```

---

<div align="center">

**MVPC-X Verification Engine**  
*Turning theoretical claims into auditable cryptographic evidence.*

</div>
