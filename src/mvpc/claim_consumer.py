#!/usr/bin/env python3
"""
claim_consumer.py — MVPC-X Claim Consumer

Ingests a claim fixture bundle (JSON) produced by an external repository,
converts each claim into VerificationEvidence, runs derive_assurance(),
and emits machine-checked D0–D6 verdicts.

This is the judge. The external repo is the case.

Usage:
    python3 -m mvpc.claim_consumer --bundle path/to/fixture_bundle.json
    python3 -m mvpc.claim_consumer --bundle path/to/fixture_bundle.json --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .assurance import AssuranceLevel, VerificationEvidence, derive_assurance
from .trust_verdicts import TrustVerdict


def _map_verdict(status: str, tier: str) -> TrustVerdict:
    """Map a manifest's self-reported status to an MVPC-X TrustVerdict.

    The manifest's own status is NOT authoritative — it is the claim's
    self-description. The judge decides what assurance it actually earns.
    """
    s = status.upper()
    t = tier.upper()
    if "SUSPEND" in s or t == "[O]":
        return TrustVerdict.INCONCLUSIVE
    if "VERIFIED" in s or t == "[P]":
        return TrustVerdict.FORMALLY_CHECKED
    if "OPEN" in s or "PARTIAL" in s:
        return TrustVerdict.INCONCLUSIVE
    return TrustVerdict.INCONCLUSIVE


def _build_evidence(claim: dict[str, Any]) -> list[VerificationEvidence]:
    """Convert one claim manifest into VerificationEvidence items.

    Only evidence that is actually present in the manifest is emitted.
    Missing hardening metadata means the claim cannot climb past D2.
    """
    claim_id = claim.get("claim_id", "UNKNOWN")
    proposition = claim.get("formal_proposition") or claim.get("statement", "")
    artifacts = claim.get("artifacts", [])
    verification = claim.get("verification", {})
    tier = claim.get("epistemic_tier", "[?]")
    status = claim.get("status", "UNKNOWN")

    evidence: list[VerificationEvidence] = []

    primary_artifact = artifacts[0] if artifacts else {}
    artifact_hash = primary_artifact.get("sha256", "unknown")
    source_id = verification.get("prover", "unspecified")

    if tier == "[P]" and verification.get("pass") is True:
        try:
            evidence.append(VerificationEvidence(
                claim_id=claim_id,
                proposition=proposition,
                source_id=source_id,
                kind="formal",
                verdict=TrustVerdict.FORMALLY_CHECKED,
                foundation=verification.get("mathlib_pin", "lean4"),
                artifact_hash=artifact_hash,
            ))
        except ValueError:
            evidence.append(VerificationEvidence(
                claim_id=claim_id,
                proposition=proposition,
                source_id=source_id,
                kind="computation",
                verdict=TrustVerdict.COMPUTATION_VERIFIED,
                artifact_hash=artifact_hash,
            ))
    elif tier == "[D]":
        evidence.append(VerificationEvidence(
            claim_id=claim_id,
            proposition=proposition,
            source_id=source_id,
            kind="computation",
            verdict=TrustVerdict.COMPUTATION_VERIFIED,
            artifact_hash=artifact_hash,
        ))
    else:
        evidence.append(VerificationEvidence(
            claim_id=claim_id,
            proposition=proposition,
            source_id=source_id,
            kind="proposal",
            verdict=TrustVerdict.INCONCLUSIVE,
            artifact_hash=artifact_hash,
        ))

    if verification.get("axiom_footprint"):
        evidence.append(VerificationEvidence(
            claim_id=claim_id,
            proposition=proposition,
            source_id="axiom-audit",
            kind="axiom_audit",
            verdict=TrustVerdict.EVIDENCE_SUPPORTED,
            artifact_hash=artifact_hash,
        ))

    if verification.get("gate_script"):
        evidence.append(VerificationEvidence(
            claim_id=claim_id,
            proposition=proposition,
            source_id="environment",
            kind="environment",
            verdict=TrustVerdict.EVIDENCE_SUPPORTED,
            artifact_hash=artifact_hash,
        ))

    return evidence


def judge_bundle(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Run derive_assurance() on every claim in a fixture bundle."""
    results = []
    for claim in bundle.get("claims", []):
        claim_id = claim.get("claim_id", "UNKNOWN")
        evidence = _build_evidence(claim)
        try:
            level = derive_assurance(evidence)
            error = None
        except Exception as exc:
            level = AssuranceLevel.D0_PROPOSED
            error = str(exc)

        results.append({
            "claim_id": claim_id,
            "manifest_tier": claim.get("epistemic_tier", "[?]"),
            "manifest_status": claim.get("status", "UNKNOWN"),
            "assurance_level": level.name,
            "assurance_value": int(level),
            "evidence_count": len(evidence),
            "error": error,
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="MVPC-X Claim Consumer — judge a fixture bundle")
    parser.add_argument("--bundle", required=True, help="Path to fixture bundle JSON")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of text")
    args = parser.parse_args()

    bundle_path = Path(args.bundle)
    if not bundle_path.exists():
        print(f"ERROR: bundle not found: {bundle_path}", file=sys.stderr)
        sys.exit(1)

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    results = judge_bundle(bundle)

    if args.json:
        print(json.dumps({"results": results}, indent=2))
    else:
        print("=" * 72)
        print("         MVPC-X CLAIM CONSUMER — JUDGE VERDICTS")
        print("=" * 72)
        print(f"Bundle source:    {bundle.get('source_repository', 'unknown')}")
        print(f"Claims judged:    {len(results)}")
        print("-" * 72)
        print(f"{'ID':<24} {'Manifest':<12} {'Assurance':<28} {'Ev#'}")
        print("-" * 72)
        for r in results:
            print(f"{r['claim_id']:<24} {r['manifest_tier']:<12} {r['assurance_level']:<28} {r['evidence_count']}")
        print("-" * 72)
        print("These are MVPC-X judge verdicts, not self-reported statuses.")
        print("=" * 72)


if __name__ == "__main__":
    main()
