"""MVPC-X — Sovereign Claim-Verification Infrastructure & Reproducible Epistemic Engine."""

from mvpc.version import __version__

from mvpc.claim import Claim, create_claim
from mvpc.evidence import Evidence, EvidenceType
from mvpc.trust import AttestationState, Finding, Severity, CoverageReport
from mvpc.trust_verdicts import TrustVerdict
from mvpc.assurance import AssuranceLevel, VerificationEvidence, derive_assurance
from mvpc.verification_plan import CheckKind, VerificationPlan, VerificationTarget
from mvpc.provenance import Provenance, SourceType, AIProvenance
from mvpc.policy import PolicyLevel, Policy, get_policy, evaluate_attestation
from mvpc.witness import Witness, generate_witness
from mvpc.explanations import get_explanation
from mvpc.security import compute_system_fingerprint, IntegritySession
from mvpc.preflight import run_preflight

__all__ = [
    "__version__",
    "Claim",
    "create_claim",
    "Evidence",
    "EvidenceType",
    "AttestationState",
    "TrustVerdict",
    "AssuranceLevel",
    "VerificationEvidence",
    "derive_assurance",
    "CheckKind",
    "VerificationPlan",
    "VerificationTarget",
    "Finding",
    "Severity",
    "CoverageReport",
    "Provenance",
    "SourceType",
    "AIProvenance",
    "PolicyLevel",
    "Policy",
    "get_policy",
    "evaluate_attestation",
    "Witness",
    "generate_witness",
    "get_explanation",
    "compute_system_fingerprint",
    "IntegritySession",
    "run_preflight",
]
