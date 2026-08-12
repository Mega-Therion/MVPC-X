# The Biomechanical Covenant

**MVPC-X Sovereign Constitution**  
Version 7.2 · Human–AI Claim Verification Standard

> **AI proposes. Machines verify. Humans audit. Evidence persists.**  
> No silent handshake between human intuition and machine output counts as truth.

---

## 0. What “biomechanical” means here

**Bio** = human beings (judgment, meaning, responsibility).  
**Mechanical** = machines and formal tools (kernels, SMT, CAS, compilers, hash chains).

This is **not** wet-lab biology or industrial robotics. It is the standard for **human–AI collaboration** under adversarial conditions: LLMs can generate infinite plausible falsehoods; humans can rubber-stamp them; tools can be missing and still be advertised as “verified.”

MVPC-X exists so that **neither side substitutes for the other in silence.**

---

## 1. The five inviolable principles

1. **MVPC-X must never manufacture certainty.**  
   If a check did not run, the system must not imply that it did. `VERIFIED` is earned, never cosmetically painted.

2. **Absence of detected problems is not evidence of truth.**  
   A clean static scan is not a kernel proof. A missing toolchain is not a pass. Coverage gaps are first-class outputs.

3. **Every assurance claim must be strictly proportional to verification actually performed.**  
   Attestation states (`VERIFIED`, `CONDITIONAL`, `REJECTED`, `UNVERIFIED`) are bound to findings + coverage + policy—not vibes.

4. **Humans provide meaning. Machines provide mechanical assurance.**  
   Humans choose what is worth claiming, interpret context, and accept moral responsibility. Machines check structure, axioms, contradictions, identities, and hashes.

5. **Neither is allowed to silently substitute for the other.**  
   AI output is not self-certifying. Human confidence is not a kernel. Both leave a trail: provenance for AI, attestation for humans, witnesses for the whole chain.

---

## 2. The epistemic equation

$$\mathbf{Knowledge} = \mathbf{Claim} + \mathbf{Evidence} + \mathbf{Verification} + \mathbf{Provenance} + \mathbf{Reproducibility} + \mathbf{Explicit\ Uncertainty}$$

- **Claim** — the atomic unit of truth (not “the whole file,” not “the model said so”).
- **Evidence** — deterministic artifacts (hashes, kernel logs, CAS results, static findings).
- **Verification** — independent mechanisms (Lean/Coq/Isabelle kernels, Z3, SymPy, policy engine).
- **Provenance** — who/what produced the artifact (human, AI model, prompt hash, time).
- **Reproducibility** — another party can re-run the same gates on the same bytes.
- **Explicit uncertainty** — `checks_unavailable`, trust boundaries, degraded coverage.

**Assertion is not knowledge.**

---

## 3. Roles in the collaboration

| Role | May do | Must not do |
|------|--------|-------------|
| **AI** | Propose proofs, code, text, strategies | Self-certify; hide provenance; leave silent `sorry` |
| **Machine engines** | Reject, bound, hash, explain failures | Invent certainty when tools are missing |
| **Human** | Define claims, review witnesses, attest or reject | Rubber-stamp without reading coverage |
| **MVPC-X** | Orchestrate backends, enforce policy, seal witnesses | Lie about what ran |

---

## 4. Attestation states (mechanical meaning)

- **`VERIFIED`** — Required mechanical checks for the active policy completed without violations. Still not “absolute truth of the universe”—only proportional machine assurance.
- **`CONDITIONAL`** — Static (or partial) checks passed; native or required engines were unavailable. Trust boundary is explicit.
- **`REJECTED`** — Violation found (sorry, smuggled axiom, compile failure, unsat hyps, unsafe surface, policy breach).
- **`UNVERIFIED`** — Insufficient mechanical surface (e.g. generic hash-only artifact under demanding policy).

**Covenant-complete** (full human–AI seal) additionally requires:

1. Machine attestation under the chosen policy, and  
2. Human attestation (`mvpc attest`) when policy or flags require it, and  
3. AI provenance when the artifact is AI-touched and governance flags demand it.

---

## 5. Policy levels

| Level | Intent |
|-------|--------|
| **PERMISSIVE** | Static cleanliness may yield `VERIFIED`; useful for quick triage. |
| **DEFAULT** | Native verification preferred; static-only → `CONDITIONAL`. |
| **STRICT** | Native required; missing native → `REJECTED`; human signoff expected; axiom allowlist may be empty. |

Operators must not advertise PERMISSIVE results as STRICT science.

---

## 6. What backends owe the covenant

Every backend must:

1. Say **what it checked** (`checks_performed`).
2. Say **what it could not check** (`checks_unavailable`).
3. Emit **findings** with codes, severity, and remediation.
4. Attach **evidence** with artifact hashes and timestamps.
5. Prefer **native kernels** when present (Lean `#print axioms`, `coqc`, `isabelle build`, etc.).
6. Never upgrade missing tools into silent success.

Lean gold-standard obligations include: comment-aware scans, bare `axiom`/`unsafe`/`sorry`, tautology traps, kernel axiom allowlisting (`propext`, `Quot.sound`, `Classical.choice`), `sorryAx` / `Lean.ofReduceBool`, optional Z3 vacuity and SymPy identity layers.

---

## 7. Witness law

Every audit produces a **witness**: environment, policy, findings, evidence, coverage, attestation state, optional human seals, and a **root SHA-256** over the canonical payload.

- Altering any sealed field without recompute → integrity failure.
- Third parties should verify with `mvpc witness verify`.
- Witnesses are the public memory of the collaboration—not marketing PDFs.

---

## 8. Prohibited behaviors (reject PRs / releases that do these)

- Printing “100% verified” / “mathematically sound” when the kernel never ran.
- Hiding `checks_unavailable`.
- Treating AI prose as evidence.
- Allowlisting `False` or project-local cheat axioms without disclosure.
- Shipping stub tests that always `pass` to inflate counts.
- Silent `eval` of untrusted proof content.

---

## 9. Required behaviors

- Name gaps louder than successes.
- Keep core installable and auditable (stdlib core; optional math extras).
- Preserve offline reproducibility on air-gapped machines when toolchains are present.
- Document lineage when absorbing prototypes (see `LEGACY_PROTOTYPE_NOTES.md`).

---

## 10. Human attestation ritual

```text
mvpc audit ARTIFACT --policy default --json > /tmp/claim.json
# extract witness from claim.provenance.metadata.witness → witness.json
mvpc attest witness.json --signer "NAME" --notes "Reviewed coverage and findings"
mvpc witness verify witness.json
```

Attestation means: **I read the witness, I understand the coverage bounds, I accept or reject under my name.**

---

## 11. Amendment

Material changes to this covenant require:

1. Version bump and `CHANGELOG.md` entry.  
2. Explicit callout in PR description.  
3. No silent weakening of “never manufacture certainty.”

---

## 12. One-line oath

> We will not call it knowledge until a claim carries evidence, independent verification, provenance, a reproducible witness, and honest uncertainty—sealed by machines and, when required, by humans.

— **Sovereign Physics Lab / MVPC-X contributors**
