"""Physical realization helpers (SI + hybrid automata)."""

from mvpc.phys.hybrid_automata import CPSSafetyAuditor, HybridAutomaton, HybridState, SafetyBounds
from mvpc.phys.si_units import SI_REGISTRY, SIDimension, SIDimensionChecker

__all__ = [
    "CPSSafetyAuditor",
    "HybridAutomaton",
    "HybridState",
    "SI_REGISTRY",
    "SIDimension",
    "SIDimensionChecker",
    "SafetyBounds",
]
