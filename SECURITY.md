# Security Policy

We take the security of `sissa_ivy` seriously. Please follow the guidance below to report vulnerabilities responsibly.

## Supported Branches

Currently maintained (accepting security fixes):

- `main`
- Active feature branches with open PRs (security fixes will be rebased/merged promptly)

## Reporting a Vulnerability

1. Do NOT open a public GitHub issue for suspected security problems.
2. Email a minimal report to: `SECURITY_DISCLOSURE_PLACEHOLDER@example.com` (replace once real alias exists).
3. Include:
   - Affected files / components
   - Reproduction steps or proof-of-concept (avoid destructive payloads)
   - Impact assessment (confidentiality / integrity / availability)
   - Suggested remediation if known
4. Optionally include a short-term mitigation (config change, command-line flag, etc.).

## Handling Timeline (Target)

| Phase | Target Window |
|-------|---------------|
| Initial acknowledgement | 3 business days |
| Triage & severity classification | 7 days |
| Fix development (medium severity) | 30 days |
| Coordinated disclosure (if needed) | Case-by-case |

High/critical issues will be prioritized and may follow an accelerated path.

## Severity Guidance (Informal)

- Critical: Remote code execution or unauthorized data modification.
- High: Privilege escalation, denial of service with minimal effort.
- Medium: Information disclosure of non-sensitive operational details.
- Low: Hard-to-exploit edge cases or non-sensitive metadata leakage.

## Out of Scope

- Social engineering attacks.
- Dependency vulnerabilities already tracked upstream unless a unique exploit path exists here.
- Misconfigurations unrelated to repository code.

## Patch Process

1. Private patch drafted & reviewed.
2. Tests added or updated (regression + negative).
3. Fix merged into `main` with clear security note in commit/PR.
4. (Optional) Point release or tag created if necessary.

## Credit & Disclosure

We will credit reporters in release notes unless anonymity is requested.

## Using the Project Securely

- Pin dependencies when they are introduced.
- Run the repository tools with least privilege.
- Review JSON spec changes (e.g., archetypes) for untrusted injections.

## Contact

Until a dedicated security address is configured, use the placeholder email and optionally open a PRIVATE discussion if enabled.

Thank you for helping keep this project safe and reliable.
