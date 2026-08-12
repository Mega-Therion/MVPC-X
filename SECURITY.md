# Security & Threat Model

MVPC-X is designed for **adversarial artifacts**: proofs and scripts that may try to fool attestation **or** corrupt the verifier itself.

---

## 1. System self-integrity (primary control)

**Threat:** A malicious artifact (or concurrent process) modifies installed MVPC-X source while an audit runs, so later checks are weaker or always-green.

**Control:** *System fingerprint seal*

1. **Before ingest** — SHA-256 over every `mvpc/**/*.py` file → `system_fingerprint`.
2. **Mid-run** — recompute; must match before.
3. **After processing** — recompute; must match before.

Mismatch → finding `SYSTEM_INTEGRITY_FAILURE` (VIOLATION) and policy-level rejection under normal settings.

```bash
mvpc integrity --verify-twice
```

Witness/claim metadata includes the integrity session (`provenance.metadata.integrity`).

This is the “checksum before / during / after” property: **same system before the artifact is touched, same system after it is done.**

---

## 2. Artifact integrity (secondary)

**Threat:** File changes on disk during the run (editor, malware, race).

**Control:** Artifact SHA-256 pre + post; mismatch → `ARTIFACT_MUTATION`.

---

## 3. Intake guards

| Guard | Default |
|-------|---------|
| Max size | 50 MiB |
| Symlinks | Rejected (`--allow-symlinks` to allow) |
| Blocked extensions | `.exe`, `.dll`, `.so`, `.bat`, … |
| Optional `allowed_root` | Path jail for hosted deployments |

Blocked paths never reach backends.

---

## 4. Classic proof adversaries

| Attack | Mitigation |
|--------|------------|
| `sorry` / `admit` / `Admitted` / `oops` | Static VIOLATION |
| Bare `axiom` / smuggled kernel axioms | Static + Lean `#print axioms` allowlist |
| `native_decide` / `unsafe` | Flagged |
| Vacuous hypotheses | Optional Z3 layer |
| Python `eval`/`exec`/shell | Static flags; native path is `py_compile` only — **we do not execute arbitrary script bodies as the verifier** |
| Witness tampering | Root SHA-256 `mvpc witness verify` |

---

## 5. What we deliberately do *not* do

- Run untrusted binaries as part of “verification.”
- Trust AI text as evidence.
- Declare VERIFIED when the native kernel never ran (DEFAULT/STRICT).
- Pretend optional CAS/SMT ran when packages are missing.

---

## 6. Hosted / multi-tenant recommendations

If you wrap MVPC-X behind an upload API:

1. Store uploads outside the package install tree.  
2. Pass `allowed_root=` to intake (extend engine if you expose it).  
3. Run audits in a disposable container/VM.  
4. Treat `SYSTEM_INTEGRITY_FAILURE` as page-worthy.  
5. Do not mount the live `site-packages/mvpc` tree writable to the job user.  

---

## 7. Reporting

Report verifier bypasses or integrity bugs via GitHub Security Advisories on this repository or `viewsbyryan@gmail.com`.
