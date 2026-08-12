import argparse
import sys
import os
import json

from mvpc.policy import PolicyLevel
from mvpc.auditor import audit_directory
from mvpc.report import format_terminal_report, format_json_report, format_markdown_report
from mvpc.hashing import verify_witness_hash

def get_policy_level(policy_str: str) -> PolicyLevel:
    p = policy_str.lower()
    if p == 'permissive':
        return PolicyLevel.PERMISSIVE
    elif p == 'strict':
        return PolicyLevel.STRICT
    return PolicyLevel.DEFAULT

def main():
    parser = argparse.ArgumentParser(description="MVP-C Core Engine CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    audit_p = subparsers.add_parser('audit', help="Audit a single artifact or directory")
    audit_p.add_argument('path', help="Path to artifact or directory")
    audit_p.add_argument('--policy', default='default', choices=['permissive', 'default', 'strict'], help="Policy level")
    audit_p.add_argument('--json', action='store_true', help="Output in JSON")
    audit_p.add_argument('--output-dir', help="Directory to save reports")
    audit_p.add_argument('--ci-mode', action='store_true', help="CI mode (exit code reflects state)")
    
    claim_p = subparsers.add_parser('claim', help="Process a claim manifest")
    claim_p.add_argument('manifest', help="Path to claim.yaml")
    
    witness_p = subparsers.add_parser('witness', help="Witness operations")
    witness_sub = witness_p.add_subparsers(dest="witness_cmd", required=True)
    verify_w = witness_sub.add_parser('verify', help="Verify a witness")
    verify_w.add_argument('witness_file', help="Path to witness.json")
    
    args = parser.parse_args()
    
    if args.command == 'audit':
        claims = audit_directory(args.path, get_policy_level(args.policy))
        
        has_rejections = False
        
        for c in claims:
            state = c.attestation_state.name if hasattr(c.attestation_state, 'name') else str(c.attestation_state)
            if state == 'REJECTED':
                has_rejections = True
                
            if args.output_dir:
                os.makedirs(args.output_dir, exist_ok=True)
                base = os.path.basename(args.path)
                with open(os.path.join(args.output_dir, f"{c.id}.md"), 'w') as f:
                    f.write(format_markdown_report(c))
                with open(os.path.join(args.output_dir, f"{c.id}.json"), 'w') as f:
                    f.write(format_json_report(c))
                    
            if args.json:
                print(format_json_report(c))
            else:
                print(format_terminal_report(c))
                print("-" * 40)
                
        if args.ci_mode and has_rejections:
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
            with open(args.witness_file, 'r') as f:
                w_dict = json.load(f)
            if verify_witness_hash(w_dict):
                print("Witness hash is VALID")
            else:
                print("Witness hash is INVALID")
                sys.exit(1)
        except Exception as e:
            print(f"Error verifying witness: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
