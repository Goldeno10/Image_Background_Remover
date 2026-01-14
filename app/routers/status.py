import json
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from ..redis_client import redis_client


logger = logging.getLogger("uvicorn.error")

router = APIRouter(
    prefix="/status",
    tags=["status"],
)

@router.get(
    "/{task_id}",
    dependencies=[Depends(RateLimiter(times=60, seconds=60))],
)
async def get_status(task_id: str):
    """
    Retrieves the current state of an image processing task from Redis.
    """
    try:
        # redis_client is used directly; ensure it's the sync or async version 
        # consistent with your redis_client.py definition.
        raw = redis_client.get(task_id)
        
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Task not found or has expired from the cache."
            )

        data = json.loads(raw) # type: ignore

        # Build a clean, structured response
        return {
            "processing_id": task_id,
            "status": data.get("status", "unknown"),
            "progress": {
                "model_used": data.get("model"),
                "email_notified": data.get("email_status") == "sent",
            },
            "result": {
                "file_url": data.get("file_url"),
                "filename": data.get("filename"),
                "storage_provider": "s3" if data.get("s3") else "local"
            },
            "error": data.get("error") # Only present if status is 'failed'
        }

    except json.JSONDecodeError:
        logger.error(f"Malformed metadata in Redis for task {task_id}")
        raise HTTPException(status_code=500, detail="Internal metadata corruption.")
    except Exception as e:
        logger.error(f"Unexpected error fetching status: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve task status.")
