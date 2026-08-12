import json
from mvpc.claim import Claim
from mvpc.trust import AttestationState, Finding, Severity

def format_terminal_report(claim: Claim) -> str:
    """Format claim report for terminal."""
    out = []
    out.append(f"Claim ID: {claim.id}")
    out.append(f"Statement: {claim.statement}")
    out.append(f"State: {claim.attestation_state.name if hasattr(claim.attestation_state, 'name') else str(claim.attestation_state)}")
    
    out.append("\nCoverage:")
    out.append(f"  Checks Performed: {', '.join(claim.coverage.checks_performed)}")
    if claim.coverage.checks_unavailable:
        out.append(f"  Checks Unavailable: {', '.join(claim.coverage.checks_unavailable)}")
        
    if claim.findings:
        out.append("\nFindings:")
        for f in claim.findings:
            sev = f.severity.name if hasattr(f.severity, 'name') else str(f.severity)
            out.append(f"  [{sev}] {f.code}: {f.message}")
            
    out.append("\nNote: This specific set of checks passed. The artifact is proportional to the verification actually performed.")
    return "\n".join(out)

def format_markdown_report(claim: Claim) -> str:
    """Format claim report as markdown."""
    md = f"# Verification Report: {claim.id}\n\n"
    md += f"**Statement**: {claim.statement}\n"
    state = claim.attestation_state.name if hasattr(claim.attestation_state, 'name') else str(claim.attestation_state)
    md += f"**State**: {state}\n\n"
    
    md += "## Coverage\n"
    md += f"- Checks Performed: {', '.join(claim.coverage.checks_performed)}\n"
    if claim.coverage.checks_unavailable:
        md += f"- Checks Unavailable: {', '.join(claim.coverage.checks_unavailable)}\n"
        
    if claim.findings:
        md += "\n## Findings\n"
        for f in claim.findings:
            sev = f.severity.name if hasattr(f.severity, 'name') else str(f.severity)
            md += f"- **{sev}** ({f.code}): {f.message}\n"
            
    md += "\n> Note: This specific set of checks passed. Absence of detected problems is not evidence of truth.\n"
    return md

def format_json_report(claim: Claim) -> str:
    """Format claim report as JSON."""
    return claim.to_json()
