import json
from mvpc.claim import Claim
from mvpc.trust import AttestationState, Finding, Severity
from mvpc.explanations import get_explanation

def format_terminal_report(claim: Claim) -> str:
    """Format claim report for terminal with plain-English remediation advice."""
    out = []
    out.append("=" * 70)
    out.append(f" MVPC-X CLAIM ATTESTATION — {claim.id}")
    out.append("=" * 70)
    out.append(f" Statement : {claim.statement}")
    state = claim.attestation_state.name if hasattr(claim.attestation_state, 'name') else str(claim.attestation_state)
    out.append(f" State     : {state}")
    
    out.append("\n Coverage:")
    out.append(f"  ✓ Performed   : {', '.join(claim.coverage.checks_performed) if claim.coverage.checks_performed else 'None'}")
    if claim.coverage.checks_unavailable:
        out.append(f"  ⚠ Unavailable : {', '.join(claim.coverage.checks_unavailable)}")
        
    if claim.findings:
        out.append("\n Findings & Guidance:")
        for i, f in enumerate(claim.findings, 1):
            sev = f.severity.name if hasattr(f.severity, 'name') else str(f.severity)
            exp = get_explanation(f.code)
            line_str = f" (line {f.line})" if f.line else ""
            out.append(f"  [{i}] {sev} | {exp.get('title', f.code)} ({f.code}){line_str}")
            out.append(f"      Message : {f.message}")
            if exp.get('explanation'):
                out.append(f"      Why     : {exp['explanation']}")
            remediation = f.remediation or exp.get('action')
            if remediation:
                out.append(f"      Fix     : {remediation}")
            out.append("")

    if claim.human_signoff:
        out.append(" Human Attestation:")
        signer = claim.human_signoff.get('signer', 'Unknown')
        ts = claim.human_signoff.get('timestamp', 'Unknown')
        notes = claim.human_signoff.get('notes', '')
        acc = claim.human_signoff.get('accepted', True)
        out.append(f"  Signed by: {signer} @ {ts} | Accepted: {acc}")
        if notes:
            out.append(f"  Notes    : {notes}")
        out.append("")
            
    out.append("=" * 70)
    out.append(" Note: Every assurance claim must be proportional to verification performed.")
    out.append("=" * 70)
    return "\n".join(out)

def format_markdown_report(claim: Claim) -> str:
    """Format claim report as rich GitHub Markdown."""
    state = claim.attestation_state.name if hasattr(claim.attestation_state, 'name') else str(claim.attestation_state)
    md = [
        f"# MVPC-X Verification Report: `{claim.id}`\n",
        f"**Statement**: {claim.statement}\n",
        f"**Attestation State**: `{state}`\n",
        "## Coverage\n",
        f"- **Checks Performed**: {', '.join(claim.coverage.checks_performed) if claim.coverage.checks_performed else 'None'}",
    ]
    if claim.coverage.checks_unavailable:
        md.append(f"- **Checks Unavailable**: {', '.join(claim.coverage.checks_unavailable)}")
        
    if claim.findings:
        md.append("\n## Findings & Remediation\n")
        for i, f in enumerate(claim.findings, 1):
            sev = f.severity.name if hasattr(f.severity, 'name') else str(f.severity)
            exp = get_explanation(f.code)
            line_str = f" (line {f.line})" if f.line else ""
            md.append(f"### {i}. {exp.get('title', f.code)} (`{f.code}`){line_str}")
            md.append(f"- **Severity**: `{sev}`")
            md.append(f"- **Message**: {f.message}")
            if exp.get('explanation'):
                md.append(f"- **Explanation**: {exp['explanation']}")
            remediation = f.remediation or exp.get('action')
            if remediation:
                md.append(f"- **How to Fix**: {remediation}")
            md.append("")

    if claim.human_signoff:
        md.append("## Human Attestation\n")
        signer = claim.human_signoff.get('signer', 'Unknown')
        ts = claim.human_signoff.get('timestamp', 'Unknown')
        notes = claim.human_signoff.get('notes', '')
        acc = claim.human_signoff.get('accepted', True)
        md.append(f"- **Signer**: `{signer}`")
        md.append(f"- **Timestamp**: `{ts}`")
        md.append(f"- **Accepted**: `{'YES' if acc else 'NO'}`")
        if notes:
            md.append(f"- **Notes**: {notes}")
        md.append("")
            
    md.append("\n> **The Sovereign Covenant**: AI proposes. Machines verify. Humans audit. Evidence persists.\n")
    return "\n".join(md)

def format_json_report(claim: Claim) -> str:
    """Format claim report as JSON."""
    return claim.to_json()
