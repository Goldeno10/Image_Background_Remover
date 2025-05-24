from fastapi import APIRouter, Request, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import EmailStr
from ..models import ProcessingRequest
from ..tasks import enqueue_image_processing

router = APIRouter(tags=["process"])

@router.post("/process", status_code=202)
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
    # build Pydantic model from form fields
    pr = ProcessingRequest(
        email=email,
        model=model,
        output_format=output_format,
        quality=quality,
        scale=scale,
    )

    # 2) read the bytes immediately
    file_bytes = await file.read()
    filename   = file.filename

    task_id = enqueue_image_processing(background_tasks, pr, file_bytes, filename)

    # now use request.base_url to build your status link
    status_url = str(request.base_url) + f"status/{task_id}"

    return JSONResponse(
        {
            "processing_id": str(task_id),
            "status_url": status_url,
            "message": "Processing started. Check your email when done.",
        }
    )

