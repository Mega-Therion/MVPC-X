"""Scaffold standard package shapes for higher-assurance audits."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

TEMPLATES: Dict[str, Dict[str, str]] = {
    "lean": {
        "Basic.lean": """-- MVPC-X Lean template (stdlib-friendly; no Mathlib required)
-- Replace with real mathematics. Never leave `sorry` in trusted surface.

theorem add_comm_nat (a b : Nat) : a + b = b + a := by
  omega
""",
        "README.md": """# Lean scaffold

```bash
mvpc preflight Basic.lean
mvpc audit Basic.lean --policy default
```

For Mathlib projects, place this file inside a Lake package and run from the package root.
""",
    },
    "coq": {
        "Basic.v": """(* MVPC-X Coq template *)
Theorem add_0_r : forall n : nat, n + 0 = n.
Proof.
  intro n. induction n; simpl; auto.
Qed.
""",
        "README.md": """# Coq scaffold

```bash
mvpc preflight Basic.v
mvpc audit Basic.v --policy default
```
""",
    },
    "isabelle": {
        "Basic.thy": """theory Basic
  imports Main
begin

lemma add_comm_nat: "a + b = (b + a :: nat)"
  by simp

end
""",
        "README.md": """# Isabelle scaffold

Add a ROOT session file for native `isabelle build`.
```bash
mvpc preflight Basic.thy
mvpc audit Basic.thy
```
""",
    },
    "python-math": {
        "claims.py": """# MVPC-X mathematical claims template
# MVPC-CLAIM identity: sin(x)**2 + cos(x)**2 == 1
# MVPC-CLAIM identity: (x + y)**2 == x**2 + 2*x*y + y**2
# MVPC-CLAIM numeric: (x + 1)**2 == x**2 + 2*x + 1 samples=x:-2,-1,0,1,2

def smoke() -> bool:
    return True

if __name__ == "__main__":
    assert smoke()
""",
        "README.md": """# Python math scaffold

```bash
pip install -e ".[math]"   # from MVPC-X repo, or: pip install sympy z3-solver numpy
mvpc preflight claims.py
mvpc audit claims.py --policy default
```
""",
    },
    "claim": {
        "claim.yaml": """# MVPC-X claim manifest template (multi-evidence package)
claim:
  statement: "Replace with your proposition"
  origin: human   # human | ai | mixed
  scope: "domain / paper section"
  assumptions:
    - "List explicit assumptions"
  evidence:
    - type: formal_proof
      path: Basic.lean
    - type: computation
      path: claims.py
  ai_provenance:
    model: null
    prompt_file: null
""",
        "README.md": """# Claim manifest scaffold

Point evidence paths at real artifacts, then:
```bash
mvpc preflight claim.yaml
# Full YAML claim engine may be partial — audit each evidence path:
mvpc audit Basic.lean
mvpc audit claims.py
```
""",
    },
}

ALIASES = {
    "py": "python-math",
    "python": "python-math",
    "math": "python-math",
    "thy": "isabelle",
    "v": "coq",
    "manifest": "claim",
    "yaml": "claim",
}


def list_templates() -> List[str]:
    return sorted(TEMPLATES.keys())


def scaffold(kind: str, dest_dir: str, *, force: bool = False) -> List[str]:
    """Write template files into dest_dir. Returns paths written."""
    key = ALIASES.get(kind.lower(), kind.lower())
    if key not in TEMPLATES:
        raise ValueError(
            f"Unknown template '{kind}'. Choose from: {', '.join(list_templates())}"
        )
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for name, content in TEMPLATES[key].items():
        target = dest / name
        if target.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite {target} (use --force)")
        target.write_text(content, encoding="utf-8")
        written.append(str(target.resolve()))
    return written
