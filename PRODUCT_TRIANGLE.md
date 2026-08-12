# Product triangle

MVPC-X is **one lane** of a three-product geometry. It must stay usable **alone**.

```text
Chyren-Aeon     (private)     full OmegA + Chyren synthesis for the owner only
Chyren-Archon   (public)      RIYU / SELIN open node  (repo: chyren-selin)
MVPC-X          (public)      THIS REPO — standalone mechanical claim/proof tool
```

## Dependency law

```text
MVPC-X  ──standalone──►  anyone (no Chyren required)
   ▲
   │ optional local call (CLI / subprocess)
   │
Chyren-Archon  (selin verify-artifact)
Chyren-Aeon    (private; same hook)
```

- **MVPC-X must never import or require** Archon, Aeon, or personal identity stores.
- **Archon and Aeon may call** `mvpc` on the same machine.
- People who only want proof checking install **only** this repo.

## What this repo is

Machine-verified proof / claim auditing: multi-backend checks, witnesses, system self-integrity, preflight, scaffold.

## What this repo is not

- Not a chatbot / ADCCL conversational governor  
- Not a RIYU identity product  
- Not the owner's private memory stack  

Those live in Archon (public) and Aeon (private).

## Consumer pin

Archon and Aeon should document a minimum MVPC version (e.g. `>=7.3.0`) and invoke:

```bash
mvpc audit PATH --policy default --ci-mode
# or via Archon:
selin verify-artifact PATH
```

See also: [chyren-selin docs/MVPC_INTEGRATION.md](https://github.com/Mega-Therion/chyren-selin/blob/main/docs/MVPC_INTEGRATION.md).
