# MVPC-X Development Roadmap

## Phase 1: Core Foundation (v7.0.0) — *Current*
- [x] Epistemic Primitives (Claim, Evidence, Verification, Provenance, Witness).
- [x] Trust Model & Multi-tier Policy Engine (Permissive, Default, Strict).
- [x] Multi-Backend Architecture (Lean 4, Coq, Python, Generic).
- [x] Cryptographic Witness Generation & Verification.
- [x] Full CLI Interface (`mvpc audit`, `mvpc witness verify`, JSON output).
- [x] Zero-dependency core Python package.
- [x] Full unit test suite (34 passing tests).

---

## Phase 2: Community Backends (v7.1.0)
- [ ] **Isabelle/HOL Backend:** Integration with `isabelle build` and `.thy` theory parsing.
- [ ] **Agda Backend:** Verification for dependent type proofs (`.agda`).
- [ ] **Z3 / SMT-LIB2 Backend:** Automated SMT solver evidence validation.
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
