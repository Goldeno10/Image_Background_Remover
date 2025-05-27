import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi_limiter.depends import RateLimiter
from ..redis_client import redis_client


router = APIRouter(
    prefix="/status",
    tags=["status"],
)

@router.get(
    "/{task_id}",
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
def get_status(task_id: str):
    raw = redis_client.get(task_id)
    if not raw:
        raise HTTPException(404, "Task not found or expired")

    data = json.loads(raw)

    response = {
        "processing_id": task_id,
        "status": data["status"],
    }

    if "error" in data:
        response["error"] = data["error"]

    if "filename" in data:
        response["filename"] = data["filename"]

    if "s3" in data:
        response["s3"] = data["s3"]

    if "email_status" in data:
        response["email_status"] = data["email_status"]

    response["file_url"] = data.get("file_url", None)
    return response

