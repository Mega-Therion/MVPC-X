# Golden Witness Demo

This directory is the **public end-to-end demo** of the biomechanical covenant:

1. Audit adversarial and clean fixtures.  
2. Emit claim JSON (with embedded witness).  
3. Optionally seal human attestation.  
4. Verify witness integrity offline.

## Quick demo (from repo root)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"

# 1) Reject unfinished proof
mvpc audit tests/fixtures/sorry.lean --policy default

# 2) JSON claim + witness metadata
mvpc audit tests/fixtures/sorry.lean --json > examples/golden/out_sorry_claim.json

# 3) Clean Lean under permissive (static sufficient)
mvpc audit tests/fixtures/clean.lean --policy permissive --json > examples/golden/out_clean_claim.json

# 4) Math claims (SymPy / optional Z3)
mvpc audit tests/fixtures/math_claims.py --json > examples/golden/out_math_claim.json

# 5) Extract witness and attest (human seal)
python examples/golden/extract_and_attest.py examples/golden/out_clean_claim.json \
  --signer "Demo Reviewer" --notes "Golden path review"

# 6) Verify seal
mvpc witness verify examples/golden/out_clean_witness.json
```

## What “good” looks like

| Artifact | Expected tendency |
|----------|-------------------|
| `sorry.lean` | `REJECTED` + `LEAN_SORRY` |
| `axiom_smuggle.lean` | findings on bare axiom / danger |
| `clean.lean` | `VERIFIED` (permissive) or `CONDITIONAL`/`VERIFIED` (default w/ lean) |
| `math_claims.py` | no identity violations when sympy installed |
| attested witness | `mvpc witness verify` → VALID |

## Covenant reminder

Absence of errors under a weak policy is not STRICT science.  
Read `checks_unavailable` before you trust a green state.

See [COVENANT.md](../../COVENANT.md).
