import os
import json
import boto3

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, RedirectResponse
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
    if meta.get("status") != "completed":
        raise HTTPException(423, "Task not completed yet")

    filename = meta.get("filename")
    if not filename:
        raise HTTPException(404, "Filename missing in task metadata")

    if meta.get("s3", False):
        s3_key = f"processed/{filename}"

        try:
            s3 = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )

            presigned_url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": settings.AWS_S3_BUCKET,
                    "Key": s3_key,
                    "ResponseContentDisposition": f'attachment; filename="{filename}"'
                },
                ExpiresIn=3600,
            )

            return RedirectResponse(presigned_url)
        except Exception as e:
            raise HTTPException(500, f"Error generating S3 URL: {str(e)}")

    # If not S3, return local file
    local_path = os.path.join(settings.OUTPUT_DIR, filename)
    if not os.path.exists(local_path):
        raise HTTPException(404, "File missing from local storage")

    return FileResponse(local_path, filename=filename)
