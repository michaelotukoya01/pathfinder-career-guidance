"""Vercel entrypoint: /api is Python; public/ is served from the CDN."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# These are disposable model-work directories, never profile storage. Production
# profiles must use DATABASE_URL so cold starts cannot erase assessment history.
if os.getenv("VERCEL"):
    os.environ["MODEL_STORAGE_DIR"] = "/tmp/pathfinder-models"
    os.environ["TRAINING_DATA_DIR"] = "/tmp/pathfinder-training"
    os.environ["ENABLE_RETRAINING_SCHEDULER"] = "false"
    os.environ.pop("ADMIN_API_KEY", None)

if os.getenv("VERCEL") and not os.getenv("DATABASE_URL"):
    # Fail closed for data operations, while leaving the frontend available.
    career_api = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @career_api.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def database_not_configured(path: str):
        return JSONResponse(status_code=503, content={
            "detail": "Cloud database setup is pending. Please try again after setup is complete."
        }, headers={"Cache-Control": "no-store"})
else:
    from main import app as career_api


@asynccontextmanager
async def lifespan(app):
    async with career_api.router.lifespan_context(career_api):
        yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", career_api)


class FrontendFiles(StaticFiles):
    async def get_response(self, path, scope):
        if path in {".", "", "dashboard", "guide"}:
            path = "index.html"
        return await super().get_response(path, scope)


# Also serve generated assets from the application when Vercel's static-file
# discovery occurs before the frontend build has created public/.
public_dir = Path(__file__).resolve().parent / "public"
if public_dir.is_dir():
    app.mount("/", FrontendFiles(directory=public_dir, html=True))
