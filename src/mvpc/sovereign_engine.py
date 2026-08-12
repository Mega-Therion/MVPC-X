"""MVPC-X Sovereign Nexus Engine — integrated runtime (spec v2.0 ULTRA-GOLD).

Core axiom:
  AI proposes. Machines verify. Humans audit. Physical evidence persists.

This module integrates the master orchestrator pattern with the trust
foundation (verdict taxonomy, SafeVerify, fingerprint, ledger).

IMPORTANT: lightweight backend drivers perform *syntax/heuristic* scans
unless a real kernel is installed. They must not be rendered as
FORMALLY_CHECKED without an actual checker acceptance.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from mvpc.core.safe_verify import safe_verify_source
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
        mapping = [
            ("M", self.mass),
            ("L", self.length),
            ("T", self.time),
            ("I", self.current),
            ("Theta", self.temperature),
            ("N", self.amount),
            ("J", self.luminous),
        ]
        for name, val in mapping:
            if abs(val) > 1e-12:
                units.append(f"[{name}]^{val:g}")
        return " ".join(units) if units else "[Dimensionless]"


SI_DIMENSIONS: Dict[str, SIDimension] = {
    "dimensionless": SIDimension(),
    "mass": SIDimension(mass=1.0),
    "length": SIDimension(length=1.0),
    "time": SIDimension(time=1.0),
    "current": SIDimension(current=1.0),
    "temperature": SIDimension(temperature=1.0),
    "velocity": SIDimension(length=1.0, time=-1.0),
    "acceleration": SIDimension(length=1.0, time=-2.0),
    "force": SIDimension(mass=1.0, length=1.0, time=-2.0),
    "energy": SIDimension(mass=1.0, length=2.0, time=-2.0),
    "power": SIDimension(mass=1.0, length=2.0, time=-3.0),
    "pressure": SIDimension(mass=1.0, length=-1.0, time=-2.0),
}


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
        return self.trust_verdict in {
            TrustVerdict.FORMALLY_CHECKED.value,
            TrustVerdict.COMPUTATION_VERIFIED.value,
            TrustVerdict.EVIDENCE_SUPPORTED.value,
        } and not self.has_unverified_axioms


class NeutralIngestionEngine:
    @staticmethod
    def process_raw_claim(raw_data: Dict[str, Any]) -> NeutralClaim:
        try:
            proposer = ProposerType(str(raw_data.get("proposer_type", "synthetic")).lower())
        except ValueError:
            proposer = ProposerType.SYNTHETIC
        try:
            backend = TargetBackend(str(raw_data.get("target_backend", "lean4")).lower())
        except ValueError:
            backend = TargetBackend.LEAN4

        formal_code = str(raw_data.get("formal_code", "") or raw_data.get("header_code", ""))
        content_hash = hashlib.sha256(
            f"{proposer.value}:{backend.value}:{formal_code}".encode()
        ).hexdigest()
        claim_id = raw_data.get("claim_id") or f"sha256-{content_hash[:16]}"

        phys = raw_data.get("physical_realization_profile") or {}
        physical_profile = PhysicalProfile(
            requires_si_checking=bool(phys.get("requires_si_checking", True)),
            requires_cps_bounds=bool(phys.get("requires_cps_bounds", True)),
            max_allowable_temperature=float(phys.get("max_allowable_temperature", 350.0)),
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


class AbstractBackendDriver:
    def verify(self, claim: NeutralClaim) -> VerificationResult:
        raise NotImplementedError


def _scan_result(
    claim: NeutralClaim,
    *,
    backend: TargetBackend,
    forbidden: List[str],
    required_any: List[str],
    t0: float,
) -> VerificationResult:
    code = claim.formal_code
    axioms = [a for a in forbidden if a in code]
    sv = safe_verify_source(code, backend=backend.value)
    if not sv.clean:
        axioms = list({*axioms, *[f.rule for f in sv.findings]})

    syntax_ok = any(tok in code for tok in required_any) if required_any else bool(code.strip())
    has_bad = bool(axioms) or not sv.clean

    if has_bad:
        verdict = TrustVerdict.EVIDENCE_SUPPORTED.value
        if any(a in {"sorry", "sorryAx", "admit", "Admitted", "assume"} for a in axioms):
            verdict = TrustVerdict.EVIDENCE_SUPPORTED.value
        else:
            verdict = TrustVerdict.INCONCLUSIVE.value
        heuristic_pass = False
        err = f"unsound markers or weak syntax: {axioms or 'scan findings'}"
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


class Lean4BackendDriver(AbstractBackendDriver):
    def verify(self, claim: NeutralClaim) -> VerificationResult:
        return _scan_result(
            claim,
            backend=TargetBackend.LEAN4,
            forbidden=["sorry", "sorryAx"],
            required_any=["theorem", "lemma", "def", "example"],
            t0=time.perf_counter(),
        )


class RocqBackendDriver(AbstractBackendDriver):
    def verify(self, claim: NeutralClaim) -> VerificationResult:
        return _scan_result(
            claim,
            backend=TargetBackend.ROCQ,
            forbidden=["Admitted", "admit"],
            required_any=["Theorem", "Lemma", "Definition"],
            t0=time.perf_counter(),
        )


class IsabelleBackendDriver(AbstractBackendDriver):
    def verify(self, claim: NeutralClaim) -> VerificationResult:
        return _scan_result(
            claim,
            backend=TargetBackend.ISABELLE,
            forbidden=["sorry"],
            required_any=["lemma", "theorem", "by"],
            t0=time.perf_counter(),
        )


class DafnyBackendDriver(AbstractBackendDriver):
    def verify(self, claim: NeutralClaim) -> VerificationResult:
        return _scan_result(
            claim,
            backend=TargetBackend.DAFNY,
            forbidden=["assume"],
            required_any=["method", "lemma", "function"],
            t0=time.perf_counter(),
        )


class MultiBackendVerificationArray:
    def __init__(self) -> None:
        self.drivers: Dict[TargetBackend, AbstractBackendDriver] = {
            TargetBackend.LEAN4: Lean4BackendDriver(),
            TargetBackend.ROCQ: RocqBackendDriver(),
            TargetBackend.ISABELLE: IsabelleBackendDriver(),
            TargetBackend.DAFNY: DafnyBackendDriver(),
        }

    def verify_claim(self, claim: NeutralClaim) -> VerificationResult:
        driver = self.drivers.get(claim.target_backend)
        if not driver:
            return VerificationResult(
                claim_id=claim.claim_id,
                backend=claim.target_backend,
                trust_verdict=TrustVerdict.UNSAFE_TO_VERIFY.value,
                heuristic_pass=False,
                execution_time_ms=0.0,
                ast_nodes_count=0,
                axioms_used=[],
                has_unverified_axioms=True,
                error_message=f"unsupported backend: {claim.target_backend}",
            )
        return driver.verify(claim)


@dataclass
class ProofStateNode:
    state_id: str
    goal_statement: str
    parent_id: Optional[str] = None
    visit_count: int = 0
    value_score: float = 0.0
    prior_prob: float = 1.0
    children_ids: List[str] = field(default_factory=list)


class CryptographicGoalCache:
    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}

    def compute_hash(self, goal_statement: str, hypotheses: List[str]) -> str:
        raw = f"{goal_statement}|" + "|".join(sorted(hypotheses))
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, goal_hash: str) -> Any:
        return self._cache.get(goal_hash)

    def put(self, goal_hash: str, result: Any) -> None:
        self._cache[goal_hash] = result


class PUCBSearchController:
    def __init__(self, c_exploration: float = 1.414) -> None:
        self.c_exploration = c_exploration
        self.nodes: Dict[str, ProofStateNode] = {}
        self.goal_cache = CryptographicGoalCache()

    def add_node(self, node: ProofStateNode) -> None:
        self.nodes[node.state_id] = node

    def compute_p_ucb_score(self, node_id: str) -> float:
        node = self.nodes[node_id]
        if not node.parent_id or node.parent_id not in self.nodes:
            n_parent = max(1, node.visit_count)
        else:
            n_parent = max(1, self.nodes[node.parent_id].visit_count)
        return node.value_score + self.c_exploration * node.prior_prob * (
            math.sqrt(n_parent) / (1.0 + node.visit_count)
        )

    def select_best_candidate(self, candidate_ids: List[str]) -> str:
        best_id = candidate_ids[0]
        best_score = -float("inf")
        for cid in candidate_ids:
            score = self.compute_p_ucb_score(cid)
            if score > best_score:
                best_score = score
                best_id = cid
        return best_id


class GroebnerTacticBridge:
    @staticmethod
    def verify_ideal_membership(
        target_poly_str: str,
        generator_poly_strs: List[str],
        vars_str: str,
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
            cert = f"GroebnerBasis({generator_poly_strs}) => Remainder({target_poly_str}) = {remainder}"
            return bool(is_member), cert
        except Exception as exc:
            return False, f"CAS error: {exc}"


class SIDimensionChecker:
    def __init__(self) -> None:
        self.registry: Dict[str, SIDimension] = dict(SI_DIMENSIONS)

    def register_variable(self, name: str, dim: SIDimension) -> None:
        self.registry[name] = dim

    def infer_and_verify_formula(
        self, lhs_name: str, rhs_terms: List[Tuple[str, float]]
    ) -> Tuple[bool, str]:
        lhs_dim = self.registry.get(lhs_name)
        if not lhs_dim:
            return False, f"unknown LHS: {lhs_name}"
        computed = SIDimension()
        for var_name, exp in rhs_terms:
            dim = self.registry.get(var_name)
            if not dim:
                return False, f"unknown RHS: {var_name}"
            computed = computed.multiply(dim.power(exp))
        match = lhs_dim.is_equal(computed)
        return match, f"LHS [{lhs_name}: {lhs_dim.to_string()}] vs RHS [{computed.to_string()}] => {match}"


class CPSSafetyAuditor:
    @staticmethod
    def audit_hybrid_trajectory(
        time_steps: List[float],
        velocity_profile: List[float],
        temperature_profile: List[float],
        profile: PhysicalProfile,
    ) -> Tuple[bool, List[str]]:
        violations: List[str] = []
        if not profile.requires_cps_bounds:
            return True, []
        for t, v, temp in zip(time_steps, velocity_profile, temperature_profile):
            if v > profile.max_allowable_velocity:
                violations.append(f"velocity at t={t:g}: {v:g} > {profile.max_allowable_velocity:g}")
            if temp > profile.max_allowable_temperature:
                violations.append(f"temperature at t={t:g}: {temp:g} > {profile.max_allowable_temperature:g}")
        return len(violations) == 0, violations


class ZeroLeakageCertifier:
    @staticmethod
    def verify_physical_realization(
        claim: NeutralClaim, si_checker: SIDimensionChecker
    ) -> Tuple[bool, str]:
        if not claim.physical_realization_profile.requires_si_checking:
            return True, "SI checking not required"
        unregistered = []
        for var_name, dim_type in claim.physical_realization_profile.physical_variables.items():
            if dim_type not in si_checker.registry and var_name not in si_checker.registry:
                unregistered.append(var_name)
        if unregistered:
            return False, f"unregistered physical variables: {unregistered}"
        return True, "zero physical leakage record: all quantities mapped to SI registry"


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


class LexicalZoneVerifier:
    @staticmethod
    def verify_edits(
        claim: NeutralClaim, edited_blocks: List[str], edited_params: List[str]
    ) -> Tuple[bool, str]:
        allowed_b = set(claim.lexical_zoning.evolve_block)
        allowed_p = set(claim.lexical_zoning.evolve_value)
        bad_b = [b for b in edited_blocks if b not in allowed_b]
        bad_p = [p for p in edited_params if p not in allowed_p]
        if bad_b or bad_p:
            return False, f"lexical zone violation blocks={bad_b} params={bad_p}"
        return True, "lexical zoning ok"


class SafeVerifyAxiomAuditor:
    @staticmethod
    def audit_verification_result(result: VerificationResult) -> Tuple[bool, str]:
        if result.has_unverified_axioms:
            return False, f"unverified axioms: {result.axioms_used}"
        if not result.heuristic_pass and result.trust_verdict == TrustVerdict.REJECTED.value:
            return False, result.error_message or "verification rejected"
        return True, "SafeVerify: no forbidden markers in heuristic/kernel scan"


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
        prev = self.chain[-1].evidence_chain_hash if self.chain else "GENESIS"
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        payload = (
            f"{prev}|{claim.claim_id}|{verification_result.trust_verdict}|"
            f"{groebner_ok}|{si_ok}|{cps_ok}|{leakage_ok}|{safe_verify_ok}|{post_fp}"
        )
        chain_hash = hashlib.sha256(payload.encode()).hexdigest()
        manifest = EvidenceManifest(
            manifest_version="2.0.0-ULTRA-GOLD-EVIDENCE",
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


class SovereignNexusEngine:
    def __init__(self) -> None:
        self.ingestion = NeutralIngestionEngine()
        self.mvpcx = MultiBackendVerificationArray()
        self.pucb = PUCBSearchController()
        self.groebner = GroebnerTacticBridge()
        self.si_checker = SIDimensionChecker()
        self.cps_auditor = CPSSafetyAuditor()
        self.leakage_certifier = ZeroLeakageCertifier()
        self.ledger = ImmutableEvidenceLedger()

        self.si_checker.register_variable("F", SI_DIMENSIONS["force"])
        self.si_checker.register_variable("m", SI_DIMENSIONS["mass"])
        self.si_checker.register_variable("a", SI_DIMENSIONS["acceleration"])
        self.si_checker.register_variable("v", SI_DIMENSIONS["velocity"])

    def process_and_verify(
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

        si_ok, si_msg = self.leakage_certifier.verify_physical_realization(claim, self.si_checker)

        cps_ok = True
        cps_violations: List[str] = []
        if trajectory_data:
            t_steps, v_prof, temp_prof = trajectory_data
            cps_ok, cps_violations = self.cps_auditor.audit_hybrid_trajectory(
                t_steps, v_prof, temp_prof, claim.physical_realization_profile
            )

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
                "Heuristic/backend scan path. FORMALLY_CHECKED requires a real "
                "kernel checker acceptance, not string heuristics."
            ),
            "verification_result": asdict(v_result),
            "groebner_cas_certification": {"certified": groebner_ok, "details": groebner_msg},
            "si_dimension_certification": {"certified": si_ok, "details": si_msg},
            "cps_safety_certification": {"certified": cps_ok, "violations": cps_violations},
            "safe_verify_audit": {"passed": safe_ok, "details": safe_msg},
            "immutable_evidence_manifest": asdict(manifest),
        }


def main() -> None:
    print("MVPC-X Sovereign Nexus Engine v2.0.0-ULTRA-GOLD")
    print("Axiom: AI proposes. Machines verify. Humans audit. Physical evidence persists.\n")
    engine = SovereignNexusEngine()

    sample = {
        "claim_id": "sha256-lean4-cps-001",
        "proposer_type": "symbiotic",
        "target_backend": "lean4",
        "formal_code": """
