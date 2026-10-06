# Administration

Start with [DEPLOYMENT.md](DEPLOYMENT.md) and [SECURITY.md](SECURITY.md).

## Protected endpoints

`GET /profiles` and every `/model/*` management endpoint require `Authorization: Bearer ADMIN_API_KEY`. Without a key of at least 32 characters, they return 503. A missing or incorrect supplied key returns 401.

Generate a random key locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Keep it in backend configuration; never put it in Vite variables, a public issue, or source control. Rotate it by replacing the environment value and restarting the backend. Do not log Authorization headers.

## Profile recovery

Legacy JSON records are imported once into SQLite and remain private until a token is issued. On the trusted server, run:

```bash
python scripts/restore_profile_access.py PROFILE_UUID
```

Deliver the resulting access code privately to its owner. Existing codes stop working after rotation. A device access code cannot access a different profile. The dashboard supports server-data deletion and local draft/checklist cleanup.

## Models

Bundled artifacts are the fallback. Compatible locally retrained artifacts are loaded from `models/`. Older feature schemas are rejected rather than activated. Current input features exclude target-derived confidence and skill gaps.

Train a candidate with `python training.py --output .run/model-candidate`. Review its evaluation and provenance before updating artifacts. The optional server retrainer writes versions and activates the trained model; therefore enabling retraining is an administrative action, not a passive monitoring feature.

Keep automatic retraining off for the default release. There is no real-time labor-market feed; `MARKET_WEIGHT=0` excludes mock market information.

## Storage and monitoring

SQLite transactions preserve concurrent assessments and deduplicate repeated assessment IDs. Back up with SQLite's backup API and test recovery. Logs contain request paths/status/timing and client addresses, but should not contain tokens or assessment bodies. `/health` reports whether the main components are initialized; it is not a full database integrity check.
