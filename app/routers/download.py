import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..redis_client import redis_client
from ..config import settings
import json

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/{task_id}")
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