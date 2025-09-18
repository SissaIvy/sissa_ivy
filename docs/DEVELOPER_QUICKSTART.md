# Developer Quick‑Start (Codespaces & Local)# Developer Quick‑Start (Codespaces & Local)

## 0) Prereqs## 0) Prereqs

- Python 3.11+ (local) or GitHub Codespaces

- Optional: Node 18+ if you run the War Room UI locally- **Python 3.11+** (local) or **GitHub Codespaces**.

- Optional: Node 18+ if you run the War Room UI locally.

## 1) Clone / Open

```bash## 1) Clone / Open

git clone https://github.com/SissaIvy/sissa_ivy.git

cd sissa_ivy```bash

```git clone https://github.com/SissaIvy/sissa_ivy.git

– or open the repo in **Codespaces**.cd sissa_ivy

```

## 2) Hygiene (one command)

```bash– or open the repo in **Codespaces**.

make -C "$(git rev-parse --show-toplevel)" repo-hygiene

```## 2) Hygiene (one command)

Runs Unicode normalization, bidi/hidden Unicode checks, layout guard, and pre‑commit hooks.

```bash

## 3) Python envmake -C "$(git rev-parse --show-toplevel)" repo-hygiene

```bash```

python -m venv .venv && source .venv/bin/activate

pip install -r requirements.txtRuns Unicode normalization, bidi/hidden Unicode checks, layout guard, and pre‑commit hooks.

pytest -q

```## 3) Python env



## 4) ServiceNow dry‑run smoke (no network calls)```bash

```bashpython -m venv .venv && source .venv/bin/activate

ROOT="$(git rev-parse --show-toplevel)"pip install -r requirements.txt

bash "$ROOT/scripts/bootstrap.sh"   # default SNOW_DRY_RUN=1pytest -q

head -n 40 "$ROOT/reports/tickets/snow_incidents.json" || true```

```

## 4) ServiceNow dry‑run smoke (no network calls)

## 5) War Room UI (optional local preview)

```bash```bash

cd ui/psyops-war-roomROOT="$(git rev-parse --show-toplevel)"

npm ibash "$ROOT/scripts/bootstrap.sh"   # default SNOW_DRY_RUN=1

npm run previewhead -n 40 "$ROOT/reports/tickets/snow_incidents.json" || true

``````



## 6) Real ServiceNow calls (opt‑in; guarded)## 5) War Room UI (optional local preview)

```bash

export SNOW_INSTANCE="acme"          # or https://acme.service-now.com```bash

export SNOW_OAUTH_TOKEN="REDACTED"   # or SNOW_USER/SNOW_PASScd ui/psyops-war-room

export SNOW_DRY_RUN=0npm i

bash scripts/bootstrap.shnpm run preview

``````

## 7) Useful Make targets## 6) Real ServiceNow calls (opt‑in; guarded)

```bash

make repo-hygiene               # normalize + checks```bash

make drift-report-local         # branch drift report (local)export SNOW_INSTANCE="acme"          # or https://acme.service-now.com

make snow-bridge ENV=PROD       # safe, dry‑run path via bootstrapexport SNOW_OAUTH_TOKEN="REDACTED"   # or SNOW_USER/SNOW_PASS

make snow-bridge-prod ENV=PROD  # real run (requires SNOW_* env)export SNOW_DRY_RUN=0

```bash scripts/bootstrap.sh

```

## 7) Useful Make targets

```bash
make repo-hygiene             # normalize + checks
make drift-report-local       # branch drift report (local)
make snow-bridge ENV=PROD     # safe, dry‑run path via bootstrap
make snow-bridge-prod ENV=PROD  # real run (requires SNOW_* env)
```