theorem physical_boundary_safety (m v : Real) (h_m : m > 0) (h_v : v <= 100) :
    (1/2) * m * v^2 <= 5000 * m := by
  sorry
""",
        "physical_realization_profile": {
            "requires_si_checking": True,
            "requires_cps_bounds": True,
            "max_allowable_temperature": 320.0,
            "max_allowable_velocity": 80.0,
            "physical_variables": {"m": "mass", "v": "velocity"},
        },
        "lexical_zoning": {
            "evolve_block": ["helper_lemmas"],
            "evolve_value": ["hyperparameters"],
        },
    }
    print("--> Test 1: sorry (expect SafeVerify fail)")
    r1 = engine.process_and_verify(
        sample,
        trajectory_data=([0.0, 1.0, 2.0], [10.0, 50.0, 75.0], [295.0, 305.0, 315.0]),
    )
    print("Status:", r1["overall_status"], "verdict:", r1["trust_verdict"])
    print("SafeVerify:", r1["safe_verify_audit"])

    valid = dict(sample)
    valid["claim_id"] = "sha256-lean4-cps-002-valid"
    valid["formal_code"] = """
theorem physical_boundary_safety (m v : Real) (h_m : m > 0) (h_v : v <= 100) :
    (1/2) * m * v^2 <= 5000 * m := by
  have h1 : v^2 <= 10000 := by nlinarith
  linarith
"""
    print("\n--> Test 2: no sorry + CAS + trajectory")
    r2 = engine.process_and_verify(
        valid,
        trajectory_data=([0.0, 1.0, 2.0], [10.0, 50.0, 75.0], [295.0, 305.0, 315.0]),
        cas_polynomials=("x**2 - y**2", ["x - y"], "x y"),
    )
    print("Status:", r2["overall_status"], "verdict:", r2["trust_verdict"])
    print("CAS:", r2["groebner_cas_certification"])
    print("CPS:", r2["cps_safety_certification"])
    print("Manifest:", r2["immutable_evidence_manifest"]["evidence_chain_hash"][:24], "...")


if __name__ == "__main__":
    main()
