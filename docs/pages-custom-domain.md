# GitHub Pages — Custom Domain for PitCrew Dashboard

This repo publishes the dashboard from `ui/pitcrew-dashboard/dist` to GitHub Pages.

## Two ways to set a custom domain

1) Repo Settings (manual)
   - Go to GitHub → repository → Settings → Pages → Custom domain
   - Enter your domain (e.g., `example.com` or `www.example.com`) and Save
   - GitHub will create a `CNAME` file automatically on first publish

2) CI‑driven (recommended)
   - Add a repo secret `PAGES_CUSTOM_DOMAIN` with the domain value (no protocol)
   - The Pages workflow writes that value to `dist/CNAME` at build time

## DNS configuration

- Apex (root) domain, e.g., `example.com` → set these A records:
  - 185.199.108.153
  - 185.199.109.153
  - 185.199.110.153
  - 185.199.111.153

- Subdomain, e.g., `www.example.com` → set a CNAME record pointing to:
  - `<your-username>.github.io`

After DNS propagates (can take up to 24 hours), return to Settings → Pages and enable “Enforce HTTPS”.

## Security notes

- Avoid wildcard records like `*.example.com` (domain takeover risk)
- Verify your domain in GitHub for additional protection

