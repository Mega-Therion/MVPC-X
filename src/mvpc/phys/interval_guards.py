"""Layer 4: CPS interval arithmetic bounds + rate-of-change guards."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, List, Sequence


@dataclass
class Interval:
    lo: float
    hi: float

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            self.lo, self.hi = self.hi, self.lo

    def expand_relative(self, frac: float) -> "Interval":
        mid = 0.5 * (self.lo + self.hi)
        pad = abs(mid) * frac + frac
        return Interval(self.lo - pad, self.hi + pad)

    def exceeds_max(self, max_v: float) -> bool:
        return self.hi > max_v

    def below_min(self, min_v: float) -> bool:
        return self.lo < min_v


@dataclass
class IntervalGuardReport:
    ok: bool
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def point_to_interval(value: float, noise_frac: float = 0.05) -> Interval:
    return Interval(value, value).expand_relative(noise_frac)


def audit_interval_trajectory(
    times: Sequence[float],
    values: Sequence[float],
    *,
    max_value: float,
    min_value: float | None = None,
    noise_frac: float = 0.05,
    name: str = "x",
) -> IntervalGuardReport:
    violations: list[str] = []
    for t, v in zip(times, values):
        iv = point_to_interval(float(v), noise_frac)
        if iv.exceeds_max(max_value):
            violations.append(
                f"{name} interval at t={t:g}: [{iv.lo:g},{iv.hi:g}] exceeds max {max_value:g}"
            )
        if min_value is not None and iv.below_min(min_value):
            violations.append(
                f"{name} interval at t={t:g}: [{iv.lo:g},{iv.hi:g}] below min {min_value:g}"
            )
    return IntervalGuardReport(ok=not violations, violations=violations)


def audit_rate_of_change(
    times: Sequence[float],
    values: Sequence[float],
    *,
    max_abs_rate: float,
    name: str = "x",
) -> IntervalGuardReport:
    violations: list[str] = []
    for i in range(1, min(len(times), len(values))):
        dt = float(times[i]) - float(times[i - 1])
        if dt <= 0:
            violations.append(f"non-increasing time at i={i}")
            continue
        rate = (float(values[i]) - float(values[i - 1])) / dt
        if abs(rate) > max_abs_rate:
            violations.append(
                f"|{name}_dot|={abs(rate):g} at t={times[i]:g} exceeds {max_abs_rate:g}"
            )
    return IntervalGuardReport(ok=not violations, violations=violations)


def audit_cps_interval_and_rates(
    times: Sequence[float],
    velocity: Sequence[float],
    temperature: Sequence[float],
    *,
    max_velocity: float,
    max_temperature: float,
    max_accel: float = 50.0,
    max_thermal_rate: float = 20.0,
    noise_frac: float = 0.05,
) -> IntervalGuardReport:
    v_iv = audit_interval_trajectory(
        times, velocity, max_value=max_velocity, noise_frac=noise_frac, name="v"
    )
    t_iv = audit_interval_trajectory(
        times, temperature, max_value=max_temperature, noise_frac=noise_frac, name="T"
    )
    v_rate = audit_rate_of_change(times, velocity, max_abs_rate=max_accel, name="v")
    t_rate = audit_rate_of_change(
        times, temperature, max_abs_rate=max_thermal_rate, name="T"
    )
    violations = v_iv.violations + t_iv.violations + v_rate.violations + t_rate.violations
    return IntervalGuardReport(ok=not violations, violations=violations)
