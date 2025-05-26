# app/routers/process.py

from fastapi import APIRouter, Request, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter
from pydantic import EmailStr

from ..models import ProcessingRequest
from ..tasks import enqueue_image_processing

router = APIRouter(prefix="/process", tags=["process"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MiB

@router.post(
    "/",
    status_code=202,
    dependencies=[
        # Burst: max 1 call per 15 seconds
        Depends(RateLimiter(times=1, seconds=15)),
        # Steady: max 5 calls per 60 seconds
        Depends(RateLimiter(times=5, seconds=60)),
    ],
)
async def create_task(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    email: EmailStr = Form(...),
    model: str = Form("u2net"),
    output_format: str = Form("png"),
    quality: int = Form(95),
    scale: float = Form(1.0),
):
    # 1) Build Pydantic model
    pr = ProcessingRequest(
        email=email,
        model=model,
        output_format=output_format,
        quality=quality,
        scale=scale,
    )

    # 2) Read & enforce size limit
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large. Maximum size is 5 MB.")

    # 3) Enqueue background job
    task_id = enqueue_image_processing(background_tasks, pr, file_bytes, file.filename)

    # 4) Return status URL
    status_url = str(request.base_url) + f"status/{task_id}"
    return JSONResponse({
        "processing_id": str(task_id),
        "status_url": status_url,
        "message": "Processing started. Check your email when done.",
    })

