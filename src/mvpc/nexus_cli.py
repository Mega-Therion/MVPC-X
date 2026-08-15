"""Unified Nexus CLI — python -m mvpc.nexus_cli

Subcommands: audit, cps-check, si-check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from mvpc import __version__
except Exception:  # pragma: no cover
    __version__ = "8.0.0"

from mvpc.nexus_pipeline import SovereignNexusPipeline
from mvpc.phys.hybrid_automata import CPSSafetyAuditor, SafetyBounds
from mvpc.phys.si_units import SIDimensionChecker


def cmd_audit(args: argparse.Namespace) -> int:
    pipeline = SovereignNexusPipeline()

    if args.claim_file:
        raw_claim = json.loads(Path(args.claim_file).read_text(encoding="utf-8"))
    elif args.claim_json:
        raw_claim = json.loads(args.claim_json)
    else:
        raw_claim = {
            "claim_id": "cli-claim-001",
            "proposer_type": "symbiotic",
            "target_backend": "lean4",
            "formal_code": "theorem safety_check (x : Real) : x = x := by rfl",
            "physical_realization_profile": {
                "requires_si_checking": True,
                "requires_cps_bounds": True,
                "max_allowable_temperature": args.temp_max,
                "max_allowable_velocity": args.v_max,
                "physical_variables": {"m": "mass", "v": "velocity"},
            },
        }

    trajectory = None
    if args.trajectory_file:
        traj = json.loads(Path(args.trajectory_file).read_text(encoding="utf-8"))
        trajectory = (traj["time"], traj["velocity"], traj["temperature"])

    cas_polys = None
    if args.cas_target and args.cas_generators and args.cas_vars:
        gens = [g.strip() for g in args.cas_generators.split(",")]
        cas_polys = (args.cas_target, gens, args.cas_vars)

    result = pipeline.run_pipeline(
        raw_claim_json=raw_claim,
        trajectory_data=trajectory,
        cas_polynomials=cas_polys,
    )

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"[+] Audit JSON -> {args.json_out}")

    if args.export_md:
        md = f"""# MVPC Sovereign Nexus Audit Report
**Version:** {__version__}  
**Claim ID:** `{result['claim_id']}`  
**Overall Status:** `{result['overall_status']}`  
**Trust Verdict:** `{result.get('trust_verdict')}`  
**Driver Mode:** `{result.get('driver_mode')}`  

## Verification Summary
- **Backend:** `{result['target_backend']}`
- **Heuristic Pass:** `{result['verification_result'].get('heuristic_pass')}`
- **SafeVerify Passed:** `{result['safe_verify_audit']['passed']}`
- **SI / Leakage:** `{result['si_dimension_certification']['certified']}`
- **CPS Safe:** `{result['cps_safety_certification']['certified']}`

> Note: Heuristic pass is **not** FORMALLY_CHECKED. Real kernel acceptance required for formal truth claims.

## Evidence Manifest
- **Pre-Audit FP:** `{result['immutable_evidence_manifest']['pre_audit_fingerprint']}`
- **Post-Audit FP:** `{result['immutable_evidence_manifest']['post_audit_fingerprint']}`
- **Chain Hash:** `{result['immutable_evidence_manifest']['evidence_chain_hash']}`
"""
        Path(args.export_md).write_text(md, encoding="utf-8")
        print(f"[+] Markdown -> {args.export_md}")

    print(json.dumps(result, indent=2))
    return 0 if result["overall_status"] == "PASSED" else 1


def cmd_cps_check(args: argparse.Namespace) -> int:
    auditor = CPSSafetyAuditor()
    if args.trajectory_file:
        data = json.loads(Path(args.trajectory_file).read_text(encoding="utf-8"))
        t_steps, v_prof, temp_prof = data["time"], data["velocity"], data["temperature"]
    else:
        t_steps = [0.0, 1.0, 2.0]
        v_prof = [10.0, 40.0, 80.0]
        temp_prof = [295.0, 310.0, 325.0]

    bounds = SafetyBounds(max_velocity=args.v_max, max_temperature=args.temp_max)
    is_safe, violations = auditor.audit_trajectory(
        t_steps, v_prof, temp_prof, bounds=bounds
    )
    print(
        json.dumps(
            {
                "cps_safe": is_safe,
                "max_velocity_limit": args.v_max,
                "max_temperature_limit": args.temp_max,
                "violations": violations,
            },
            indent=2,
        )
    )
    return 0 if is_safe else 1


def cmd_si_check(args: argparse.Namespace) -> int:
    checker = SIDimensionChecker()
    if not args.lhs or not args.rhs:
        print("[-] --lhs and --rhs required (e.g. --lhs F --rhs m:1.0,a:1.0)")
        return 1

    terms = []
    for part in args.rhs.split(","):
        part = part.strip()
        if not part:
            continue
        bits = part.split(":")
        var_name = bits[0].strip()
        exp = float(bits[1].strip()) if len(bits) > 1 else 1.0
        terms.append((var_name, exp))

    match, msg = checker.verify_equation(args.lhs, terms)
    print(json.dumps({"si_homogeneity_match": match, "details": msg}, indent=2))
    return 0 if match else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mvpc-nexus",
        description=f"MVPC Sovereign Nexus CLI v{__version__}",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    p_audit = sub.add_parser("audit", help="Full Nexus audit pipeline")
    p_audit.add_argument("--claim-file")
    p_audit.add_argument("--claim-json")
    p_audit.add_argument("--trajectory-file")
    p_audit.add_argument("--cas-target")
    p_audit.add_argument("--cas-generators")
    p_audit.add_argument("--cas-vars")
    p_audit.add_argument("--v-max", type=float, default=100.0)
    p_audit.add_argument("--temp-max", type=float, default=350.0)
    p_audit.add_argument("--json-out")
    p_audit.add_argument("--export-md")
    p_audit.set_defaults(func=cmd_audit)

    p_cps = sub.add_parser("cps-check", help="Standalone CPS trajectory check")
    p_cps.add_argument("--trajectory-file")
    p_cps.add_argument("--v-max", type=float, default=100.0)
    p_cps.add_argument("--temp-max", type=float, default=350.0)
    p_cps.set_defaults(func=cmd_cps_check)

    p_si = sub.add_parser("si-check", help="Standalone SI homogeneity check")
    p_si.add_argument("--lhs")
    p_si.add_argument("--rhs", help="e.g. m:1.0,a:1.0")
    p_si.set_defaults(func=cmd_si_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
