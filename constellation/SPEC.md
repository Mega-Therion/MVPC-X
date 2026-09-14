# Constellation Health Receipt — v1.0.0

A uniform, fail-closed integrity contract shared by every repository in the
constellation. One command per repo, one machine-readable receipt, hash-chained.

## Why this exists

Three failure modes this constellation has actually hit, all of which this
contract makes visible instead of silent:

1. **A red CI read as a skipped CI.** Res-Nova's own gate script asserted for
   days that GitHub Actions was billing-locked and never executed. Actions was
   in fact running and *failing* — three real drifts had reached the default
   branch behind that misreading (2026-09-14).
2. **A published artifact drifting from the thing it attests.** 4Leibniz's
   committed `artifacts/v1/formal-claims.json` is what downstream consumers read
   "proved" badges from; CI regenerates a materially different catalog.
3. **Verified work that never lands.** Several thousand credits of agent work
   reported `go test PASS` against a sandbox clone and never reached any repo.

A receipt answers one question honestly: *as of this commit, which declared
invariants actually hold?*

## Contract

Every repository provides:

- `constellation/invariants.json` — the declaration (below).
- `scripts/health_receipt.py` — the runner. Identical across repos; its own
  hash is recorded in each receipt via `invariants_hash` + `schema_version`.
- `constellation/receipts/` — optional persisted receipts, hash-chained.

### `constellation/invariants.json`

```json
{
  "repo": "res-nova",
  "schema_version": "1.0.0",
  "invariants": [
    {
      "id": "local-gate",
      "cmd": "bash scripts/local_gate.sh",
      "required": true,
      "timeout": 900,
      "why": "the checks .github/workflows/verify.yml declares"
    }
  ]
}
```

`required: false` marks an invariant that is reported but does not fail the
receipt — use it for checks that are genuinely aspirational, and say so in
`why`. An optional invariant that never becomes required is a lie with extra
steps; it should either graduate or be deleted.

### Fail-closed rules (non-negotiable)

- A missing, unparseable, or empty `invariants.json` is a **FAIL**, never a pass.
  A repo that declares nothing cannot be healthy by default.
- An invariant that errors, times out, or declares no `cmd` is a **FAIL**.
- Exit status is non-zero unless every `required` invariant passed.
- Nothing is inferred. If a check did not run, it did not pass.

### Receipt integrity

`receipt_hash = sha256(canonical_json(receipt_without_receipt_hash))`, and
`prev_receipt_hash` points at the newest receipt already in
`constellation/receipts/`. Editing a persisted receipt breaks its own hash;
removing one from the middle breaks the chain. `tree_dirty` records whether the
working tree had uncommitted changes, so a receipt taken over a dirty tree can
never be mistaken for one taken over a commit.

## Epistemic tags

Shared vocabulary across every claim ledger in the constellation. These travel
with a claim; they are never stripped for readability.

| Tag | Meaning |
|---|---|
| `[P]` / `proved` | Machine-checked. Names the toolchain and the declaration. |
| `[D]` / `derived` | Explicit derivation, assumptions stated. Not machine-checked. |
| `[emp]` | Correlated with an identified dataset, within a stated scope. |
| `[C]` / `conditional` | Depends on an unresolved assumption, which is named. |
| `[conj]` | Conjecture. No derivation yet. |
| `[O]` / `open` | Open problem. Stated so it can be closed or refuted. |
| `refuted` | Preserved contradiction record. Never silently deleted. |

A claim may only be `proved` when a verifier actually checked it in the run
being reported. "It was proved last week" is `conditional` on that run.

## Usage

```bash
python3 scripts/health_receipt.py           # run, print receipt, exit 0/1
python3 scripts/health_receipt.py --write   # also persist + chain it
```

Canonical home: this file is vendored identically into each repository.
`schema_version` must match across copies; a mismatch means drift.
