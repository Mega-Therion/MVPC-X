# Dependencies

## Runtime (core)

| Requirement | Notes |
|-------------|--------|
| Python 3.10+ | Required |
| None beyond stdlib | Core audit path is zero-dep |

## Optional extras

```bash
pip install -e ".[math]"   # sympy, z3-solver, numpy
pip install -e ".[test]"   # pytest
pip install -e ".[all]"    # math + test
```

## Optional native toolchains (not pip)

| Tool | Used for |
|------|----------|
| `lean` / `lake` | Lean 4 kernel + axioms |
| `coqc` / `coqtop` | Coq |
| `isabelle` | Isabelle/HOL |

Missing tools → coverage gaps / CONDITIONAL or REJECTED by policy — never silent full VERIFIED under DEFAULT/STRICT when native was required.

## Reverse dependencies (may call MVPC)

| Consumer | How |
|----------|-----|
| Chyren-Archon (`chyren-selin`) | `selin verify-artifact` → `MVPC_BIN` (default `mvpc`) |
| Chyren-Aeon (private) | Same local CLI pattern |

## Environment

| Var | Meaning |
|-----|---------|
| *(none required for standalone)* | |
| Consumers set `MVPC_BIN` | Path to this CLI when not on PATH |

## Forbidden

- Depending on `chyren-*` packages  
- Network calls to owner infrastructure for verification  
- Shipping personal identity / AEON data  
