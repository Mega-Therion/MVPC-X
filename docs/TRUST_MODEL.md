# MVPC-X Trust Model

## Core principle

> MVPC-X does not certify truth in the abstract. It produces a reproducible, policy-bound record of exactly what claim was checked, against what evidence, by which verifier versions, under which assumptions, and with what limitations.

## Verdict hierarchy

| Verdict | Implies truth? | Notes |
|---|---|---|
| FORMALLY_CHECKED | Within formal system | Named checker accepted a theorem |
| COMPUTATION_VERIFIED | Within computation model | Deterministic computation/identity |
| EXECUTION_OBSERVED | No | Controlled execution output only |
| EVIDENCE_SUPPORTED | No | Policy evidence threshold met |
| HUMAN_ATTESTED | No | Scoped human/system attestation |
| INCONCLUSIVE | No | Insufficient evidence or resources |
| REJECTED | No (negative) | Policy/backend rejected |
| UNSAFE_TO_VERIFY | No | Intake/sandbox/integrity blocked |
| CONFLICTING_VERDICTS | No | Independent results disagree |

Truth-implying labels may only be rendered for FORMALLY_CHECKED or COMPUTATION_VERIFIED when TCB, assumptions, traceability sign-off, policy hash, and signature requirements are met. Never collapse other verdicts to a generic "verified" badge.

## Bio-mechanical bridge

- **Machine guard:** syntax, formal consequence, integrity, policy, hashes, signatures, reproducibility.
- **Human guard:** meaning, scope, formalization fidelity, applicability of assumptions.
- Neither silently replaces the other. AI proposals are metadata labeled AI_PROPOSED until human-approved.

## Required limitations disclosure

Every witness must disclose what was checked, what was not, assumptions, admitted lemmas, TCB limits, reproduction steps, and attestation scopes.
