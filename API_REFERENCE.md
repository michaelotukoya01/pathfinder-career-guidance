# API reference

Interactive OpenAPI documentation is available at `/docs`. Local base URL: `http://127.0.0.1:8000`. The frontend reverse proxy exposes the same routes under `/api`.

## Recommendations

| Method / path | Access | Behavior |
| --- | --- | --- |
| `GET /health` | Public | Component initialization status |
| `POST /recommend` | Public | Recommended career, top three scores, skill gaps, recency details |
| `POST /recommend?include_explanation=true` | Public | Same result, with optional external explanation |
| `POST /explain` | Public | Explanation for a valid assessment |

Use `test_input.json` as a complete synthetic request example. Technical skills accept decimals from 0 to 5. Academic, interest, preference, and personality ratings are integers from 1 to 5. Recency dates are optional. `confidence_score` and `skill_gaps` remain accepted for compatibility/context but do not influence the release classifier.

## Profiles

`POST /profiles` accepts optional background fields and returns `{id, access_token, message}`. Store the random token securely; it is only returned at creation. The server stores its hash.

All routes below require `Authorization: Bearer <profile access token>`:

| Method / path | Behavior |
| --- | --- |
| `GET /profiles/{id}` | Background and complete saved history; excludes token hashes |
| `PUT /profiles/{id}` | Merge validated background fields |
| `DELETE /profiles/{id}` | Delete profile and its legacy JSON file, if present |
| `POST /profiles/{id}/assessments` | Append an assessment; repeat IDs are idempotent |
| `GET /profiles/{id}/assessments?limit=50` | Newest-first history, limit 1–1000 |

Save the same client-generated assessment ID when retrying a failed request. Different assessment IDs create different records. Server timestamps are authoritative. Explanation and recency details are preserved.

## Administration

These routes require the separate administrator key:

- `GET /profiles?limit=100&offset=0`
- `GET /model/versions`
- `POST /model/retrain?force=false`
- `POST /model/promote/{version_id}`
- `POST /model/scheduler/start`
- `POST /model/scheduler/stop`

## Errors and limits

Missing/wrong profile credentials: 401. Unknown profile: 404. Invalid input: 422. Request body above 1 MiB: 413. Rate limit: 429 with `Retry-After`. Admin configuration missing: 503. Storage failure: 500.

The default rate limit is 30 requests per minute per client IP in one API process. Production proxy configuration must preserve trustworthy client addresses. JSON responses use `Cache-Control: no-store`.
