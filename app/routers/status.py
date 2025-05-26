from fastapi import APIRouter, HTTPException, Depends
from fastapi_limiter.depends import RateLimiter
from ..redis_client import redis_client
import json

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
    return {"processing_id": task_id, "status": data["status"]}
