# MVPC-X Security Response

## Reporting

Report vulnerabilities privately. Do not open public issues for unfixed security bugs.

Include: description, reproduction, affected components, impact, optional fix idea.

## Targets

| Stage | Target |
|---|---|
| Acknowledgment | 48 hours |
| Initial assessment | 7 days |
| Fix/mitigation | severity-dependent, aim 30 days |
| Public disclosure | after fix or 90 days |

## Critical examples

- Signature forgery without private key
- FORMALLY_CHECKED without valid checker acceptance
- Sandbox escape
- Policy-as-code execution

## Supply chain baseline

CI-only builds, locked dependencies, SBOM, signed releases, no long-lived publish tokens when OIDC is available.
