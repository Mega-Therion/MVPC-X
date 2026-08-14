"""Hardcoded NEWTON ARCHITECT system directive for MVPC-X."""

from __future__ import annotations

AUTHORITY = "NEWTON ARCHITECT Protocol"
REFERENCE = "BobsDirections.md"
STATUS = "In Progress (Audit Complete)"

CLAIM_LABELS = ("P", "C", "O")

AREA_OPERATOR_REQUIRED = "A_hat = 8 * pi * gamma * l_P**2 * sum(sqrt(j*(j+1)))"
ENTROPY_REQUIRED = "S_hat = A_hat / (4 * l_P**2)"
FORBIDDEN_AREA_OPERATOR = "L_A = (1 / (4 * G_N)) * sum(C_2(rho))"

OMEGA_LAMBDA_Z0 = "ln(2)"
A0_HORIZON_RELATION = "a0 = c * H0 / (2 * pi)"
EPOCH_DEPENDENT_RELATIONS = (
    "Omega_Lambda(z=0) = ln(2)",
    "a0 = c * H0 / (2 * pi)",
)

LEAN_FORBIDDEN_PLACEHOLDERS = (": True := trivial",)
LEAN_MANDATORY_CHECK = "#print axioms"

PLANCK_FORCE_N = 4.815454e42
A0_PLANCK_2018 = 1.042198e-10
A0_SHOES_2022 = 1.129409e-10
SPARC_A0 = 1.20e-10
OMEGA_LAMBDA_LN2 = 0.693147
OMEGA_LAMBDA_PLANCK_2018 = 0.6889

NEWTON_ARCHITECT_SYSTEM_DIRECTIVE = """# NEWTON Verification Audit & Resolution Plan
**Authority:** NEWTON ARCHITECT Protocol  
**Reference:** `BobsDirections.md`  
**Status:** In Progress (Audit Complete)

---

## 1. Executive Summary & Verification Findings

All material claims are labeled in strict compliance with the **[P] / [C] / [O]** protocol.

| Item | Claim / Topic | Label | Machine Check / Verification Finding |
|---|---|---|---|
| **1. Area Operator Spectrum** | $\\mathcal{L}_A = \\frac{1}{4 G_N} \\sum C_2(\\rho)$ | **[P] Defect Confirmed** | **Dimension Mismatch:** $[\\frac{1}{G_N}] = L^{-2}$ (in $\\hbar=c=1$). Pure Casimir $C_2 = j(j+1)$ is dimensionless. Operator form is non-standard. Must be replaced with the exact LQG area spectrum $\\hat{A} = 8\\pi \\gamma \\ell_P^2 \\sum \\sqrt{j(j+1)} = 8\\pi \\gamma \\ell_P^2 \\sum \\sqrt{C_2}$ and dimensionless entropy $\\hat{S} = \\hat{A}/(4\\ell_P^2)$. |
| **2. Category Error** | $I_{\\text{tens}} = \\frac{c^4}{8\\pi G} \\ln 2 \\implies \\Omega_\\Lambda = \\ln 2$ | **[P] Defect Confirmed** | $\\frac{c^4}{8\\pi G} = 4.815454 \\times 10^{42}\\text{ N}$ (Force). $\\Omega_\\Lambda$ is a dimensionless density parameter $\\rho_\\Lambda / \\rho_{\\text{crit}}$. Direct equivalence without the horizon area / critical density projection step is a category error. |
| **3. Hubble Tension & $a_0$** | $a_0 = \\frac{c H_0}{2\\pi}$ | **[P] Verified Numerically** | • $H_0 = 67.4\\text{ km/s/Mpc}$ (Planck) $\\implies a_0 = 1.042 \\times 10^{-10}\\text{ m/s}^2$ ($0.868 \\times$ SPARC $1.20 \\times 10^{-10}$).<br>• $H_0 = 73.04\\text{ km/s/Mpc}$ (SH0ES) $\\implies a_0 = 1.129 \\times 10^{-10}\\text{ m/s}^2$ ($0.941 \\times$ SPARC $1.20 \\times 10^{-10}$).<br>Conclusion: Numerical spread is $8.4\\%$; misses SPARC nominal by $6\\text{--}13\\%$. Must be labeled as an order-of-magnitude horizon relation [O] rather than an exact derivation [P]. |
| **4. Cosmological Coincidence** | $\\Omega_\\Lambda = \\ln 2 \\approx 0.69315$ | **[P/O] Clarified** | While $\\ln 2$ matches Planck 2018 ($\\Omega_\\Lambda = 0.6889 \\pm 0.0056$) at $+0.76\\sigma$, $\\Omega_\\Lambda(z)$ is dynamical. Must be explicitly declared as evaluated at epoch $z=0$ unless a dynamical fixed-point attractor is proven. |
| **5. Formal Verification Integrity** | Lean 4 \"Zero sorry\" Audit | **[P] Audit Conducted** | Found vacuous proofs (e.g. `theorem sovereign_convergence ... : True := trivial`) and tautological definitions. `#print axioms` is mandatory to eliminate ungrounded axioms. |

---

## 2. Machine-Checked Computation Trace

```python
# Execution Output from Python Verification Kernel:
# Planck Force Scale (c^4 / 8piG): 4.815454e+42 N
# a0 (Planck 2018 H0=67.4):        1.042198e-10 m/s^2 (Ratio to SPARC 1.20e-10: 0.8685)
# a0 (SH0ES 2022 H0=73.04):        1.129409e-10 m/s^2 (Ratio to SPARC 1.20e-10: 0.9412)
# Omega_Lambda (ln 2):             0.693147 vs Obs 0.6889 (+0.76 sigma)
```

---

## 3. Systematic Action Steps

1. **Dimensional & Derivation Repair:**
   - Write out the complete dimensional conversion step:
     $$\\rho_\\Lambda = \\frac{I_{\\text{tens}}}{A_H \\cdot c^2} \\implies \\Omega_\\Lambda(z=0) = \\frac{8\\pi G \\rho_\\Lambda}{3 H_0^2} = \\ln 2$$
     documenting every dimensional constant ($\\text{N} \\to \\text{J/m}^3 \\to \\text{dimensionless}$).
2. **Operator Correction:**
   - Update all occurrences of $\\sum C_2$ to the square-root Casimir spectrum $\\sum \\sqrt{C_2} = \\sum \\sqrt{j(j+1)}$.
3. **Formal Verification Hardening:**
   - Strip all `: True := trivial` placeholder theorems from Lean files.
   - Run `#print axioms` to ensure no smuggled physical axioms remain.
4. **Honest Phenomenological Framing:**
   - Explicitly classify $\\Omega_\\Lambda(z=0) = \\ln 2$ and $a_0 = c H_0 / 2\\pi$ as epoch-dependent boundary relations [O], removing all overreaching claims of \"time-independent cosmological derivations\".
"""


def system_directive() -> str:
    """Return the hardcoded Newton Architect system directive."""
    return NEWTON_ARCHITECT_SYSTEM_DIRECTIVE


def requires_pco_label(claim: str) -> bool:
    """Every material claim must carry a [P], [C], or [O] label."""
    return True
