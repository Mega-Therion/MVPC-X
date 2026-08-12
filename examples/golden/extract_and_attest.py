#!/usr/bin/env python3
"""Extract witness from claim JSON and seal human attestation (golden demo helper)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mvpc.witness import Witness


def main() -> int:
    p = argparse.ArgumentParser(description="Extract witness from claim JSON and attest")
    p.add_argument("claim_json", type=Path)
    p.add_argument("--signer", required=True)
    p.add_argument("--notes", default="")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output witness path (default: alongside claim as *_witness.json)",
    )
    p.add_argument("--reject", action="store_true")
    args = p.parse_args()

    data = json.loads(args.claim_json.read_text(encoding="utf-8"))
    witness_dict = (
        data.get("provenance", {})
        .get("metadata", {})
        .get("witness")
    )
    if not witness_dict:
        print("No provenance.metadata.witness in claim JSON", file=sys.stderr)
        return 1

    w = Witness(
        witness_id=witness_dict.get("witness_id", "W-UNKNOWN"),
        claim_id=witness_dict.get("claim_id", data.get("id", "C-UNKNOWN")),
        artifact_path=witness_dict.get("artifact_path", "unknown"),
        artifact_hash=witness_dict.get("artifact_hash", "unknown"),
        environment=witness_dict.get("environment", {}),
        policy=witness_dict.get("policy", {}),
        checks_performed=witness_dict.get("checks_performed", []),
        findings=witness_dict.get("findings", []),
        evidence=witness_dict.get("evidence", []),
        coverage=witness_dict.get("coverage", {}),
        attestation_state=witness_dict.get("attestation_state", "UNVERIFIED"),
        remediation=witness_dict.get("remediation"),
        human_review_obligations=witness_dict.get("human_review_obligations", []),
        timestamp=witness_dict.get("timestamp", ""),
        human_attestations=list(witness_dict.get("human_attestations", [])),
        witness_hash=witness_dict.get("witness_hash", ""),
    )
    w.add_human_attestation(args.signer, notes=args.notes, accepted=not args.reject)

    out = args.out
    if out is None:
        out = args.claim_json.with_name(
            args.claim_json.stem.replace("_claim", "") + "_witness.json"
            if "claim" in args.claim_json.stem
            else args.claim_json.stem + "_witness.json"
        )
        if args.claim_json.name.startswith("out_"):
            out = args.claim_json.with_name(
                args.claim_json.name.replace("_claim.json", "_witness.json")
            )

    out.write_text(w.to_json(), encoding="utf-8")
    print(f"Sealed witness \u2192 {out}")
    print(f"Root SHA-256   \u2192 {w.witness_hash}")
    print(f"Integrity      \u2192 {w.verify_integrity()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
