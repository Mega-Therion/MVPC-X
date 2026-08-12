import argparse
import sys
import os
import json
from datetime import datetime, timezone

from mvpc.policy import PolicyLevel
from mvpc.auditor import audit_directory
from mvpc.report import format_terminal_report, format_json_report, format_markdown_report
from mvpc.hashing import verify_witness_hash, hash_file
from mvpc.witness import Witness
from mvpc.provenance import AIProvenance, SourceType
from mvpc.trust import Finding, Severity

def get_policy_level(policy_str: str) -> PolicyLevel:
    p = policy_str.lower()
    if p == 'permissive':
        return PolicyLevel.PERMISSIVE
    elif p == 'strict':
        return PolicyLevel.STRICT
    return PolicyLevel.DEFAULT

def main():
    parser = argparse.ArgumentParser(
        prog="mvpc",
        description="MVPC-X — Sovereign Claim-Verification Infrastructure & Reproducible Epistemic Engine"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # --- Audit subcommand ---
    audit_p = subparsers.add_parser('audit', help="Audit an artifact or directory against mechanical policy")
    audit_p.add_argument('path', help="Path to artifact (.lean, .v, .thy, .py, ...) or directory")
    audit_p.add_argument('--policy', default='default', choices=['permissive', 'default', 'strict'], help="Policy level (default: default)")
    audit_p.add_argument('--json', action='store_true', help="Output machine-readable JSON")
    audit_p.add_argument('--output-dir', help="Directory to save markdown and JSON reports")
    audit_p.add_argument('--ci-mode', action='store_true', help="CI mode: exit 1 if violations found; exit 2 if human attestation missing when required")
    
    # Governance & Provenance flags
    audit_p.add_argument('--ai-touched', action='store_true', help="Mark artifact as AI-generated/assisted")
    audit_p.add_argument('--ai-model', type=str, default=None, help="AI model identifier (e.g., 'gemini-3.1-pro', 'claude-3-7-sonnet')")
    audit_p.add_argument('--ai-prompt-file', type=str, default=None, help="File containing the generation prompt to hash into provenance")
    audit_p.add_argument('--require-ai-provenance', action='store_true', help="Enforce that AI-touched artifacts must have full model and prompt hashes")
    audit_p.add_argument('--require-human', action='store_true', help="Require human attestation for complete verification")

    # --- Attest subcommand ---
    attest_p = subparsers.add_parser('attest', help="Attach human review attestation to an existing machine witness")
    attest_p.add_argument('witness_file', help="Path to existing witness.json")
    attest_p.add_argument('--signer', required=True, help="Identity or signature of human reviewer")
    attest_p.add_argument('--notes', default="", help="Review notes or qualification of verification")
    attest_p.add_argument('--reject', action='store_true', help="Explicitly mark human review as rejected")
    attest_p.add_argument('--output-file', help="Path to save updated witness (default: overwrites input witness_file)")

    # --- Claim manifest subcommand ---
    claim_p = subparsers.add_parser('claim', help="Process a claim manifest (.yaml)")
    claim_p.add_argument('manifest', help="Path to claim.yaml")
    
    # --- Witness verify subcommand ---
    witness_p = subparsers.add_parser('witness', help="Cryptographic witness operations")
    witness_sub = witness_p.add_subparsers(dest="witness_cmd", required=True)
    verify_w = witness_sub.add_parser('verify', help="Verify cryptographic SHA-256 self-hash of a witness file")
    verify_w.add_argument('witness_file', help="Path to witness.json")
    
    args = parser.parse_args()
    
    if args.command == 'audit':
        policy_level = get_policy_level(args.policy)
        claims = audit_directory(args.path, policy_level)
        
        has_violations = False
        missing_human = False
        
        # Build AI provenance if provided
        ai_prov = None
        if args.ai_touched or args.ai_model or args.ai_prompt_file:
            prompt_h = hash_file(args.ai_prompt_file) if args.ai_prompt_file and os.path.isfile(args.ai_prompt_file) else "none"
            ai_prov = AIProvenance(
                model=args.ai_model or "unspecified",
                provider="unknown",
                prompt_hash=prompt_h,
                generation_time=datetime.now(timezone.utc).isoformat(),
                revision_chain=[],
                human_edits=False
            )

        for c in claims:
            if ai_prov:
                c.provenance.ai_provenance = ai_prov
                c.provenance.source_type = SourceType.AI

            if args.require_ai_provenance and (not c.provenance.ai_provenance or c.provenance.ai_provenance.prompt_hash == "none"):
                c.findings.append(Finding(
                    code="AI_PROVENANCE_MISSING",
                    severity=Severity.VIOLATION,
                    message="Required AI provenance (model or prompt hash) is missing",
                    system="CovenantGovernance"
                ))

            if args.require_human and not c.human_signoff:
                c.findings.append(Finding(
                    code="HUMAN_ATTESTATION_MISSING",
                    severity=Severity.WARNING,
                    message="Human attestation required but not yet attached (run 'mvpc attest')",
                    system="CovenantGovernance"
                ))
                missing_human = True

            state = c.attestation_state.name if hasattr(c.attestation_state, 'name') else str(c.attestation_state)
            if state == 'REJECTED' or any(f.severity == Severity.VIOLATION for f in c.findings):
                has_violations = True
                
            if args.output_dir:
                os.makedirs(args.output_dir, exist_ok=True)
                with open(os.path.join(args.output_dir, f"{c.id}.md"), 'w', encoding='utf-8') as f:
                    f.write(format_markdown_report(c))
                with open(os.path.join(args.output_dir, f"{c.id}.json"), 'w', encoding='utf-8') as f:
                    f.write(format_json_report(c))
                    
            if args.json:
                print(format_json_report(c))
            else:
                print(format_terminal_report(c))
                print()
                
        if args.ci_mode:
            if has_violations:
                sys.exit(1)
            if missing_human and args.require_human:
                sys.exit(2)
            
    elif args.command == 'attest':
        try:
            with open(args.witness_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Rehydrate Witness object
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
                timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
                human_attestations=data.get("human_attestations", []),
                witness_hash=data.get("witness_hash", "")
            )

            # Attach human signoff and re-seal hash
            w.add_human_attestation(
                signer=args.signer,
                notes=args.notes,
                accepted=not args.reject
            )

            out_path = args.output_file or args.witness_file
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(w.to_json())

            print("=" * 70)
            print(f" HUMAN ATTESTATION SEALED — {w.witness_id}")
            print("=" * 70)
            print(f" Claim ID       : {w.claim_id}")
            print(f" Signer         : {args.signer}")
            print(f" Accepted       : {'NO (Rejected)' if args.reject else 'YES'}")
            print(f" Timestamp      : {w.human_attestations[-1]['timestamp']}")
            if args.notes:
                print(f" Notes          : {args.notes}")
            print(f" Root SHA-256   : {w.witness_hash}")
            print(f" Saved to       : {out_path}")
            print("=" * 70)

        except Exception as e:
            print(f"Error during human attestation: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == 'claim':
        from mvpc.engine import VerificationEngine
        from mvpc.backends.registry import get_default_registry
        engine = VerificationEngine(PolicyLevel.DEFAULT, get_default_registry())
        try:
            claim = engine.verify_claim(args.manifest)
            print(format_terminal_report(claim))
        except NotImplementedError as e:
            print(f"Error: {e}")
            sys.exit(1)
            
    elif args.command == 'witness' and args.witness_cmd == 'verify':
        try:
            with open(args.witness_file, 'r', encoding='utf-8') as f:
                w_dict = json.load(f)
            if verify_witness_hash(w_dict):
                print(f"✓ Witness hash is VALID (SHA-256: {w_dict.get('witness_hash', 'N/A')})")
            else:
                print("✗ Witness hash is INVALID (tampered or corrupted)")
                sys.exit(1)
        except Exception as e:
            print(f"Error verifying witness: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
