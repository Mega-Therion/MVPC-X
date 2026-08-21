# MVPC-X Sovereign Nexus: Implementation Contract

## Purpose and Boundary

The Sovereign Nexus extends MVPC-X as an **additive, source-agnostic verification control plane**. It preserves the repository’s existing rule that a claim is the atomic unit of truth and adds the workflow requested in the supplied blueprint: normalized intake, deterministic preflight hardening, multi-backend evidence, CAS certificate checking, glass-box output, and permanent linked manifests.

> **PANI rule:** The proposer may be recorded as provenance, but is excluded from mechanical verdict calculation. A formal source accepted by a kernel is not stronger or weaker because it was written by a human, an AI system, or a mixed team.

The Nexus does **not** claim to translate informal natural language into a valid Lean, Rocq, Isabelle, or Dafny proof. In this release, informal and LaTeX inputs normalize into a canonical structural representation and remain `UNTRANSLATED` until a separately supplied formal artifact reaches a native kernel. This boundary prevents a proposed translation from being mislabeled as a formal proof.

## Architecture Mapping

| Blueprint concern | Existing MVPC-X seam | Nexus addition |
| --- | --- | --- |
| Source-agnostic AST ingestion | Backend registry and preflight | Canonical `NormalizedAst`, language detection, declaration extraction, balance checks, and source hash |
| LAVA multi-backend array | Lean, Coq, Isabelle, Dafny, Python backends | Uniform backend receipts with static/native coverage and explicit unavailable states |
| CAS bridge | `brain.cas_bridge` and SymPy support | Canonical JSON polynomial-certificate verification of `f - Σ(cᵢbᵢ) = 0` |
| PANI and lexical zoning | Claim provenance and `core.lexical_zones` | Proposer-neutral decision input and zone-validation evidence |
| Self-fingerprinting | `core.fingerprint` and `security.IntegritySession` | Pre/mid/post snapshots, `MVPC_BIN` trust report, and manifest/dependency parity evidence |
| Permanent ledger | `EvidenceLedger` and witnesses | Paired, canonical `.json` and `.md` manifests chained by the previous manifest hash |
| Glass Box UX | `ui.dual_pane` and `ui.proof_tree` | Stable JSON/Markdown data contract with explicit Green, Orange, and Red semantics |

## Verdict Semantics

| State | Meaning | Required evidence |
| --- | --- | --- |
| `FORMALLY_VERIFIED` | A configured native backend completed without blocking findings and policy permits the result | Native backend receipt, stable fingerprint, zero-axiom audit, and linked manifest |
| `CONDITIONAL` | Source is structurally analyzable but no qualifying native verification completed | Static receipt plus explicit coverage gap |
| `REJECTED` | Intake, syntax, policy, zone, certificate, integrity, or native backend check failed | Machine-readable failure reasons and linked failure manifest |
| `UNTRANSLATED` | Natural-language or LaTeX input has no supplied formal artifact | Normalized source representation only; never a proof claim |

A valid CAS certificate is **algebraic evidence**, not a substitute for formal-kernel verification. A Green status is therefore reserved for a qualifying native backend receipt; CAS success may enrich a manifest but cannot independently turn an informal claim into `FORMALLY_VERIFIED`.

## Intake and Integrity Model

The control plane uses the current MVPC-X intake guard first. The Nexus then verifies optional caller-provided `MVPC_BIN` configuration. A trusted external binary must be a regular, non-symlink executable beneath an approved root, must not be group- or world-writable, and must match a configured SHA-256 pin in strict mode. If the caller supplies no `MVPC_BIN`, standalone local verification stays available and the manifest records that no external consumer binary was relied upon.

Dependency parity captures the content hashes of `pyproject.toml` and `DEPENDENCIES.md`. A configured expected lock digest is enforced when present. The manifest records the observed digest and whether an expected digest was supplied; it does not invent a package-lock guarantee where the repository has none.

Any pre→mid, pre→post, or mid→post fingerprint divergence produces a `CORRUPTED` manifest and blocks release of a verification verdict. The ledger can record the failure, but a corrupted run cannot become a proof witness.

## Public Runtime Contract

The new `mvpc nexus` command will expose three deterministic operations:

| Command | Role | External side effects |
| --- | --- | --- |
| `mvpc nexus inspect <artifact>` | Normalize source, run hardened preflight, emit Glass Box JSON/Markdown | None beyond optional output files |
| `mvpc nexus verify <artifact>` | Run source normalization, policy gates, backend array, fingerprinting, and ledger emission | Executes installed local formal tools only; no network calls |
| `mvpc nexus cas-verify <certificate.json>` | Validate an explicit polynomial certificate | Local SymPy only when installed; otherwise reports unavailable |

The implementation will keep the existing `mvpc audit`, `mvpc preflight`, and `mvpc integrity` commands intact. `mvpc nexus` is an explicit additional pathway rather than a silent change to legacy audit semantics.

## Acceptance Requirements

The implementation must prove through tests that it does all of the following.

| Requirement | Testable behavior |
| --- | --- |
| PANI | Different provenance labels yield the same deterministic outcome for equivalent source and policy inputs |
| Informal-source safety | LaTeX and natural-language source cannot be reported as formally verified |
| Intake hardening | Unsafe, escaped, mutable, unpinned, or symlinked `MVPC_BIN` configurations are rejected in strict mode |
| Dependency parity | `pyproject.toml` and `DEPENDENCIES.md` are hashed and a mismatched expected digest is rejected |
| Fingerprint integrity | A divergence marks the run corrupted and blocks a proof verdict |
| LAVA truthfulness | Missing native tools report coverage gaps; they never become kernel evidence |
| CAS certificate checking | A correct `f - Σ(cᵢbᵢ) = 0` certificate passes and a changed coefficient fails |
| Ledger integrity | JSON/Markdown manifest pairs share a digest, chain to the prior manifest, and detect tampering |
| Glass Box status | Green requires a native verified receipt; Orange represents conditional/untranslated work; Red represents rejected/corrupted work |

## Non-Goals

This release does not bundle Lean, Rocq, Isabelle, Dafny, SageMath, or an LLM service. It does not send source code to a network provider. It does not accept a machine-generated explanation, confidence score, or CAS output as a formal proof. These are deliberate trust boundaries, not deferred claims of completion.
