"""Physical realization helpers (SI + hybrid automata + interval guards)."""

from mvpc.phys.hybrid_automata import CPSSafetyAuditor, HybridAutomaton, HybridState, SafetyBounds
from mvpc.phys.interval_guards import (
    Interval,
    IntervalGuardReport,
    audit_cps_interval_and_rates,
    audit_interval_trajectory,
    audit_rate_of_change,
)
from mvpc.phys.si_units import SI_REGISTRY, SIDimension, SIDimensionChecker

__all__ = [
    "CPSSafetyAuditor",
    "HybridAutomaton",
    "HybridState",
    "Interval",
    "IntervalGuardReport",
    "SI_REGISTRY",
    "SIDimension",
    "SIDimensionChecker",
    "SafetyBounds",
    "audit_cps_interval_and_rates",
    "audit_interval_trajectory",
    "audit_rate_of_change",
]
