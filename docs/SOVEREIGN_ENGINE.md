# Sovereign Nexus Engine Runtime

**Module:** `mvpc.sovereign_engine`  
**Spec:** 2.0.0-ULTRA-GOLD

## Run demo

```bash
pip install -e ".[all]"
python -m mvpc.sovereign_engine
```

## API

```python
from mvpc.sovereign_engine import SovereignNexusEngine

engine = SovereignNexusEngine()
result = engine.process_and_verify(raw_claim_json, trajectory_data=..., cas_polynomials=...)
```

## Trust alignment

Heuristic backend drivers do **not** emit `FORMALLY_CHECKED`.

| Field | Meaning |
|---|---|
| `heuristic_pass` | Syntax looks like a theorem; no sorry/admit/assume |
| `trust_verdict` | MVPC-X taxonomy label |
| `FORMALLY_CHECKED` | Requires real kernel acceptance |

## Fixes vs raw monolith

1. Removed duplicate `cps_safety_certification` key/typo
2. `trust_verdict` + `heuristic_pass` instead of overstated `verified`
3. Shared `safe_verify_source`
4. Optional SymPy
5. Stable fingerprint digest (no wall-clock in hash core)
