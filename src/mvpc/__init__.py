"""MVPC-X — Sovereign Claim-Verification Infrastructure & Reproducible Epistemic Engine."""

from mvpc.version import __version__  # single source of truth

from mvpc.claim import Claim, create_claim
from mvpc.evidence import Evidence, EvidenceType
from mvpc.trust import AttestationState, Finding, Severity, CoverageReport
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
