# Security & Threat Model

## Threat Model & Design Principles

MVPC-X is designed to operate under adversarial conditions where source code, proofs, or claims may attempt to fool the verification pipeline into false attestation.

### 1. Attack Vectors & Mitigations

#### A. Proof Smuggling (Axiom Spoofing)
- **Threat:** Proof files may define circular axioms (e.g. `axiom shortcut : False`) to trivially prove false propositions.
- **Mitigation:** The Lean and Coq backends inspect the AST for undeclared or unapproved `axiom` / `Axiom` statements. Under `STRICT` policy, unapproved axioms cause immediate rejection.

#### B. Proof Stubbing (`sorry` / `admit`)
- **Threat:** Automated provers or LLMs often leave `sorry` or `admit` stubs when unable to close proof goals.
- **Mitigation:** Static pattern matching and AST scanning flag all incomplete tactics as `VIOLATION` severity findings.

#### C. Arbitrary Code Execution via Python / Dynamic Scripts
- **Threat:** Verification scripts could contain malicious payloads (`exec()`, `eval()`, `os.system()`, subprocess escape).
- **Mitigation:** The Python backend conducts static AST scanning before executing any file. Unsafe calls are trapped and flagged as violations.

#### D. Witness Tampering
- **Threat:** A malicious actor modifies a witness report to claim a rejected file was verified.
- **Mitigation:** Every witness has a root SHA-256 hash computed over its canonicalized fields and artifact hashes. Calling `mvpc witness verify <witness.json>` independently re-hashes the artifact and witness fields to detect modification.

---

## Reporting Vulnerabilities

If you discover a security issue or bypass in any static analyzer or backend, please report it via GitHub Security Advisories on this repository or contact the maintainers at `viewsbyryan@gmail.com`.
