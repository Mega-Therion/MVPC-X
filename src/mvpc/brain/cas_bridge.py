"""SymPy/Sage CAS bridge for algebraic certificate sketches."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from mvpc.canonical import hash_canonical


@dataclass
class CASCertificate:
    success: bool
    engine: str
    problem: dict[str, Any]
    certificate: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def hash(self) -> str:
        return hash_canonical(self.to_dict())


def groebner_certificate(
    polynomials: list[str],
    variables: list[str],
    *,
    engine: str = "sympy",
) -> CASCertificate:
    problem = {"polynomials": polynomials, "variables": variables}
    if engine == "sympy":
        try:
            import sympy as sp
            from sympy import groebner
        except ImportError:
            return CASCertificate(
                success=False, engine="sympy", problem=problem, certificate="", notes="sympy not installed"
            )
        try:
            syms = sp.symbols(" ".join(variables))
            if not isinstance(syms, tuple):
                syms = (syms,)
            polys = [sp.sympify(p) for p in polynomials]
            G = groebner(polys, *syms, order="lex")
            cert = ", ".join(str(g) for g in G)
            return CASCertificate(
                success=True,
                engine="sympy",
                problem=problem,
                certificate=cert,
                notes="Gröbner basis computed; requires formal reification",
            )
        except Exception as exc:
            return CASCertificate(
                success=False, engine="sympy", problem=problem, certificate="", notes=str(exc)
            )
    if engine == "sage":
        return CASCertificate(
            success=False, engine="sage", problem=problem, certificate="", notes="Sage RPC not configured"
        )
    return CASCertificate(
        success=False, engine=engine, problem=problem, certificate="", notes=f"unknown engine {engine}"
    )
