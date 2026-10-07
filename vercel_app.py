"""Serve the existing API under /api; Vercel serves public/ from its CDN."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

# These are disposable model-work directories, never profile storage. Production
# profiles must use DATABASE_URL so cold starts cannot erase assessment history.
if os.getenv("VERCEL"):
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("Vercel deployment requires a persistent DATABASE_URL")
    os.environ["MODEL_STORAGE_DIR"] = "/tmp/pathfinder-models"
    os.environ["TRAINING_DATA_DIR"] = "/tmp/pathfinder-training"
    os.environ["ENABLE_RETRAINING_SCHEDULER"] = "false"
    os.environ.pop("ADMIN_API_KEY", None)

from main import app as career_api


@asynccontextmanager
async def lifespan(app):
    async with career_api.router.lifespan_context(career_api):
        yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/api", career_api)
