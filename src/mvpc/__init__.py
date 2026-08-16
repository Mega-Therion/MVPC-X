"""MVPC-X — Sovereign claim-verification infrastructure and evidence protocol."""

from mvpc.version import __version__
from mvpc.claim import Claim, create_claim
from mvpc.claim_binding import ClaimBinding, SemanticTest, bind_claim_to_formal_proof
from mvpc.evidence import Evidence, EvidenceType
from mvpc.trust import AttestationState, Finding, Severity, CoverageReport
from mvpc.trust_verdicts import TrustVerdict
from mvpc.assurance import AssuranceLevel, VerificationEvidence, derive_assurance
from mvpc.formalization import FormalizationReview, build_formalization_review
from mvpc.verification_plan import CheckKind, VerificationPlan, VerificationTarget, VerificationResult
from mvpc.verification_fabric import VerificationFabric
from mvpc.backend_adapter import register_default_backends
from mvpc.proof_record import ProofRecord
from mvpc.witness_seal import generate_signing_keypair, seal_payload, verify_sealed_payload
from mvpc.provenance import Provenance, SourceType, AIProvenance
from mvpc.policy import PolicyLevel, Policy, get_policy, evaluate_attestation
from mvpc.witness import Witness, generate_witness
from mvpc.explanations import get_explanation
from mvpc.security import compute_system_fingerprint, IntegritySession
from mvpc.preflight import run_preflight

__all__ = [
    "__version__", "Claim", "create_claim", "ClaimBinding", "SemanticTest",
    "bind_claim_to_formal_proof", "Evidence", "EvidenceType", "AttestationState",
    "TrustVerdict", "AssuranceLevel", "VerificationEvidence", "derive_assurance",
    "FormalizationReview", "build_formalization_review", "CheckKind", "VerificationPlan",
    "VerificationTarget", "VerificationResult", "VerificationFabric", "register_default_backends",
    "ProofRecord", "generate_signing_keypair", "seal_payload", "verify_sealed_payload", "Finding",
    "Severity", "CoverageReport", "Provenance", "SourceType", "AIProvenance", "PolicyLevel",
    "Policy", "get_policy", "evaluate_attestation", "Witness", "generate_witness", "get_explanation",
    "compute_system_fingerprint", "IntegritySession", "run_preflight",
]
