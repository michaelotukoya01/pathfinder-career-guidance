# Deployment

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
