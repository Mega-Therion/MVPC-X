# MVPC-X Threat Model

## Scope

This document defines the threats MVPC-X is designed to mitigate and, critically, the threats it explicitly does **not** mitigate. Every witness bundle must carry a trusted-computing-base (TCB) declaration that makes these boundaries explicit.

## Trusted computing base

The following components must be trusted for an MVPC-X verdict to hold:

1. **MVPC-X release artifact** — the installed package and any verifier kernel, checked against a release manifest.
2. **Runtime and dependencies** — the interpreter, standard library, and resolved dependency graph.
3. **Formal prover binaries** — Lean, Coq, Isabelle, Z3, or another selected backend.
4. **Operating system and kernel** — process isolation, filesystem permissions, and memory protection.
5. **Claim formalization** — the mapping from a natural-language claim to its formal theorem.
6. **Signing keys** — keys used for policies, witnesses, and attestations.
7. **Policy bundle** — the declarative rules defining acceptance for the audit.

## Threats mitigated

| Threat | Required mitigation |
|---|---|
| Accidental artifact tampering | Canonical SHA-256 hashes over all bundle components |
| Dependency drift | Hash-locked dependencies and recorded SBOM |
| Backend substitution | Backend binary hash checked against policy |
| Post-signing witness forgery | Ed25519 signatures over canonical records |
| Ledger alteration | Linked witness hashes, signatures, and fork detection |
| AI proposal treated as authority | Explicit AI provenance plus human semantic sign-off |
| Verdict overstatement | Distinct trust-result taxonomy |
| Untrusted input paths | Size, path, and symlink intake guards |

## Threats outside scope

| Threat | Boundary |
|---|---|
| Kernel or firmware compromise | Below MVPC-X user-space trust boundary |
| Privileged runtime memory modification | A sufficiently privileged actor can alter a process |
| Compromised signing key | Requires key revocation and operator response |
| Social engineering of an attestor | Human judgment is not machine-verifiable |
| Undetected semantic mismatch | A proof of the wrong formalization remains possible |
| Side-channel attacks | Not addressed by the current architecture |

## Assumptions

1. The release artifact was acquired from a trusted source and verified.
2. The OS enforces process isolation and filesystem permissions.
3. Backend binaries came from approved sources and match the recorded hashes.
4. Signing keys are securely controlled and have not been compromised.
5. The human attestor is appropriately authorized for the scope they sign.

If an assumption fails, hashes and signatures alone do not make the resulting witness trustworthy.

## Required disclosure

Every published witness must state the TCB, assumptions, checked artifacts, unverified boundaries, policy hash, backend versions, and applicable limitations. MVPC-X reports reproducible, policy-bound verification evidence; it does not certify truth in the abstract.
