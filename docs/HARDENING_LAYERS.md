# Five Hardening Layers

| # | Layer | Module |
|---|---|---|
| 1 | Anti-equivocation + Merkle AST digests | `hardening/crypto_integrity.py` |
| 2 | Multi-engine consensus + resource quotas | `hardening/consensus.py`, `hardening/quotas.py` |
| 3 | CAS Monte Carlo double-check + fallback | `hardening/cas_doublecheck.py` |
| 4 | CPS interval + rate-of-change guards | `phys/interval_guards.py` |
| 5 | AEON repair loop + transitive axiom scan | `hardening/repair_loop.py`, `hardening/transitive_scan.py` |

## Principles

- Signatures bind *who* attested a tip; hashes bind *what* was chained.
- Consensus raises confidence; it does not invent formal truth.
- Repair patches are zone-bounded (`EVOLVE-BLOCK` / `EVOLVE-VALUE`) with max depth.
- Transitive scans fail closed on `sorry`/`admit`/`unsafe` in dependency graphs when files are available.
