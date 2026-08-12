# Sovereign Nexus Implementation Status

**Spec:** `1.0.0-GOLD-SPEC` (see MVPC-X_Sovereign_Nexus_Spec_Sheet.md)  
**Aligned with:** trust foundation (verdict taxonomy, TCB, witness bundles)

## Core axiom (enforced in code comments and CLI copy)

> AI proposes. Machines verify. Humans audit. Evidence persists.

## Honest boundary

MVPC-X is a **verification and evidence-ledger engine**. It does **not** claim mathematical omniscience or absolute truth outside a declared TCB. Neural proof-search components are **proposer interfaces**; only trusted kernels may emit `FORMALLY_CHECKED`.

| Module | Spec intent | Status in tree |
|---|---|---|
| Neutral claim adapter | Source-agnostic intake | **Implemented** (`core/claim_adapter.py`) |
| Self-fingerprint pre/mid/post | Anti-tamper | **Implemented** (`core/fingerprint.py`) |
| SafeVerify axiom audit | sorryAx / unsafe / admit scan | **Implemented** (`core/safe_verify.py`) |
| Lexical zoning | EVOLVE-BLOCK / EVOLVE-VALUE | **Implemented** (`core/lexical_zones.py`) |
| Sandbox runner | No network, argv-only, limits | **Implemented** (`sandbox.py`) |
| Evidence ledger | Immutable chain + witness link | **Implemented** (`ledger.py`) |
| Lean/Coq/Isabelle backends | Existing harnesses | **Present** (pre-existing `backends/`) |
| Dafny backend | WP / Z3 harness | **Scaffold** (`backends/dafny.py`) |
| P-UCB + goal cache | Search control | **Implemented** (math + cache; no external LLM) |
| Elo rater | Sketch scoring | **Heuristic local rater** (not neural) |
| Planner / solver | 671B / 7B DeepSeek loop | **Interface + local stub only** |
| CAS bridge | SymPy/Sage reification | **SymPy path when installed; Sage optional RPC stub** |
| Dual-pane / proof tree UI | Glass box | **Data models + markdown/HTML export** (no GUI server yet) |
| Pantograph / SerAPI / PIDE | Live prover APIs | **Not bundled** — invoke installed tools |
| Dual-pane RL alignment | Spec Module 5 | **Not implemented** (requires training stack) |

## Next engineering slices

1. Wire adapter + fingerprint + SafeVerify through `engine.py` audit path.
2. CLI: `mvpc ingest`, `mvpc nexus-audit`, `mvpc verify-bundle`, `mvpc ledger`.
3. Real Pantograph/SerAPI/Dafny-server adapters behind the same backend contract.
4. Optional neural provider plugins (never in TCB).
5. Rust trust-kernel for offline bundle verify.
