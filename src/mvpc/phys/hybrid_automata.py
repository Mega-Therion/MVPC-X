"""CPS hybrid automata + trajectory safety auditor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


@dataclass
class HybridState:
    mode: str
    time: float
    continuous_vars: Dict[str, float] = field(default_factory=dict)


@dataclass
class SafetyBounds:
    max_velocity: float = 100.0
    max_temperature: float = 350.0
    max_kinetic_energy: float = 1e6
    max_pressure: float = 1e7


class HybridAutomaton:
    def __init__(self, initial_mode: str, initial_vars: Dict[str, float]) -> None:
        self.current_state = HybridState(
            mode=initial_mode, time=0.0, continuous_vars=dict(initial_vars)
        )
        self.trajectory: List[HybridState] = [self.current_state]

    def step(
        self,
        dt: float,
        flow_map: Callable[[HybridState], Dict[str, float]],
        next_mode: Optional[str] = None,
    ) -> None:
        derivatives = flow_map(self.current_state)
        new_vars = {}
        for var, val in self.current_state.continuous_vars.items():
            der = derivatives.get(var, 0.0)
            new_vars[var] = val + der * dt

        new_mode = next_mode if next_mode else self.current_state.mode
        new_time = self.current_state.time + dt
        self.current_state = HybridState(
            mode=new_mode, time=new_time, continuous_vars=new_vars
        )
        self.trajectory.append(self.current_state)


class CPSSafetyAuditor:
    @staticmethod
    def audit_trajectory(
        time_steps: List[float],
        velocity_profile: List[float],
        temperature_profile: List[float],
        mass_kg: float = 1.0,
        bounds: Optional[SafetyBounds] = None,
    ) -> Tuple[bool, List[str]]:
        if bounds is None:
            bounds = SafetyBounds()

        violations: List[str] = []
        for t, v, temp in zip(time_steps, velocity_profile, temperature_profile):
            if v > bounds.max_velocity:
                violations.append(
                    f"Kinetic Velocity Bound Violation at t={t:g}s: "
                    f"{v:g} m/s > limit {bounds.max_velocity:g} m/s"
                )
            if temp > bounds.max_temperature:
                violations.append(
                    f"Thermal Limits Bound Violation at t={t:g}s: "
                    f"{temp:g} K > limit {bounds.max_temperature:g} K"
                )
            ke = 0.5 * mass_kg * (v**2)
            if ke > bounds.max_kinetic_energy:
                violations.append(
                    f"Kinetic Energy Bound Violation at t={t:g}s: "
                    f"{ke:g} J > limit {bounds.max_kinetic_energy:g} J"
                )

        return len(violations) == 0, violations
