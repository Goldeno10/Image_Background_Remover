import os
import json
import boto3
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi_limiter.depends import RateLimiter
from botocore.exceptions import ClientError

from ..redis_client import redis_client
from ..config import settings

logger = logging.getLogger("uvicorn.error")

# 1. Global S3 Client (Reusable Connection Pool)
S3_CLIENT = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

router = APIRouter(
    prefix="/download",
    tags=["download"],
)

@router.get(
    "/{task_id}",
    dependencies=[Depends(RateLimiter(times=20, seconds=60))],
)
async def download_image(task_id: str):
    """
    Directs the user to the final image. 
    Uses S3 Presigned URLs for production or Local FileResponse for dev.
    """
    raw = redis_client.get(task_id)
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Download link expired or invalid."
        )

    meta = json.loads(raw) # type: ignore
    current_status = meta.get("status")

    # 2. Handle non-ready states
    if current_status == "processing":
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED, 
            detail="Image is still being processed. Please refresh in a few seconds."
        )
    elif current_status == "failed":
        raise HTTPException(
            status_code=status.HTTP_410_GONE, 
            detail=f"Processing failed: {meta.get('error', 'Unknown error')}"
        )

    filename = meta.get("filename")
    if not filename:
        raise HTTPException(status_code=404, detail="File metadata missing.")

    # 3. S3 Download Logic (Secure Redirect)
    if meta.get("s3", False):
        try:
            # Generate a URL that allows the user to download the private S3 object
            # without making the whole bucket public.
            presigned_url = S3_CLIENT.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": settings.AWS_S3_BUCKET,
                    "Key": f"processed/{filename}",
                    # This forces the browser to download the file instead of just showing it
                    "ResponseContentDisposition": f'attachment; filename="MIBTech_{filename}"'
                },
                ExpiresIn=3600, # URL expires in 1 hour
            )
            return RedirectResponse(url=presigned_url)
            
        except ClientError as e:
            logger.error(f"AWS S3 Error: {e}")
            raise HTTPException(status_code=500, detail="Secure storage provider error.")

    # 4. Local Download Logic
    local_path = os.path.join(settings.OUTPUT_DIR, filename)
    if not os.path.exists(local_path):
        logger.warning(f"File {filename} missing from local disk despite Redis 'completed' status.")
        raise HTTPException(status_code=404, detail="Local file no longer exists.")

    return FileResponse(
        path=local_path, 
        filename=f"MIBTech_{filename}",
        media_type="image/png" # Standard for bg-removed images
    )

