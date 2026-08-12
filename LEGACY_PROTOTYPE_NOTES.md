# Lineage & Legacy Prototype Notes

## Evolution from Prototype to MVPC-X Sovereign Architecture

### 1. The Early Prototypes (v1 - v6)
Early iterations of verification experiments (including `lean-sentinel` and early prototype scripts) suffered from several systemic limitations common across first-generation AI-eval tooling:

1. **File-Centricity:** Systems evaluated whole repositories or whole files rather than treating the individual **`Claim`** as the atomic unit of truth.
2. **Binary Illusion of Truth:** Outputs often claimed "100% Verified" or "Mathematically Sound" based solely on static regex scans, even when native compilers (`lean`, `coqc`) were never executed.
3. **Environment Assumptions:** Hardcoded local path expectations and non-standard dependencies made independent verification fragile.
4. **Lack of Cryptographic Lineage:** There was no deterministic record of *what exact environment and toolchain* produced a verification verdict.

### 2. The v7.0.0 MVPC-X Breakthrough
MVPC-X was rebuilt from first principles to resolve these epistemic flaws:

- **Atomic Claims:** Claims are decoupled from file systems. A claim can cite multiple formal and computational evidence items.
- **Proportional Attestation:** `VERIFIED`, `CONDITIONAL`, `REJECTED`, and `UNVERIFIED` are mathematically bound to what was actually checked.
- **The Covenant:** Inviolable rules that forbid the software from ever manufacturing certainty.
- **Universal Witness Hash Chains:** Every audit produces a self-verifying SHA-256 witness that can be validated offline by third parties.
- **Pure Zero-Dependency Core:** Standard Python library foundation to ensure absolute longevity and sovereign execution.
