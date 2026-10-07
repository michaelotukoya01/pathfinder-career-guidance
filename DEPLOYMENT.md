# Deployment

## Vercel with durable PostgreSQL storage

The root `vercel.json` builds the React frontend into `public/`, serves its assets
from Vercel's CDN, and runs the Python 3.13 API at `/api` on the same domain.
`/dashboard` and `/guide` support direct navigation and refresh.

1. Link the repository root to a Vercel project. Keep the root directory at `.`.
2. Provision a dedicated Neon database with the Free plan in `iad1`, and connect
   its `DATABASE_URL` to the project's **production** environment. Marketplace
   terms must be accepted by the account owner. Never put the URL in `VITE_*`.
3. Deploy with `vercel --prod`. Vercel installs pinned Python dependencies and
   builds the frontend; the API initializes its profile table in PostgreSQL.
4. Check `/api/health`, submit an assessment, save it, refresh the dashboard,
   restore access using a backup code, and delete the test profile.

Cloud profiles use PostgreSQL row locks to preserve simultaneous saves and
deduplicate retries. Local SQLite data is not uploaded automatically. Model
artifacts ship with the deployment; runtime retraining and admin endpoints are
disabled on Vercel because its temporary filesystem is not durable. Redeploy a
reviewed model to update recommendations. The application rate limiter is per
instance; use Vercel's firewall controls for deployment-wide traffic protection.

Preview deployments need their own database environment/branch if enabled; do
not connect unreviewed preview code to production profile data. Local development
continues to use SQLite when `DATABASE_URL` is unset. Keep database credentials
only in Vercel environment variables or ignored local environment files.

## Supported layout

The provided Compose configuration runs one FastAPI worker behind nginx on one host. SQLite is stored on a persistent named volume. This is appropriate for a small educational deployment; horizontal scaling requires additional work.

```bash
docker compose config --quiet
docker compose up --build --wait
```

Open http://localhost:3000. Test `/api/health`, `/guide`, an assessment, and saving history. Stop services with `docker compose down`; named volumes remain. Do not remove volumes unless you intend to delete saved data.

The configuration is included in CI container startup checks. A Docker engine was unavailable in the authoring environment, so a successful local container run has not been claimed.

## Public hosting

1. Put an HTTPS reverse proxy in front of the localhost frontend port. Configure your real domain and certificates with the host's supported process.
2. Keep the backend private. The bundled frontend nginx overwrites forwarded client addresses; the backend trusts that private proxy. If adding another proxy layer, configure trusted addresses explicitly so rate limiting reflects real clients rather than a shared proxy address.
3. Set an administrator key through backend environment configuration only if administrative HTTP access is needed. Unset admin access is disabled.
4. Use one backend worker. Rate limits and in-memory model references are process-local. Use shared rate limiting and coordinated model activation before scaling workers or replicas.
5. Back up the SQLite volume using SQLite's online backup API, not a live copy of only the main database file while WAL is active. Test restoration before relying on backups.
6. Keep the scheduler disabled until model evaluation and operations are reviewed. Never use uploaded pickle files as model inputs.

The service uses device credentials, not conventional user accounts. The backup code grants access to the profile; there is no email-based recovery. Review this product choice before inviting a large audience.

## Hosting services separately

Build the frontend with `VITE_API_URL` set to the HTTPS backend base URL, then serve `frontend/dist` from a static host with an SPA fallback to `index.html`. Set backend `CORS_ORIGINS` to the exact frontend origin. The nginx CSP in this repository assumes same-origin `/api`; adjust `connect-src` for a separate backend origin.

```bash
cd frontend
npm ci
npm run build
```

Run the backend with Python 3.13, the pinned `requirements.txt`, trusted model artifacts, and persistent `PROFILE_STORAGE_DIR`:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

Do not use the Vite development server or Uvicorn reload mode as a public production server. GitHub Pages alone cannot run the Python API.

## Optional explanations

The default image omits the optional Anthropic SDK. For this feature, build an explicitly reviewed image/environment with that SDK installed and set the backend API key. Explain the external transfer of assessment context to users before enabling it. Core recommendations remain available without it.

## Release checks

Run the commands in [README.md](README.md), inspect GitHub Actions, and test the deployed service with synthetic data. Retain the previous deployment and its matching model/preprocessor/encoder set for rollback. Visual browser checks and HTTPS checks should be performed against the actual deployment.
