# P0 Pipeline / CPS / CLI

## Modules

| Path | Role |
|---|---|
| `src/mvpc/phys/si_units.py` | SI dimensional homogeneity |
| `src/mvpc/phys/hybrid_automata.py` | Hybrid automaton + CPS trajectory bounds |
| `src/mvpc/cps_realization.py` | Leakage certifier + physics bridge |
| `src/mvpc/nexus_pipeline.py` | Full audit orchestrator |
| `src/mvpc/nexus_cli.py` | CLI: audit / cps-check / si-check |

## Run

```bash
pip install -e ".[all]"
python -m mvpc.nexus_cli audit --claim-file claim.json
python -m mvpc.nexus_cli si-check --lhs F --rhs m:1.0,a:1.0
python -m mvpc.nexus_cli cps-check --v-max 100 --temp-max 350
```

## Trust note

Pipeline backends are **heuristic** unless a real kernel is wired.
`trust_verdict` will not be `FORMALLY_CHECKED` from string scans alone.

## Fixes applied on intake

- `si-check` RHS exponent parse bug fixed (`bits[1]` not `var_exp.strip()`)
- SymPy optional for CAS
- Markdown report no longer says "Formally Verified" for heuristic passes
