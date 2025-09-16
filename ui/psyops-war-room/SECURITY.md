# War Room Security Guidance

## Content Security Policy (CSP)

Recommended headers when fronting the app with a reverse proxy:

```
Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' https:;
X-Frame-Options: DENY
Referrer-Policy: no-referrer
```

Adjust `connect-src` to include your API origin(s).

## Dependency hygiene

- Lockfile committed; CI runs `npm audit --omit=dev` (or your SCA of choice) on release branches.  
- Keep Node ≥ 20 and vite/react updated; renovate/dependabot enabled.  
- No runtime `eval`/`Function` or dynamic script injection.

## Input & output handling

- **Never** render untrusted HTML (`dangerouslySetInnerHTML`).  
- Escape output in tables; all data displayed here comes from JSON APIs and should be plain text.  
- Validate action parameters on the server (PsyOps). The UI validates for UX only.

## Secrets & telemetry

- No secrets in the bundle; configuration via environment and reverse proxy headers only.  
- Optional `x-ui-version` header already added in the API client.

## Future

- Add a CSP `report-uri` endpoint and surface blocked script/style metrics.  
- Add SRI hashes if/when external assets are introduced (currently none).
