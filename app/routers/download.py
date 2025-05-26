"""Download API for completed tasks"""

import os
import json

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi_limiter.depends import RateLimiter

from ..redis_client import redis_client
from ..config import settings

router = APIRouter(
    prefix="/download",
    tags=["download"],
)

@router.get(
    "/{task_id}",
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
def download(task_id: str):
    raw = redis_client.get(task_id)
    if not raw:
        raise HTTPException(404, "Task not found or expired")

    meta = json.loads(raw)
    if meta["status"] != "completed":
        raise HTTPException(423, "Not ready")

    filepath = os.path.join(settings.OUTPUT_DIR, meta["filename"])
    if not os.path.exists(filepath):
        raise HTTPException(404, "File missing")

    return FileResponse(filepath, filename=meta["filename"])
