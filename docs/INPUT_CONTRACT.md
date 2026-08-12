# Input Contract

**Ingest is open. Assurance is proportional to structure + tools.**

This is the MVPC-X contract for what users may put through the gate, and what the system promises back.

---

## 1. Two layers

| Layer | Promise |
|-------|---------|
| **Open ingest** | Almost any path can be submitted. We will not crash the verifier. We emit a claim/witness with honest coverage. |
| **Structured upgrade** | If you follow a supported shape (Lean/Coq/Isabelle/Python claims/manifest), you unlock deeper mechanical checks and stronger attestation. |

We do **not** require templates to run.  
We **do** recommend templates when you want `ready_for_deep_audit`.

---

## 2. What happens to weird inputs

| Input | Behavior |
|-------|----------|
| Supported extension + tools present | Specialized backend (static ± native) |
| Supported extension, tools missing | Static / partial → often `CONDITIONAL` under DEFAULT |
| Random `.txt` / unknown type | Generic hasher + coverage limits → not fake VERIFIED under DEFAULT/STRICT |
| Symlink | **Blocked** by default (`--allow-symlinks` to override) |
| Huge file (>50 MiB default) | **Blocked** at intake |
| `.exe` / `.dll` / similar | **Blocked** at intake |
| Malicious file that mutates MVPC-X on disk | **System integrity seal fails** mid/post run → `SYSTEM_INTEGRITY_FAILURE` |

---

## 3. Standard shapes (templates)

```bash
mvpc scaffold lean ./my_proof
mvpc scaffold coq ./my_proof
mvpc scaffold isabelle ./my_proof
mvpc scaffold python-math ./my_math
mvpc scaffold claim ./my_claim_pkg
```

Then:

```bash
mvpc preflight ./my_proof/Basic.lean
mvpc audit ./my_proof/Basic.lean --policy default
```

### Lean notes ("custom Lean")

- Single-file stdlib theorems: fine standalone.
- Mathlib imports: run inside a **Lake** project (`lakefile.lean` / `lakefile.toml`). Preflight will say `needs_project_context` if Lake is missing.
- MVPC-X does not rewrite your theory; it audits what you give it.

---

## 4. Preflight readiness values

| Value | Meaning |
|-------|---------|
| `ready_for_deep_audit` | Structure + tools look good for a serious run |
| `needs_project_context` | File type OK but toolchain/project root incomplete |
| `template_suggested` | Will run, but scaffold would raise assurance |
| `generic_only` | Hash/placeholder path only |
| `blocked` | Intake security rejected the path |

Preflight **never** claims the math is true. It only ranks *readiness*.

---

## 5. System self-integrity (the real "checksum")

Before any artifact is processed, MVPC-X fingerprints **itself** (all installed `mvpc/**/*.py` files → root SHA-256).

- **Mid-run** (default): re-fingerprint; must match.
- **Post-run**: re-fingerprint; must match.

If a payload somehow altered the verifier on disk during the run, attestation fails closed with `SYSTEM_INTEGRITY_FAILURE`.

Also recorded: artifact SHA-256 before/after (secondary tamper signal).

```bash
mvpc integrity              # show system fingerprint
mvpc integrity --verify-twice
mvpc audit file.lean        # seals embedded in claim.provenance.metadata.integrity
```

---

## 6. Operator checklist

1. `pip install -e ".[all]"` (or core + native toolchains you need)  
2. `mvpc integrity`  
3. `mvpc preflight PATH`  
4. Fix recommendations / `mvpc scaffold …` if needed  
5. `mvpc audit PATH --policy default`  
6. Read `checks_unavailable` before trusting green  
7. `mvpc attest` when humans must seal  

---

## 7. Non-goals

- Auto-formalizing English into Lean/Coq  
- Guaranteeing absolute mathematical truth  
- Running arbitrary user binaries  
- Silent success when tools are missing  

See [COVENANT.md](../COVENANT.md) and [SECURITY.md](../SECURITY.md).
