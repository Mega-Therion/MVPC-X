"""CPS realization bridge & zero physical leakage certifier."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from mvpc.phys.hybrid_automata import CPSSafetyAuditor, SafetyBounds
from mvpc.phys.si_units import SIDimensionChecker


class ZeroLeakageCertifier:
    @staticmethod
    def verify_physical_realization(
        physical_variables: Dict[str, str],
        si_checker: SIDimensionChecker,
        requires_si_checking: bool = True,
    ) -> Tuple[bool, str]:
        if not requires_si_checking:
            return True, "SI Checking not required for this abstract formal claim."

        unregistered = []
        for var_name, dim_type in physical_variables.items():
            if dim_type not in si_checker.registry and var_name not in si_checker.registry:
                unregistered.append(var_name)

        if unregistered:
            return (
                False,
                f"Physical Realization Leakage Detected: Unregistered physical variables {unregistered}",
            )

        return (
            True,
            "Zero Physical Leakage Certified: All formal quantities strictly mapped to SI dimensions.",
        )


class CPSRealizationBridge:
    def __init__(self) -> None:
        self.si_checker = SIDimensionChecker()
        self.cps_auditor = CPSSafetyAuditor()

    def audit_claim_physics(
        self,
        physical_variables: Dict[str, str],
        trajectory_data: Optional[Tuple[List[float], List[float], List[float]]] = None,
        max_velocity: float = 100.0,
        max_temperature: float = 350.0,
        requires_si_checking: bool = True,
    ) -> Dict[str, Any]:
        leakage_ok, leakage_msg = ZeroLeakageCertifier.verify_physical_realization(
            physical_variables,
            self.si_checker,
            requires_si_checking=requires_si_checking,
        )

        cps_ok = True
        violations: List[str] = []
        if trajectory_data:
            time_steps, velocity_prof, temp_prof = trajectory_data
            bounds = SafetyBounds(
                max_velocity=max_velocity, max_temperature=max_temperature
            )
            cps_ok, violations = self.cps_auditor.audit_trajectory(
                time_steps, velocity_prof, temp_prof, bounds=bounds
            )

        return {
            "physical_audit_passed": leakage_ok and cps_ok,
            "zero_leakage_certified": leakage_ok,
            "zero_leakage_details": leakage_msg,
            "cps_safety_passed": cps_ok,
            "cps_violations": violations,
        }
