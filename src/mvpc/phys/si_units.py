"""SI base & derived dimensions — homogeneity checking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class SIDimension:
    mass: float = 0.0
    length: float = 0.0
    time: float = 0.0
    current: float = 0.0
    temperature: float = 0.0
    amount: float = 0.0
    luminous: float = 0.0

    def is_equal(self, other: "SIDimension", tol: float = 1e-6) -> bool:
        return (
            abs(self.mass - other.mass) < tol
            and abs(self.length - other.length) < tol
            and abs(self.time - other.time) < tol
            and abs(self.current - other.current) < tol
            and abs(self.temperature - other.temperature) < tol
            and abs(self.amount - other.amount) < tol
            and abs(self.luminous - other.luminous) < tol
        )

    def multiply(self, other: "SIDimension") -> "SIDimension":
        return SIDimension(
            mass=self.mass + other.mass,
            length=self.length + other.length,
            time=self.time + other.time,
            current=self.current + other.current,
            temperature=self.temperature + other.temperature,
            amount=self.amount + other.amount,
            luminous=self.luminous + other.luminous,
        )

    def divide(self, other: "SIDimension") -> "SIDimension":
        return SIDimension(
            mass=self.mass - other.mass,
            length=self.length - other.length,
            time=self.time - other.time,
            current=self.current - other.current,
            temperature=self.temperature - other.temperature,
            amount=self.amount - other.amount,
            luminous=self.luminous - other.luminous,
        )

    def power(self, p: float) -> "SIDimension":
        return SIDimension(
            mass=self.mass * p,
            length=self.length * p,
            time=self.time * p,
            current=self.current * p,
            temperature=self.temperature * p,
            amount=self.amount * p,
            luminous=self.luminous * p,
        )

    def to_string(self) -> str:
        units = []
        if self.mass != 0:
            units.append(f"[M]^{self.mass:g}")
        if self.length != 0:
            units.append(f"[L]^{self.length:g}")
        if self.time != 0:
            units.append(f"[T]^{self.time:g}")
        if self.current != 0:
            units.append(f"[I]^{self.current:g}")
        if self.temperature != 0:
            units.append(f"[Theta]^{self.temperature:g}")
        if self.amount != 0:
            units.append(f"[N]^{self.amount:g}")
        if self.luminous != 0:
            units.append(f"[J]^{self.luminous:g}")
        return " ".join(units) if units else "[Dimensionless]"


SI_REGISTRY: Dict[str, SIDimension] = {
    "dimensionless": SIDimension(),
    "mass": SIDimension(mass=1.0),
    "m": SIDimension(mass=1.0),
    "length": SIDimension(length=1.0),
    "x": SIDimension(length=1.0),
    "time": SIDimension(time=1.0),
    "t": SIDimension(time=1.0),
    "current": SIDimension(current=1.0),
    "I": SIDimension(current=1.0),
    "temperature": SIDimension(temperature=1.0),
    "T": SIDimension(temperature=1.0),
    "velocity": SIDimension(length=1.0, time=-1.0),
    "v": SIDimension(length=1.0, time=-1.0),
    "acceleration": SIDimension(length=1.0, time=-2.0),
    "a": SIDimension(length=1.0, time=-2.0),
    "force": SIDimension(mass=1.0, length=1.0, time=-2.0),
    "F": SIDimension(mass=1.0, length=1.0, time=-2.0),
    "energy": SIDimension(mass=1.0, length=2.0, time=-2.0),
    "E": SIDimension(mass=1.0, length=2.0, time=-2.0),
    "power": SIDimension(mass=1.0, length=2.0, time=-3.0),
    "P": SIDimension(mass=1.0, length=2.0, time=-3.0),
    "pressure": SIDimension(mass=1.0, length=-1.0, time=-2.0),
}


class SIDimensionChecker:
    def __init__(self) -> None:
        self.registry: Dict[str, SIDimension] = dict(SI_REGISTRY)

    def register_variable(self, name: str, dim: SIDimension) -> None:
        self.registry[name] = dim

    def check_homogeneity(self, dim1: SIDimension, dim2: SIDimension) -> bool:
        return dim1.is_equal(dim2)

    def verify_equation(self, lhs_var: str, rhs_terms: List[Tuple[str, float]]) -> Tuple[bool, str]:
        lhs_dim = self.registry.get(lhs_var)
        if not lhs_dim:
            return False, f"Unknown LHS variable '{lhs_var}' in SI registry."

        computed_rhs = SIDimension()
        for var_name, exp in rhs_terms:
            dim = self.registry.get(var_name)
            if not dim:
                return False, f"Unknown RHS variable '{var_name}' in SI registry."
            computed_rhs = computed_rhs.multiply(dim.power(exp))

        match = lhs_dim.is_equal(computed_rhs)
        msg = (
            f"LHS [{lhs_var}: {lhs_dim.to_string()}] vs "
            f"RHS [{computed_rhs.to_string()}] => Match: {match}"
        )
        return match, msg
