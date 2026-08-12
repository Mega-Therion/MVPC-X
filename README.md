# MVPC-X

**Standalone mechanical claim- and proof-verification tool.**

> AI proposes. Machines verify. Humans audit. Evidence persists.

[![CI](https://github.com/Mega-Therion/MVPC-X/actions/workflows/ci.yml/badge.svg)](https://github.com/Mega-Therion/MVPC-X/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## Product triangle (read this first)

| Product | Repo | You need it if… |
|---------|------|------------------|
| **MVPC-X** (this repo) | [MVPC-X](https://github.com/Mega-Therion/MVPC-X) | You only want a **proof/claim auditor** |
| **Chyren-Archon** | [chyren-selin](https://github.com/Mega-Therion/chyren-selin) | You want a **public RIYU / ADCCL node** (optional MVPC) |
| **Chyren-Aeon** | private | Owner-only full stack |

**MVPC-X does not require Archon or Aeon.**  
Archon and Aeon *can* call MVPC locally for formal files.

Details: [PRODUCT_TRIANGLE.md](PRODUCT_TRIANGLE.md) · [DEPENDENCIES.md](DEPENDENCIES.md)

---

## Install

```bash
git clone https://github.com/Mega-Therion/MVPC-X.git
cd MVPC-X
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"
mvpc --help
```

## Quick use

```bash
mvpc integrity --verify-twice
mvpc preflight path/to/File.lean
mvpc audit path/to/File.lean --policy default
mvpc scaffold lean ./demo && mvpc audit ./demo/Basic.lean
```

From **Chyren-Archon** (if installed):

```bash
export MVPC_BIN=mvpc
selin verify-artifact path/to/File.lean
```

## What it does

- Multi-backend audit (Lean, Coq, Isabelle, Python claims, generic)
- Witness JSON/Markdown + hash integrity
- **System self-fingerprint** before / mid / after audit (verifier anti-tamper)
- Intake guards, preflight readiness, templates

## Covenant

See [COVENANT.md](COVENANT.md) and [SECURITY.md](SECURITY.md).

## License

MIT — [LICENSE](LICENSE)
