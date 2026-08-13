"""Unified CLI entry bridging legacy mvpc commands with nexus + harden."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mvpc.version import __version__


def _cmd_nexus(argv: list[str]) -> int:
    from mvpc.nexus_cli import main as nexus_main

    return int(nexus_main(argv))


def _cmd_harden(args: argparse.Namespace) -> int:
    from mvpc.hardened_pipeline import HardenedSovereignPipeline

    if args.claim_file:
        claim = json.loads(Path(args.claim_file).read_text(encoding="utf-8"))
    else:
        claim = {
            "formal_code": args.code or "theorem t : True := by\n  trivial\n",
            "target_backend": args.backend,
            "proposer_type": "biological",
            "physical_realization_profile": {
                "requires_si_checking": True,
                "physical_variables": {"m": "mass", "v": "velocity"},
                "max_allowable_velocity": 100.0,
                "max_allowable_temperature": 350.0,
            },
        }
    traj = None
    if args.trajectory_file:
        t = json.loads(Path(args.trajectory_file).read_text(encoding="utf-8"))
        traj = (t["time"], t["velocity"], t["temperature"])
    cas = None
    if args.cas_target and args.cas_generators and args.cas_vars:
        cas = (args.cas_target, [g.strip() for g in args.cas_generators.split(",")], args.cas_vars)

    pipe = HardenedSovereignPipeline(sign=not args.no_sign)
    result = pipe.run(
        claim,
        trajectory_data=traj,
        cas_polynomials=cas,
        consensus_backends=tuple(args.consensus.split(",")),
        enable_repair=not args.no_repair,
    )
    print(json.dumps(result, indent=2, default=str))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return 0 if result["overall_status"] == "PASSED" else 1


def _cmd_legacy(argv: list[str]) -> int:
    try:
        from mvpc.cli import main as legacy_main
    except Exception as exc:
        print(f"legacy cli unavailable: {exc}", file=sys.stderr)
        return 2
    try:
        return int(legacy_main(argv))
    except TypeError:
        sys.argv = ["mvpc", *argv]
        return int(legacy_main())


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="mvpc-bridge",
        description=f"MVPC-X unified CLI bridge v{__version__}",
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd")

    p_n = sub.add_parser("nexus", help="Nexus CLI (audit/cps-check/si-check)")
    p_n.add_argument("nexus_args", nargs=argparse.REMAINDER)

    p_h = sub.add_parser("harden", help="Hardened end-to-end pipeline")
    p_h.add_argument("--claim-file")
    p_h.add_argument("--code")
    p_h.add_argument("--backend", default="lean4")
    p_h.add_argument("--trajectory-file")
    p_h.add_argument("--cas-target")
    p_h.add_argument("--cas-generators")
    p_h.add_argument("--cas-vars")
    p_h.add_argument("--consensus", default="lean4,dafny")
    p_h.add_argument("--no-sign", action="store_true")
    p_h.add_argument("--no-repair", action="store_true")
    p_h.add_argument("--json-out")
    p_h.set_defaults(func=_cmd_harden)

    p_l = sub.add_parser("legacy", help="Delegate to mvpc.cli")
    p_l.add_argument("legacy_args", nargs=argparse.REMAINDER)

    if argv and argv[0] == "nexus":
        rest = argv[1:]
        if rest and rest[0] == "--":
            rest = rest[1:]
        return _cmd_nexus(rest)
    if argv and argv[0] == "legacy":
        rest = argv[1:]
        if rest and rest[0] == "--":
            rest = rest[1:]
        return _cmd_legacy(rest)

    args = parser.parse_args(argv)
    if args.cmd == "harden":
        return int(args.func(args))
    if args.cmd == "nexus":
        return _cmd_nexus(getattr(args, "nexus_args", []) or [])
    if args.cmd == "legacy":
        return _cmd_legacy(getattr(args, "legacy_args", []) or [])
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
