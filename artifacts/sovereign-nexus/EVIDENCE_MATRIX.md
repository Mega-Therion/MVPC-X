# MVPC-X Sovereign Nexus Evidence Matrix

**Repository:** `Mega-Therion/MVPC-X`  
**Base revision:** `09876e858e092868ab413a59123ea6216f092031`  
**Scope:** Source-agnostic Nexus intake, PANI-neutral policy, local backend receipts, CAS certificate validation, Glass Box contracts, permanent linked manifests, and the verification-contract repairs required for a passing full suite.

> **Evidence rule:** A successful command records exactly what that command established. In particular, a normalizer, a static scan, a CAS polynomial identity, a model explanation, or a ledger entry is never treated as a formal proof. `FORMALLY_VERIFIED` requires a qualifying local native-backend receipt and intact run fingerprints.

| Requirement | Implementation surface | Executed verification | Evidence artifact | Status |
| --- | --- | --- | --- | --- |
| Proposer-Agnostic Neutral Invariant | `src/mvpc/nexus/policy.py` | Foundation and runtime tests | `pytest-full.txt` — SHA-256 `2f4e97862dda62918b6d7fc865b6eed1ddeb190a4eb4284406f64157e06a374d` | **[P] Tested:** policy accepts normalized source, not proposer identity; equivalent source receives the same deterministic decision. |
| Source-agnostic ingestion and structural AST normalization | `src/mvpc/nexus/ast_normalizer.py` | Foundation and runtime tests | `pytest-full.txt` | **[P] Tested:** Lean, Rocq, Isabelle, Dafny, LaTeX, and natural-language detection is deterministic; informal sources remain `UNTRANSLATED`. |
| Strict lexical zoning and zero-axiom intake gate | `src/mvpc/nexus/policy.py`, existing `core.lexical_zones` | Foundation tests | `pytest-full.txt` | **[P] Tested:** malformed zones, unbalanced syntax, and placeholder/axiom markers reject before a proof verdict. |
| MVPC_BIN hardening and dependency-manifest parity | `src/mvpc/nexus/intake.py` | Foundation tests | `pytest-full.txt` | **[P] Tested:** strict external mode rejects unpinned binaries; symlinks, escaped roots, mutable binaries, and digest mismatches are blocked. `pyproject.toml` and `DEPENDENCIES.md` are recorded and can be pinned. |
| Pre/mid/post environment fingerprinting | `src/mvpc/nexus/runtime.py`, existing `core.fingerprint` | Runtime tests and end-to-end CLI exercise | `pytest-full.txt` | **[P] Tested:** fingerprints are embedded in each permanent manifest; divergence produces `CORRUPTED` rather than a proof verdict. |
| Language-Agnostic Verification Array | `src/mvpc/nexus/backend_array.py` | Runtime tests | `pytest-full.txt` | **[P] Tested:** formal files delegate only to local MVPC-X backends, unavailable native tools become explicit coverage gaps, and inspect mode does not launch backends. |
| CAS certificate bridge | `src/mvpc/nexus/cas_certificate.py` | Runtime and CLI exercise | `pytest-full.txt` | **[P] Tested:** exact SymPy evaluation validates `f - Σ(cᵢbᵢ) = 0`; a changed target fails. Result text explicitly states that CAS is not kernel proof. |
| Glass Box traffic-light contract | `src/mvpc/nexus/glassbox.py` | Runtime tests | `pytest-full.txt` | **[P] Tested:** Green requires native completion, Orange represents conditional/untranslated work, and Red marks rejected/corrupted runs. |
| Permanent ledger manifests | `src/mvpc/nexus/manifest_ledger.py` | Foundation, runtime, and CLI exercise | `pytest-full.txt` | **[P] Tested:** paired `.json` and `.md` manifests chain from a genesis hash; JSON or linkage tampering is detected. |
| Workspace initialization | `src/mvpc/scaffold.py` | Runtime test and CLI exercise | `pytest-full.txt` | **[P] Tested:** `mvpc scaffold nexus` initializes human intent, formal source, CAS certificate, and ledger index files. |
| Legacy proof-record assurance compatibility | `assurance.py`, `verification_plan.py`, `proof_record.py`, `claim_consumer.py` | Full regression suite | `pytest-full.txt` | **[P] Repaired and tested:** scoped claim/proposition/artifact identity is carried into assurance evidence; legacy 3- and 5-positional constructors remain compatible; unknown artifact identities cannot become formal evidence. |
| Formatting and diff integrity | Modified Python sources and tests | `ruff format --check`; `git diff --check` | `format-check.txt` SHA-256 `ff581aaa8f1b2a77e28a682a7cae7b738f926730737e49664d06c810bcd5aa03`; `diff-check.txt` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | **[P] Verified:** modified source is formatted and the diff has no whitespace errors. |
| Nexus lint gate | New Nexus source and Nexus tests | `ruff check src/mvpc/nexus tests/nexus` | `ruff-nexus.txt` SHA-256 `5b196eb3a6acb50d3fa398d04ca284985cc1ffec870e940264b00780bfd2c971` | **[P] Verified:** no lint findings in the new Nexus package or its dedicated tests. |
| Secret exposure | Changed source and Nexus tests | Targeted token/private-key pattern scan | `secret-scan.txt` SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | **[P] Security-scanned:** no matched high-risk token or private-key pattern. |
| Declared dependency vulnerabilities | Test and math requirement set | `pip-audit -r declared-runtime-requirements.txt` | `pip-audit-declared.txt` SHA-256 `15950a68a7ed99c59779717acefdceb3f69cfd31bde67d2c954f2a3cea4d7955` | **[P] Audited:** no known vulnerabilities were reported for the declared requirement set. |
| Ambient sandbox dependency vulnerabilities | Broader preinstalled Python environment | `pip-audit` | `pip-audit.txt` SHA-256 `47beffb14980e20344946765f37e585ddadd49696a89cb6c6108426a7146375e` | **[C] Environment note:** audit reported 9 vulnerabilities in four preinstalled packages, including `pypdf`, `setuptools`, `wheel`, and `xhtml2pdf`. They are not MVPC-X declared dependencies, but deployment should use a clean isolated environment. |

