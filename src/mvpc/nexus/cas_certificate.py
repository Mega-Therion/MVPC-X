"""Local algebraic certificate validation for the Nexus CAS bridge.

A passing certificate establishes only the asserted polynomial identity
``f - Σ(c_i * b_i) = 0`` under SymPy's exact arithmetic. It is useful evidence,
but is never labeled as formal-kernel verification by this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:  # Optional dependency declared by MVPC-X's ``math`` extra.
    import sympy as sp
except ImportError:  # pragma: no cover - exercised where math extra is absent
    sp = None  # type: ignore[assignment]


_ALLOWED_EXPR = re.compile(r"^[A-Za-z0-9_+\-*/^().,\s]+$")
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class PolynomialCertificate:
    variables: tuple[str, ...]
    target: str
    generators: tuple[str, ...]
    coefficients: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PolynomialCertificate:
        variables = tuple(str(value) for value in data.get("variables", ()))
        target = str(data.get("target", ""))
        generators = tuple(str(value) for value in data.get("generators", ()))
        coefficients = tuple(str(value) for value in data.get("coefficients", ()))
        if not variables or not all(
            _IDENTIFIER.fullmatch(value) for value in variables
        ):
            raise ValueError("variables must contain one or more algebraic identifiers")
        if len(set(variables)) != len(variables):
            raise ValueError("variables must be unique")
        if not target or not generators or len(generators) != len(coefficients):
            raise ValueError(
                "target, generators, and equally sized coefficients are required"
            )
        for value in (target, *generators, *coefficients):
            if not _ALLOWED_EXPR.fullmatch(value) or "__" in value:
                raise ValueError("certificate expression contains unsupported syntax")
        return cls(
            variables=variables,
            target=target,
            generators=generators,
            coefficients=coefficients,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()


@dataclass(frozen=True)
class CasCertificateResult:
    available: bool
    valid: bool
    certificate_hash: str | None
    residual: str | None
    reason: str
    engine: str = "sympy"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_polynomial(expression: str, symbols: dict[str, Any]) -> Any:
    assert sp is not None
    parsed = sp.sympify(expression.replace("^", "**"), locals=symbols)
    # Constructing Poly rejects transcendental functions and symbols outside the
    # declared variable basis, which is the boundary required for this bridge.
    return sp.Poly(parsed, *symbols.values(), domain="QQ")


def verify_polynomial_certificate(
    certificate: PolynomialCertificate,
) -> CasCertificateResult:
    if sp is None:
        return CasCertificateResult(
            available=False,
            valid=False,
            certificate_hash=certificate.digest(),
            residual=None,
            reason="SymPy is not installed; CAS certificate was not evaluated.",
        )
    try:
        symbols = {name: sp.Symbol(name) for name in certificate.variables}
        target = _parse_polynomial(certificate.target, symbols)
        generators = [
            _parse_polynomial(value, symbols) for value in certificate.generators
        ]
        coefficients = [
            _parse_polynomial(value, symbols) for value in certificate.coefficients
        ]
        residual = target.as_expr() - sum(
            coefficient.as_expr() * generator.as_expr()
            for coefficient, generator in zip(coefficients, generators)
        )
        normalized = sp.Poly(sp.expand(residual), *symbols.values(), domain="QQ")
        is_zero = normalized.is_zero
        return CasCertificateResult(
            available=True,
            valid=bool(is_zero),
            certificate_hash=certificate.digest(),
            residual=str(normalized.as_expr()),
            reason=(
                "Exact polynomial residual is zero. This is CAS evidence, not formal-kernel proof."
                if is_zero
                else "Polynomial residual is non-zero; certificate does not establish ideal membership."
            ),
        )
    except Exception as exc:  # noqa: BLE001 - symbolic parser failures are returned as certificate data
        return CasCertificateResult(
            available=True,
            valid=False,
            certificate_hash=certificate.digest(),
            residual=None,
            reason=f"Certificate rejected: {type(exc).__name__}: {exc}",
        )


def verify_certificate_file(path: str | Path) -> CasCertificateResult:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError("certificate JSON must be an object")
    return verify_polynomial_certificate(PolynomialCertificate.from_dict(raw))
