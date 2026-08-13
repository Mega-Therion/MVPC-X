"""End-to-end pipeline with all five hardening layers wired in."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

from mvpc.hardening.cas_doublecheck import cas_verify_with_fallback
from mvpc.hardening.consensus import EngineBallot, multi_engine_vote
from mvpc.hardening.crypto_integrity import generate_ed25519_keypair, sign_manifest
from mvpc.hardening.quotas import ResourceQuota
from mvpc.hardening.repair_loop import RepairLoop
from mvpc.hardening.transitive_scan import transitive_axiom_scan
from mvpc.kernel_backends import run_kernel
from mvpc.nexus_pipeline import SovereignNexusPipeline
from mvpc.phys.interval_guards import audit_cps_interval_and_rates
from mvpc.trust_verdicts import TrustVerdict


class HardenedSovereignPipeline:
    def __init__(self, *, sign: bool = True, max_repair: int = 2) -> None:
        self.base = SovereignNexusPipeline()
        self.sign = sign
        self.keypair = generate_ed25519_keypair() if sign else None
        self.repair = RepairLoop(max_depth=max_repair)
        self.quota = ResourceQuota(timeout_seconds=60.0)

    def run(
        self,
        raw_claim_json: Dict[str, Any],
        *,
        trajectory_data: Optional[Tuple[list, list, list]] = None,
        cas_polynomials: Optional[Tuple[str, list, str]] = None,
        consensus_backends: Sequence[str] = ("lean4", "dafny"),
        enable_repair: bool = True,
        noise_frac: float = 0.05,
    ) -> Dict[str, Any]:
        code = str(raw_claim_json.get("formal_code", "") or "")
        backend = str(raw_claim_json.get("target_backend", "lean4"))

        repair_out = None
        if enable_repair and code:
            repair_out = self.repair.run(code)
            if repair_out.success:
                code = repair_out.final_source
                raw_claim_json = {**raw_claim_json, "formal_code": code}

        tscan = transitive_axiom_scan(code)
        base_result = self.base.run_pipeline(
            raw_claim_json,
            trajectory_data=trajectory_data,
            cas_polynomials=cas_polynomials,
        )
        kern = run_kernel(backend, code, timeout=self.quota.timeout_seconds)

        def ballot_for(eng: str) -> EngineBallot:
            kr = run_kernel(eng, code, timeout=min(30.0, self.quota.timeout_seconds))
            return EngineBallot(
                engine=eng,
                trust_verdict=kr.trust_verdict,
                pass_=kr.ok,
                detail=kr.detail,
            )

        engines = {b: (lambda p, e=b: ballot_for(e)) for b in consensus_backends}
        consensus = multi_engine_vote(raw_claim_json, engines)

        cas_res = None
        if cas_polynomials:
            t, gens, vs = cas_polynomials
            cas_res = cas_verify_with_fallback(t, list(gens), vs).to_dict()

        interval_res = None
        if trajectory_data:
            ts, vel, temp = trajectory_data
            prof = raw_claim_json.get("physical_realization_profile") or {}
            interval_res = audit_cps_interval_and_rates(
                ts,
                vel,
                temp,
                max_velocity=float(prof.get("max_allowable_velocity", 100.0)),
                max_temperature=float(prof.get("max_allowable_temperature", 350.0)),
                noise_frac=noise_frac,
            ).to_dict()

        final_verdict = base_result.get("trust_verdict", TrustVerdict.INCONCLUSIVE.value)
        if kern.driver_mode == "kernel" and kern.ok:
            final_verdict = TrustVerdict.FORMALLY_CHECKED.value
        elif consensus.agreed and consensus.consensus_verdict == TrustVerdict.FORMALLY_CHECKED.value:
            final_verdict = TrustVerdict.FORMALLY_CHECKED.value
        elif not tscan.clean:
            final_verdict = TrustVerdict.EVIDENCE_SUPPORTED.value
        if interval_res and not interval_res.get("ok", True):
            final_verdict = TrustVerdict.REJECTED.value

        overall = (
            final_verdict
            in {
                TrustVerdict.FORMALLY_CHECKED.value,
                TrustVerdict.COMPUTATION_VERIFIED.value,
                TrustVerdict.EVIDENCE_SUPPORTED.value,
            }
            and tscan.clean
            and (interval_res is None or interval_res.get("ok", True))
        )
        if not base_result.get("safe_verify_audit", {}).get("passed", False):
            overall = False

        manifest = dict(base_result.get("immutable_evidence_manifest") or {})
        manifest.update(
            {
                "trust_verdict": final_verdict,
                "kernel": kern.to_dict(),
                "consensus": consensus.to_dict(),
                "cas_doublecheck": cas_res,
                "cps_interval": interval_res,
                "transitive_scan_clean": tscan.clean,
                "repair": repair_out.to_dict() if repair_out else None,
            }
        )
        if self.sign and self.keypair:
            manifest = sign_manifest(manifest, self.keypair)

        return {
            "overall_status": "PASSED" if overall else "FAILED",
            "trust_verdict": final_verdict,
            "base": base_result,
            "kernel": kern.to_dict(),
            "consensus": consensus.to_dict(),
            "cas_doublecheck": cas_res,
            "cps_interval": interval_res,
            "transitive_scan": tscan.to_dict(),
            "repair": repair_out.to_dict() if repair_out else None,
            "signed_manifest": manifest,
            "note": (
                "FORMALLY_CHECKED only when a real kernel returns success "
                "and SafeVerify is clean."
            ),
        }
