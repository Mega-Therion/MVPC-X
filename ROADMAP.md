# MVPC-X Development Roadmap

## Phase 1: Core Foundation (v7.0.0) — *Complete*
- [x] Epistemic Primitives (Claim, Evidence, Verification, Provenance, Witness).
- [x] Trust Model & Multi-tier Policy Engine (Permissive, Default, Strict).
- [x] Multi-Backend Architecture (Lean 4, Coq, Python, Generic).
- [x] Cryptographic Witness Generation & Verification.
- [x] Full CLI Interface (`mvpc audit`, `mvpc witness verify`, JSON output).
- [x] Zero-dependency core Python package.
- [x] Full unit test suite.

---

## Phase 2: Community Backends & Mathematical Engines (v7.1.0) — *Complete*
- [x] **Isabelle/HOL Backend:** Integration with `isabelle build -D` and `.thy` theory / `ROOT` session parsing.
- [x] **Inline Mathematical Claims Engine:** Embedded `# MVPC-CLAIM` support for SymPy CAS identities, Z3 constraint satisfiability, and NumPy point sampling.
- [x] **Human Attestation Subcommand:** `mvpc attest` interactive workflow for human review signoffs.
- [x] **Pedagogical Remediation Dictionary:** Built-in guidance for fixing detected violations.
- [ ] **Agda Backend:** Verification for dependent type proofs (`.agda`).
- [ ] **Rust Formal Verification:** Integration with Creusot, Kani, and Miri.
- [ ] **TLA+ / PlusCal:** Model checking verification for distributed systems.

---

## Phase 3: AI Inference & Pipeline Guardrails (v7.5.0)
- [ ] **Streaming AI Middleware:** Interceptor for LLM code generation APIs that audits generated proofs before presenting to users.
- [ ] **Automated Remediation Hints:** AI-assisted repair suggestions for detected `sorry` / syntax issues without bypassing verification.
- [ ] **Provenance Verifier:** Cryptographic signature check for AI model weights and prompt records.

---

## Phase 4: Decentralized Witness Ledger (v8.0.0)
- [ ] **Content-Addressable Witness Storage:** Git-notes and IPFS witness publishing.
- [ ] **Peer-to-Peer Attestation Federation:** Distributed reproducibility checks where multiple independent machines verify and co-sign witnesses.