## Executed Test Summary

| Command | Outcome |
| --- | --- |
| `pytest -q` | **167 passed** in 11.55 seconds. |
| `python3 -m compileall -q src` | Completed successfully. |
| `ruff format --check` on modified modules | Completed successfully. |
| `ruff check src/mvpc/nexus tests/nexus` | Completed successfully. |
| `pip-audit -r artifacts/sovereign-nexus/declared-runtime-requirements.txt` | No known vulnerabilities found. |

## Release Boundary

The Nexus implementation is **tested and integration-ready**. Its proof-status boundary is intentionally conservative: the current environment did not provide Lean, Rocq, Isabelle, or Dafny binaries, so end-to-end command exercises produced conditional/untranslated evidence where appropriate rather than a fabricated Green result. A deployment that needs `FORMALLY_VERIFIED` must install and pin the relevant native toolchain, run `mvpc nexus verify` in an isolated environment, and preserve the emitted permanent manifest pair.

The project-declared dependency audit passed. The broader sandbox audit detected unrelated preinstalled dependency advisories; the recommended deployment posture is a fresh virtual environment with only the declared MVPC-X dependencies, plus prompt patching of global tooling in any shared host image.

## Artifact Manifest

| Artifact | SHA-256 |
| --- | --- |
| `pytest-full.txt` | `2f4e97862dda62918b6d7fc865b6eed1ddeb190a4eb4284406f64157e06a374d` |
| `pip-audit-declared.txt` | `15950a68a7ed99c59779717acefdceb3f69cfd31bde67d2c954f2a3cea4d7955` |
| `pip-audit.txt` | `47beffb14980e20344946765f37e585ddadd49696a89cb6c6108426a7146375e` |
| `format-check.txt` | `ff581aaa8f1b2a77e28a682a7cae7b738f926730737e49664d06c810bcd5aa03` |
| `ruff-nexus.txt` | `5b196eb3a6acb50d3fa398d04ca284985cc1ffec870e940264b00780bfd2c971` |
| `diff-check.txt` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `secret-scan.txt` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
