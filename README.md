# Pathfinder — AI Career Recommendation & Guidance

Explore technology careers through a guided self-assessment, understand skill gaps, and turn your results into practical learning milestones.

**React + Vite · FastAPI · scikit-learn · SQLite · English / Spanish**

Pathfinder is an educational portfolio project built around a synthetic dataset. It supports career exploration; it has not been validated for hiring, admissions, aptitude testing, or predicting career success.

## What you can do

- Complete six guided sections covering background, knowledge, skills, interests, preferences, and working style.
- Resume a browser draft, edit answers, and optionally account for when you last used a skill.
- Compare three career matches and your skills against dataset averages.
- Follow project ideas, provider-owned learning references, and saved learn/build/reflect checklists.
- Keep private history using a device access code; restore access, download results, or delete saved data.
- Track actual skill observations over time, without invented progress points.
- Use responsive layouts, keyboard controls, visible focus, reduced-motion support, and English/Spanish translations.

## Run locally

Use **Python 3.13** and **Node.js 24**. Download this repository, or clone its URL, and open a terminal in the project directory.

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

```bash
# macOS / Linux
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

In a second terminal:

```bash
cd frontend
npm ci
npm start
```

Open **http://localhost:3000**. Vite proxies `/api` to `127.0.0.1:8000`. API documentation is at **http://127.0.0.1:8000/docs**.

The bundled model works without an API key. Runtime dependencies are pinned; plotting and notebook tools are optional in `requirements-research.txt`.

## Docker

With Docker Engine and Compose installed:

```bash
docker compose up --build --wait
```

Open http://localhost:3000. Compose runs a non-root API container and a frontend reverse proxy. Named volumes preserve profiles and locally retrained models. Stopping the services preserves those volumes; removing the volumes deletes their data.

Services bind only to localhost by default. See [DEPLOYMENT.md](DEPLOYMENT.md) for HTTPS, storage, and deployment limits. Container startup is checked by CI; the authoring environment did not provide a Docker engine for a local run.

## Configuration

Copy `.env.example` to `.env` for custom backend settings. `frontend/.env.example` documents the optional Vite override. Never commit credentials or put server secrets in a `VITE_` variable; frontend variables are public build-time values.

| Variable | Default | Purpose |
| --- | --- | --- |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | Used by `python main.py` |
| `CORS_ORIGINS` | Local frontend origins | Comma-separated allowed origins |
| `PROFILE_STORAGE_DIR` | `profiles` | SQLite database and legacy import directory |
| `ADMIN_API_KEY` | Unset | Random key of at least 32 characters; enables admin endpoints |
| `ENABLE_RETRAINING_SCHEDULER` | `false` | Opt-in background retraining |
| `MARKET_WEIGHT` | `0` | Mock market influence; keep zero for the standard demo |
| `VITE_API_URL` | `/api` | Frontend API base URL, set before building |
| `ANTHROPIC_API_KEY` | Unset | Optional explanations; requires the separate `anthropic` SDK |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Optional explanation model |

For local AI-written explanations, install `anthropic` into the backend environment and set `ANTHROPIC_API_KEY`. Recommendations, charts, projects, and history work without it. The default Docker image includes the core service only.

## Private history and recovery

Creating a profile returns a random device token. The browser stores it locally; SQLite stores only its SHA-256 hash. Reading, changing, saving to, or deleting a profile requires that token. Profile listing and model administration require a separate admin key. This is **device-based access**, not email/password authentication.

Use **Dashboard → Download private access backup** before changing browsers. Anyone holding the backup can access that profile. **Restore access** accepts its profile ID and token. Deleting saved data removes the server profile, its legacy JSON backup if present, and this browser's draft and learning checklist.

Existing JSON profiles are imported without changing their source files. Older profiles need a device token issued by a trusted local administrator:

```bash
python scripts/restore_profile_access.py PROFILE_UUID
```

Paste the output into **Dashboard → Restore access**. This rotates access; keep its output private. See [SECURITY.md](SECURITY.md).

## Model quality

The release uses **45 input features**, 500 synthetic records, and 12 technology careers. The generator derives `skill_gaps` and `confidence_score` from the target; both are excluded from training and inference. The confidence slider is retained only as profile context.

| Metric | Release result |
| --- | ---: |
| Training / test records | 400 / 100 |
| Held-out top-choice accuracy | 45% |
| Held-out top-three accuracy | 79% |
| Held-out macro F1 | 0.4013 |
| Majority-class baseline accuracy | 18% |
| Training-only 5-fold CV macro F1 | 0.3461 |

Preprocessing is fitted independently inside each training fold. Regularization is chosen on training data; the test split is excluded from fitting and parameter selection. The historical split was inspected during earlier development, so independent real-world validation is still needed. Scores are uncalibrated and do not estimate employment success.

The previous 54% result used target-derived inputs and preprocessing fitted before splitting. It is not comparable to this release. See [MODEL_CARD.md](MODEL_CARD.md) and [evaluation data](docs/model_evaluation.json) for per-class metrics, confusion matrix, hashes, and limitations.

Reproduce training without overwriting the shipped artifacts:

```bash
python training.py --output .run/model-candidate
```

`baseline_model.py` and `data_preprocessing.py` delegate to this pipeline. Review candidates before replacing bundled artifacts or promoting a server model. Never load pickle/joblib files supplied by unknown parties.

## Verification

```bash
python -m unittest discover -s tests -v
python scripts/check_repository.py
python -m pip install -r requirements-dev.txt
python -m pip_audit -r requirements.txt
```

```bash
cd frontend
npm run lint
npm test
npm run build
npm audit --audit-level=high
```

GitHub Actions runs these checks and container startup checks on pushes and pull requests. The repository checker examines tracked files: stage or commit before running it on a new repository. Its common-secret scan is a guardrail, not a complete security audit.

## Project map

| Path | Responsibility |
| --- | --- |
| `frontend/src/` | Assessment, results, dashboard, learning plans, localization |
| `main.py` | API, validation, inference, profile and admin access |
| `profile_store.py` | SQLite transactions, idempotent saves, legacy import |
| `training.py` | Cross-validation, evaluation, model export |
| `model_retraining.py` | Explicit model administration and optional scheduler |
| `tests/` | Backend regression, privacy, persistence and concurrency coverage |
| `docs/model_evaluation.json` | Release metrics and artifact hashes |
| `.github/workflows/ci.yml` | Automated release checks |

Historical research notes, plots, exploratory scripts, and the synthetic generator remain for context. Only the documented commands and `tests/` suite are part of the maintained release workflow.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under [MIT](LICENSE). External learning resources remain the property of their publishers.
