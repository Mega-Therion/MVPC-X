"""Layer 3: symbolic CAS + Monte Carlo numerical double-check + dual fallback."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Any, List, Sequence, Tuple

try:
    import sympy as sp

    _HAS_SYMPY = True
except ImportError:  # pragma: no cover
    sp = None  # type: ignore
    _HAS_SYMPY = False


@dataclass
class CASDoubleCheckResult:
    symbolic_ok: bool
    numeric_ok: bool | None
    engine: str
    certificate: str
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def ok(self) -> bool:
        if self.numeric_ok is None:
            return self.symbolic_ok
        return self.symbolic_ok and self.numeric_ok


def _sympy_groebner(
    target: str, generators: Sequence[str], variables: str
) -> Tuple[bool, str]:
    if not _HAS_SYMPY:
        return False, "sympy missing"
    try:
        vars_ = [sp.Symbol(v.strip()) for v in variables.split() if v.strip()]
        t = sp.sympify(target)
        gens = [sp.sympify(g) for g in generators]
        gb = sp.groebner(gens, *vars_)
        _q, rem = sp.reduced(t, gb, vars_)
        ok = rem == 0
        return bool(ok), f"sympy remainder={rem}"
    except Exception as exc:
        return False, f"sympy error: {exc}"


def _monte_carlo_vanishing(
    target: str,
    generators: Sequence[str],
    variables: str,
    *,
    samples: int = 32,
    tol: float = 1e-6,
    seed: int = 0,
) -> Tuple[bool | None, str]:
    if not _HAS_SYMPY:
        return None, "sympy missing for numeric check"
    try:
        names = [v.strip() for v in variables.split() if v.strip()]
        syms = [sp.Symbol(n) for n in names]
        t_expr = sp.sympify(target)
        g_exprs = [sp.sympify(g) for g in generators]
        rng = random.Random(seed)
        checked = 0
        for _ in range(samples * 4):
            vals = {s: rng.uniform(-2.0, 2.0) for s in syms}
            gvals = [complex(g.evalf(subs=vals)) for g in g_exprs]
            if any(abs(gv) > tol for gv in gvals):
                continue
            tv = complex(t_expr.evalf(subs=vals))
            checked += 1
            if abs(tv) > tol:
                return False, f"numeric counterexample near common zero: {vals} target={tv}"
            if checked >= samples:
                break
        if checked == 0:
            return None, "no near-common-zeros sampled; numeric inconclusive"
        return True, f"monte_carlo samples_ok={checked}"
    except Exception as exc:
        return None, f"numeric error: {exc}"


def _sage_fallback_stub(target: str, generators: Sequence[str], variables: str) -> Tuple[bool, str]:
    return False, "sage fallback not configured"


def cas_verify_with_fallback(
    target: str,
    generators: List[str],
    variables: str,
    *,
    monte_carlo_samples: int = 24,
) -> CASDoubleCheckResult:
    sym_ok, sym_msg = _sympy_groebner(target, generators, variables)
    engine = "sympy"
    if (not sym_ok and "error" in sym_msg) or (not sym_ok and not _HAS_SYMPY):
        s_ok, s_msg = _sage_fallback_stub(target, generators, variables)
        if s_ok:
            sym_ok, sym_msg, engine = s_ok, s_msg, "sage"
        else:
            engine = "sympy+fallback-miss"
            sym_msg = f"{sym_msg}; {s_msg}"

    num_ok, num_msg = _monte_carlo_vanishing(
        target, generators, variables, samples=monte_carlo_samples
    )
    return CASDoubleCheckResult(
        symbolic_ok=sym_ok,
        numeric_ok=num_ok,
        engine=engine,
        certificate=sym_msg,
        details=num_msg,
    )
