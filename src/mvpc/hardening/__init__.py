"""Hardening layers for MVPC Sovereign Nexus."""

from mvpc.hardening.cas_doublecheck import cas_verify_with_fallback
from mvpc.hardening.consensus import ConsensusResult, multi_engine_vote
from mvpc.hardening.crypto_integrity import (
    KeyPair,
    MerkleTree,
    generate_ed25519_keypair,
    hmac_sign,
    hmac_verify,
    sign_manifest,
    verify_manifest_signature,
)
from mvpc.hardening.quotas import ResourceQuota, enforce_quota_timeout
from mvpc.hardening.repair_loop import RepairLoop, RepairOutcome
from mvpc.hardening.transitive_scan import transitive_axiom_scan

__all__ = [
    "ConsensusResult",
    "KeyPair",
    "MerkleTree",
    "RepairLoop",
    "RepairOutcome",
    "ResourceQuota",
    "cas_verify_with_fallback",
    "enforce_quota_timeout",
    "generate_ed25519_keypair",
    "hmac_sign",
    "hmac_verify",
    "multi_engine_vote",
    "sign_manifest",
    "transitive_axiom_scan",
    "verify_manifest_signature",
]
