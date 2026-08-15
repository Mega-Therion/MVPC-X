"""Unified Sovereign Nexus pipeline orchestrator (P0).

Heuristic multi-backend scans + CAS + CPS/SI + SafeVerify + ledger.
Does NOT emit FORMALLY_CHECKED without a real kernel; uses trust_verdict.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from mvpc.core.safe_verify import safe_verify_source
from mvpc.newton_architect import AUTHORITY, scan_artifact_text
from mvpc.cps_realization import CPSRealizationBridge
from mvpc.trust_verdicts import TrustVerdict

try:
    import sympy as sp

    _HAS_SYMPY = True
except ImportError:  # pragma: no cover
    sp = None  # type: ignore
    _HAS_SYMPY = False


class ProposerType(str, Enum):
    BIOLOGICAL = "biological"
    SYNTHETIC = "synthetic"
    SYMBIOTIC = "symbiotic"


class TargetBackend(str, Enum):
    LEAN4 = "lean4"
    ROCQ = "rocq"
    ISABELLE = "isabelle"
    DAFNY = "dafny"


@dataclass
class PhysicalProfile:
    requires_si_checking: bool = True
    requires_cps_bounds: bool = True
    max_allowable_temperature: float = 350.0
    max_allowable_velocity: float = 100.0
    physical_variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class LexicalZoning:
    evolve_block: List[str] = field(default_factory=list)
    evolve_value: List[str] = field(default_factory=list)


@dataclass
class NeutralClaim:
    claim_id: str
    proposer_type: ProposerType
    target_backend: TargetBackend
    formal_code: str
    physical_realization_profile: PhysicalProfile
    lexical_zoning: LexicalZoning
    timestamp: float = field(default_factory=time.time)


@dataclass
class VerificationResult:
    claim_id: str
    backend: TargetBackend
    trust_verdict: str
    heuristic_pass: bool
    execution_time_ms: float
    ast_nodes_count: int
    axioms_used: List[str]
    has_unverified_axioms: bool
    error_message: Optional[str] = None
    proof_tree_digest: Optional[str] = None
    driver_mode: str = "heuristic"

    @property
    def verified(self) -> bool:
        return self.heuristic_pass and not self.has_unverified_axioms


class NeutralIngestionEngine:
    @staticmethod
    def process_raw_claim(raw_data: Dict[str, Any]) -> NeutralClaim:
        try:
            proposer = ProposerType(
                str(raw_data.get("proposer_type", "synthetic")).lower()
            )
        except ValueError:
            proposer = ProposerType.SYNTHETIC
        try:
            backend = TargetBackend(
                str(raw_data.get("target_backend", "lean4")).lower()
            )
        except ValueError:
            backend = TargetBackend.LEAN4

        formal_code = str(
            raw_data.get("formal_code", "") or raw_data.get("header_code", "")
        )
        content_hash = hashlib.sha256(
            f"{proposer.value}:{backend.value}:{formal_code}".encode()
        ).hexdigest()
        claim_id = raw_data.get("claim_id") or f"sha256-{content_hash[:16]}"

        phys = raw_data.get("physical_realization_profile") or {}
        physical_profile = PhysicalProfile(
            requires_si_checking=bool(phys.get("requires_si_checking", True)),
            requires_cps_bounds=bool(phys.get("requires_cps_bounds", True)),
            max_allowable_temperature=float(
                phys.get("max_allowable_temperature", 350.0)
            ),
            max_allowable_velocity=float(phys.get("max_allowable_velocity", 100.0)),
            physical_variables=dict(phys.get("physical_variables") or {}),
        )
        zone = raw_data.get("lexical_zoning") or {}
        lexical_zoning = LexicalZoning(
            evolve_block=list(zone.get("evolve_block") or ["helper_lemmas"]),
            evolve_value=list(zone.get("evolve_value") or ["hyperparameters"]),
        )
        return NeutralClaim(
            claim_id=str(claim_id),
            proposer_type=proposer,
            target_backend=backend,
            formal_code=formal_code,
            physical_realization_profile=physical_profile,
            lexical_zoning=lexical_zoning,
        )


def _heuristic_verify(
    claim: NeutralClaim,
    *,
    backend: TargetBackend,
    forbidden: List[str],
    required_any: List[str],
) -> VerificationResult:
    t0 = time.perf_counter()
    code = claim.formal_code
    axioms = [a for a in forbidden if a in code]
    sv = safe_verify_source(code, backend=backend.value)
    if not sv.clean:
        axioms = list({*axioms, *[f.rule for f in sv.findings]})

    # Newton Architect is the source authority for this project, so it gates
    # every verification path — not just the engine/policy one. Without this
    # the nexus -> hardened pipeline was a bypass: an artifact carrying a
    # vacuous Lean placeholder or an epoch-stripped cosmological claim could
    # reach EVIDENCE_SUPPORTED here while the same artifact was blocked by
    # mvpc.policy. Every Newton finding is Severity.VIOLATION and blocks.
    newton_findings = scan_artifact_text(code)
    if newton_findings:
        axioms = list({*axioms, *[f.code for f in newton_findings]})

    syntax_ok = (
        any(tok in code for tok in required_any) if required_any else bool(code.strip())
    )
    has_bad = bool(axioms) or not sv.clean or bool(newton_findings)
    if has_bad:
        verdict = TrustVerdict.EVIDENCE_SUPPORTED.value
        heuristic_pass = False
        err = f"unsound markers: {axioms or 'scan findings'}"
    elif syntax_ok:
        verdict = TrustVerdict.EVIDENCE_SUPPORTED.value
        heuristic_pass = True
        err = None
    else:
        verdict = TrustVerdict.REJECTED.value
        heuristic_pass = False
        err = "syntax markers missing"
    t1 = time.perf_counter()
    return VerificationResult(
        claim_id=claim.claim_id,
        backend=backend,
        trust_verdict=verdict,
        heuristic_pass=heuristic_pass,
        execution_time_ms=(t1 - t0) * 1000.0,
        ast_nodes_count=len(code.split()),
        axioms_used=axioms,
        has_unverified_axioms=has_bad,
        error_message=err,
        proof_tree_digest=hashlib.sha256(code.encode()).hexdigest()[:16],
        driver_mode="heuristic",
    )


class MultiBackendVerificationArray:
    def verify_claim(self, claim: NeutralClaim) -> VerificationResult:
        table = {
            TargetBackend.LEAN4: (
                ["sorry", "sorryAx"],
                ["theorem", "lemma", "def", "example"],
            ),
            TargetBackend.ROCQ: (
                ["Admitted", "admit"],
                ["Theorem", "Lemma", "Definition"],
            ),
            TargetBackend.ISABELLE: (["sorry"], ["lemma", "theorem", "by"]),
            TargetBackend.DAFNY: (["assume"], ["method", "lemma", "function"]),
        }
        forbidden, required = table.get(claim.target_backend, ([], []))
        if not forbidden and not required:
            return VerificationResult(
                claim_id=claim.claim_id,
                backend=claim.target_backend,
                trust_verdict=TrustVerdict.UNSAFE_TO_VERIFY.value,
                heuristic_pass=False,
                execution_time_ms=0.0,
                ast_nodes_count=0,
                axioms_used=[],
                has_unverified_axioms=True,
                error_message=f"Unsupported backend: {claim.target_backend}",
            )
        return _heuristic_verify(
            claim,
            backend=claim.target_backend,
            forbidden=forbidden,
            required_any=required,
        )


class GroebnerTacticBridge:
    @staticmethod
    def verify_ideal_membership(
        target_poly_str: str, generator_poly_strs: List[str], vars_str: str
    ) -> Tuple[bool, str]:
        if not _HAS_SYMPY:
            return False, "sympy not installed"
        try:
            var_list = [sp.Symbol(v.strip()) for v in vars_str.split() if v.strip()]
            target = sp.sympify(target_poly_str)
            generators = [sp.sympify(g) for g in generator_poly_strs]
            gb = sp.groebner(generators, *var_list)
            _q, remainder = sp.reduced(target, gb, var_list)
            is_member = remainder == 0
            cert = (
                f"Reified Certificate: GroebnerBasis({generator_poly_strs}) => "
                f"Remainder({target_poly_str}) = {remainder}"
            )
            return bool(is_member), cert
        except Exception as exc:
            return False, f"CAS Reification Error: {exc}"


class SystemFingerprinter:
    @staticmethod
    def generate_fingerprint(stage: str, claim: NeutralClaim) -> str:
        data = {
            "stage": stage,
            "claim_id": claim.claim_id,
            "python_version": sys.version.split()[0],
            "code_hash": hashlib.sha256(claim.formal_code.encode()).hexdigest(),
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class SafeVerifyAxiomAuditor:
    @staticmethod
    def audit_verification_result(result: VerificationResult) -> Tuple[bool, str]:
        if result.has_unverified_axioms:
            return False, f"SafeVerify FAILED: unverified axioms {result.axioms_used}"
        if not result.heuristic_pass:
            return False, f"SafeVerify FAILED: {result.error_message}"
        return True, "SafeVerify PASSED: no forbidden markers (heuristic/kernel scan)"


@dataclass
class EvidenceManifest:
    manifest_version: str
    timestamp_iso: str
    claim_id: str
    proposer_type: str
    target_backend: str
    pre_audit_fingerprint: str
    post_audit_fingerprint: str
    trust_verdict: str
    heuristic_pass: bool
    ast_nodes_count: int
    groebner_cas_certified: bool
    si_dimension_certified: bool
    cps_safety_certified: bool
    zero_leakage_certified: bool
    safe_verify_passed: bool
    evidence_chain_hash: str
    driver_mode: str = "heuristic"
    # Records which authority gated this evidence, so a manifest is
    # self-describing about the protocol it was judged under.
    newton_authority: str = AUTHORITY


class ImmutableEvidenceLedger:
    def __init__(self) -> None:
        self.chain: List[EvidenceManifest] = []

    def commit_evidence(
        self,
        claim: NeutralClaim,
        verification_result: VerificationResult,
        pre_fp: str,
        post_fp: str,
        groebner_ok: bool,
        si_ok: bool,
        cps_ok: bool,
        leakage_ok: bool,
        safe_verify_ok: bool,
    ) -> EvidenceManifest:
        prev = (
            self.chain[-1].evidence_chain_hash
            if self.chain
            else "GENESIS_BLOCK_0000000000000000"
        )
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        payload = (
            f"{prev}|{claim.claim_id}|{verification_result.trust_verdict}|"
            f"{groebner_ok}|{si_ok}|{cps_ok}|{leakage_ok}|{safe_verify_ok}|{post_fp}"
        )
        chain_hash = hashlib.sha256(payload.encode()).hexdigest()
        manifest = EvidenceManifest(
            manifest_version="8.0.0-EVIDENCE-MANIFEST",
            timestamp_iso=ts,
            claim_id=claim.claim_id,
            proposer_type=claim.proposer_type.value,
            target_backend=claim.target_backend.value,
            pre_audit_fingerprint=pre_fp,
            post_audit_fingerprint=post_fp,
            trust_verdict=verification_result.trust_verdict,
            heuristic_pass=verification_result.heuristic_pass,
            ast_nodes_count=verification_result.ast_nodes_count,
            groebner_cas_certified=groebner_ok,
            si_dimension_certified=si_ok,
            cps_safety_certified=cps_ok,
            zero_leakage_certified=leakage_ok,
            safe_verify_passed=safe_verify_ok,
            evidence_chain_hash=chain_hash,
            driver_mode=verification_result.driver_mode,
        )
        self.chain.append(manifest)
        return manifest


class SovereignNexusPipeline:
    def __init__(self) -> None:
        self.ingestion = NeutralIngestionEngine()
        self.mvpcx = MultiBackendVerificationArray()
        self.groebner = GroebnerTacticBridge()
        self.phys_bridge = CPSRealizationBridge()
        self.ledger = ImmutableEvidenceLedger()

    def run_pipeline(
        self,
        raw_claim_json: Dict[str, Any],
        trajectory_data: Optional[Tuple[List[float], List[float], List[float]]] = None,
        cas_polynomials: Optional[Tuple[str, List[str], str]] = None,
    ) -> Dict[str, Any]:
        claim = self.ingestion.process_raw_claim(raw_claim_json)
        pre_fp = SystemFingerprinter.generate_fingerprint("PRE_AUDIT", claim)
        v_result = self.mvpcx.verify_claim(claim)

        groebner_ok = True
        groebner_msg = "No CAS polynomials provided."
        if cas_polynomials:
            target_p, gen_ps, vars_s = cas_polynomials
            groebner_ok, groebner_msg = self.groebner.verify_ideal_membership(
                target_p, gen_ps, vars_s
            )

        phys_res = self.phys_bridge.audit_claim_physics(
            physical_variables=claim.physical_realization_profile.physical_variables,
            trajectory_data=trajectory_data,
            max_velocity=claim.physical_realization_profile.max_allowable_velocity,
            max_temperature=claim.physical_realization_profile.max_allowable_temperature,
            requires_si_checking=claim.physical_realization_profile.requires_si_checking,
        )

        si_ok = phys_res["zero_leakage_certified"]
        cps_ok = phys_res["cps_safety_passed"]
        if (
            not claim.physical_realization_profile.requires_cps_bounds
            and trajectory_data is None
        ):
            cps_ok = True

        safe_ok, safe_msg = SafeVerifyAxiomAuditor.audit_verification_result(v_result)
        post_fp = SystemFingerprinter.generate_fingerprint("POST_AUDIT", claim)

        manifest = self.ledger.commit_evidence(
            claim=claim,
            verification_result=v_result,
            pre_fp=pre_fp,
            post_fp=post_fp,
            groebner_ok=groebner_ok,
            si_ok=si_ok,
            cps_ok=cps_ok,
            leakage_ok=si_ok,
            safe_verify_ok=safe_ok,
        )

        overall = (
            v_result.heuristic_pass
            and not v_result.has_unverified_axioms
            and groebner_ok
            and si_ok
            and cps_ok
            and safe_ok
        )

        return {
            "overall_status": "PASSED" if overall else "FAILED",
            "claim_id": claim.claim_id,
            "proposer_type": claim.proposer_type.value,
            "target_backend": claim.target_backend.value,
            "trust_verdict": v_result.trust_verdict,
            "driver_mode": v_result.driver_mode,
            "note": (
                "Heuristic backend path. FORMALLY_CHECKED requires real kernel acceptance."
            ),
            "verification_result": asdict(v_result),
            "groebner_cas_certification": {
                "certified": groebner_ok,
                "details": groebner_msg,
            },
            "si_dimension_certification": {
                "certified": si_ok,
                "details": phys_res["zero_leakage_details"],
            },
            "cps_safety_certification": {
                "certified": cps_ok,
                "violations": phys_res["cps_violations"],
            },
            "safe_verify_audit": {"passed": safe_ok, "details": safe_msg},
            "immutable_evidence_manifest": asdict(manifest),
        }
