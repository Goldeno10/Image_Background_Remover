"""Download API for completed tasks"""

from fastapi.responses import RedirectResponse
import boto3

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

    if meta.get("s3"):
        s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_S3_BUCKET, 'Key': meta["filename"]},
            ExpiresIn=300
        )
        return RedirectResponse(url)

    filepath = os.path.join(settings.OUTPUT_DIR, meta["filename"])
    if not os.path.exists(filepath):
        raise HTTPException(404, "File missing")

    return FileResponse(filepath, filename=meta["filename"])




# import os
# import json

# from fastapi import APIRouter, HTTPException, Depends
# from fastapi.responses import FileResponse
# from fastapi_limiter.depends import RateLimiter

# from ..redis_client import redis_client
# from ..config import settings

# router = APIRouter(
#     prefix="/download",
#     tags=["download"],
# )

# @router.get(
#     "/{task_id}",
#     dependencies=[Depends(RateLimiter(times=20, seconds=60))],
# )
# def download(task_id: str):
#     raw = redis_client.get(task_id)
#     if not raw:
#         raise HTTPException(404, "Task not found or expired")

#     meta = json.loads(raw)
#     if meta["status"] != "completed":
#         raise HTTPException(423, "Not ready")

#     filepath = os.path.join(settings.OUTPUT_DIR, meta["filename"])
#     if not os.path.exists(filepath):
#         raise HTTPException(404, "File missing")

#     return FileResponse(filepath, filename=meta["filename"])
