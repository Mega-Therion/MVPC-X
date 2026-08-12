"""MVPC-X command line interface."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from mvpc.policy import PolicyLevel
from mvpc.auditor import audit_directory
from mvpc.report import format_terminal_report, format_json_report, format_markdown_report
from mvpc.hashing import verify_witness_hash, hash_file
from mvpc.witness import Witness
from mvpc.provenance import AIProvenance, SourceType
from mvpc.trust import Finding, Severity
from mvpc.preflight import run_preflight, format_preflight_terminal
from mvpc.scaffold import scaffold, list_templates
from mvpc.security import compute_system_fingerprint, IntegritySession


def get_policy_level(policy_str: str) -> PolicyLevel:
    p = policy_str.lower()
    if p == "permissive":
        return PolicyLevel.PERMISSIVE
    if p == "strict":
        return PolicyLevel.STRICT
    return PolicyLevel.DEFAULT


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="mvpc",
        description=(
            "MVPC-X — Sovereign Claim-Verification Infrastructure. "
            "AI proposes. Machines verify. Humans audit. Evidence persists."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- audit ---
    audit_p = sub.add_parser("audit", help="Audit an artifact or directory")
    audit_p.add_argument("path", help="File or directory")
    audit_p.add_argument(
        "--policy",
        default="default",
        choices=["permissive", "default", "strict"],
    )
    audit_p.add_argument("--json", action="store_true")
    audit_p.add_argument("--output-dir", help="Save md/json reports here")
    audit_p.add_argument("--ci-mode", action="store_true")
    audit_p.add_argument("--ai-touched", action="store_true")
    audit_p.add_argument("--ai-model", type=str, default=None)
    audit_p.add_argument("--ai-prompt-file", type=str, default=None)
    audit_p.add_argument("--require-ai-provenance", action="store_true")
    audit_p.add_argument("--require-human", action="store_true")
    audit_p.add_argument(
        "--allow-symlinks", action="store_true", help="Allow symlink artifacts"
    )
    audit_p.add_argument(
        "--skip-system-integrity",
        action="store_true",
        help="Do not fail closed on system fingerprint mismatch (debug only)",
    )
    audit_p.add_argument(
        "--preflight-first",
        action="store_true",
        help="Print preflight report before auditing",
    )

    # --- preflight ---
    pre_p = sub.add_parser(
        "preflight", help="Classify input, probe tools, score structure (no full audit)"
    )
    pre_p.add_argument("path", help="File or directory")
    pre_p.add_argument("--json", action="store_true")
    pre_p.add_argument("--allow-symlinks", action="store_true")
    pre_p.add_argument(
        "--ci-mode",
        action="store_true",
        help="Exit 1 if blocked; exit 2 if not ready_for_deep_audit",
    )

    # --- scaffold ---
    sc_p = sub.add_parser("scaffold", help="Write a standard high-assurance template")
    sc_p.add_argument(
        "kind",
        help=f"Template kind: {', '.join(list_templates())}",
    )
    sc_p.add_argument(
        "dest",
        nargs="?",
        default=".",
        help="Destination directory (default: .)",
    )
    sc_p.add_argument("--force", action="store_true")
    sc_p.add_argument(
        "--list", action="store_true", dest="list_only", help="List templates and exit"
    )

    # --- integrity (system self-check without artifact) ---
    int_p = sub.add_parser(
        "integrity",
        help="Show or verify MVPC-X system self-fingerprint (no artifact required)",
    )
    int_p.add_argument(
        "--json", action="store_true", help="Dump full fingerprint JSON"
    )
    int_p.add_argument(
        "--verify-twice",
        action="store_true",
        help="Capture seal, sleep 0, re-check (sanity)",
    )

    # --- attest ---
    attest_p = sub.add_parser("attest", help="Attach human attestation to a witness")
    attest_p.add_argument("witness_file")
    attest_p.add_argument("--signer", required=True)
    attest_p.add_argument("--notes", default="")
    attest_p.add_argument("--reject", action="store_true")
    attest_p.add_argument("--output-file")

    # --- claim ---
    claim_p = sub.add_parser("claim", help="Process a claim manifest (.yaml)")
    claim_p.add_argument("manifest")

    # --- witness ---
    wit_p = sub.add_parser("witness", help="Cryptographic witness operations")
    wit_sub = wit_p.add_subparsers(dest="witness_cmd", required=True)
    v_w = wit_sub.add_parser("verify", help="Verify witness self-hash")
    v_w.add_argument("witness_file")

    args = parser.parse_args(argv)

    if args.command == "preflight":
        report = run_preflight(args.path, allow_symlinks=args.allow_symlinks)
        if args.json:
            print(report.to_json())
        else:
            print(format_preflight_terminal(report))
        if args.ci_mode:
            if report.readiness.value == "blocked":
                sys.exit(1)
            if report.readiness.value != "ready_for_deep_audit":
                sys.exit(2)
        return

    if args.command == "scaffold":
        if getattr(args, "list_only", False):
            print("\n".join(list_templates()))
            return
        try:
            written = scaffold(args.kind, args.dest, force=args.force)
        except (ValueError, FileExistsError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        print("Scaffold wrote:")
        for w in written:
            print(f"  {w}")
        print("Next: mvpc preflight <file> && mvpc audit <file>")
        return

    if args.command == "integrity":
        if args.verify_twice:
            s = IntegritySession.begin(None)
            ok_mid = s.check_mid()
            ok = s.finalize()
            if args.json:
                print(json.dumps(s.to_dict(), indent=2))
            else:
                print("MVPC-X system integrity session")
                print(f"  before : {s.system_before['system_fingerprint']}")
                print(f"  mid OK : {ok_mid}")
                print(f"  after  : {(s.system_after or {}).get('system_fingerprint')}")
                print(f"  intact : {s.system_intact}")
            sys.exit(0 if ok and s.system_intact else 1)
        fp = compute_system_fingerprint()
        if args.json:
            print(json.dumps(fp, indent=2))
        else:
            print("MVPC-X system fingerprint")
            print(f"  root   : {fp['package_root']}")
            print(f"  files  : {fp['file_count']}")
            print(f"  sha256 : {fp['system_fingerprint']}")
            print(f"  time   : {fp['timestamp']}")
        return

    if args.command == "audit":
        if args.preflight_first and not args.json:
            print(format_preflight_terminal(run_preflight(args.path, allow_symlinks=args.allow_symlinks)))
            print()

        # Patch engine defaults via environment consumed in auditor — set on engine through audit_directory kwargs if supported
        from mvpc.engine import VerificationEngine
        from mvpc.backends.registry import get_default_registry

        # Prefer directory helper but inject engine settings by monkeypatching path:
        engine = VerificationEngine(
            get_policy_level(args.policy),
            get_default_registry(),
            enforce_system_integrity=not args.skip_system_integrity,
            allow_symlinks=args.allow_symlinks,
        )

        if os.path.isfile(args.path):
            claims = [engine.verify_artifact(args.path)]
        else:
            # reuse walk but with our engine
            claims = []
            for root, _, files in os.walk(args.path):
                for file in files:
                    if file.startswith("."):
                        continue
                    claims.append(engine.verify_artifact(os.path.join(root, file)))

        has_violations = False
        missing_human = False

        ai_prov = None
        if args.ai_touched or args.ai_model or args.ai_prompt_file:
            prompt_h = (
                hash_file(args.ai_prompt_file)
                if args.ai_prompt_file and os.path.isfile(args.ai_prompt_file)
                else "none"
            )
            ai_prov = AIProvenance(
                model=args.ai_model or "unspecified",
                provider="unknown",
                prompt_hash=prompt_h,
                generation_time=datetime.now(timezone.utc).isoformat(),
                revision_chain=[],
                human_edits=False,
            )

        for c in claims:
            if ai_prov:
                c.provenance.ai_provenance = ai_prov
                c.provenance.source_type = SourceType.AI
            if args.require_ai_provenance and (
                not c.provenance.ai_provenance
                or c.provenance.ai_provenance.prompt_hash == "none"
            ):
                c.findings.append(
                    Finding(
                        code="AI_PROVENANCE_MISSING",
                        severity=Severity.VIOLATION,
                        message="Required AI provenance missing",
                        system="CovenantGovernance",
                    )
                )
            if args.require_human and not c.human_signoff:
                c.findings.append(
                    Finding(
                        code="HUMAN_ATTESTATION_MISSING",
                        severity=Severity.WARNING,
                        message="Human attestation required (mvpc attest)",
                        system="CovenantGovernance",
                    )
                )
                missing_human = True

            state = (
                c.attestation_state.name
                if hasattr(c.attestation_state, "name")
                else str(c.attestation_state)
            )
            if state == "REJECTED" or any(
                f.severity == Severity.VIOLATION for f in c.findings
            ):
                has_violations = True

            if args.output_dir:
                os.makedirs(args.output_dir, exist_ok=True)
                with open(
                    os.path.join(args.output_dir, f"{c.id}.md"), "w", encoding="utf-8"
                ) as f:
                    f.write(format_markdown_report(c))
                with open(
                    os.path.join(args.output_dir, f"{c.id}.json"), "w", encoding="utf-8"
                ) as f:
                    f.write(format_json_report(c))

            if args.json:
                print(format_json_report(c))
            else:
                print(format_terminal_report(c))
                # surface integrity one-liner
                integ = (c.provenance.metadata or {}).get("integrity") or {}
                if integ:
                    print(
                        f" System integrity: intact={integ.get('system_intact')} "
                        f"fp={str(integ.get('system_fingerprint_before', ''))[:16]}…"
                    )
                print()

        if args.ci_mode:
            if has_violations:
                sys.exit(1)
            if missing_human and args.require_human:
                sys.exit(2)
        return

    if args.command == "attest":
        try:
            with open(args.witness_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            w = Witness(
                witness_id=data.get("witness_id", "W-UNKNOWN"),
                claim_id=data.get("claim_id", "C-UNKNOWN"),
                artifact_path=data.get("artifact_path", "unknown"),
                artifact_hash=data.get("artifact_hash", "unknown"),
                environment=data.get("environment", {}),
                policy=data.get("policy", {}),
                checks_performed=data.get("checks_performed", []),
                findings=data.get("findings", []),
                evidence=data.get("evidence", []),
                coverage=data.get("coverage", {}),
                attestation_state=data.get("attestation_state", "UNVERIFIED"),
                remediation=data.get("remediation"),
                human_review_obligations=data.get("human_review_obligations", []),
                timestamp=data.get(
                    "timestamp", datetime.now(timezone.utc).isoformat()
                ),
                human_attestations=data.get("human_attestations", []),
                witness_hash=data.get("witness_hash", ""),
            )
            w.add_human_attestation(
                signer=args.signer, notes=args.notes, accepted=not args.reject
            )
            out_path = args.output_file or args.witness_file
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(w.to_json())
            print("=" * 70)
            print(f" HUMAN ATTESTATION SEALED — {w.witness_id}")
            print("=" * 70)
            print(f" Signer       : {args.signer}")
            print(f" Accepted     : {'NO' if args.reject else 'YES'}")
            print(f" Root SHA-256 : {w.witness_hash}")
            print(f" Saved        : {out_path}")
            print("=" * 70)
        except Exception as e:
            print(f"Error during attestation: {e}", file=sys.stderr)
            sys.exit(1)
        return

    if args.command == "claim":
        from mvpc.engine import VerificationEngine
        from mvpc.backends.registry import get_default_registry

        engine = VerificationEngine(PolicyLevel.DEFAULT, get_default_registry())
        try:
            claim = engine.verify_claim(args.manifest)
            print(format_terminal_report(claim))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    if args.command == "witness" and args.witness_cmd == "verify":
        try:
            with open(args.witness_file, "r", encoding="utf-8") as f:
                w_dict = json.load(f)
            if verify_witness_hash(w_dict):
                print(
                    f"✓ Witness hash VALID (SHA-256: {w_dict.get('witness_hash', 'N/A')})"
                )
            else:
                print("✗ Witness hash INVALID (tampered or corrupted)")
                sys.exit(1)
        except Exception as e:
            print(f"Error verifying witness: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
