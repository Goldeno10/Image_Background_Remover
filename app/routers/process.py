




import uuid
import secrets
from fastapi import (
    APIRouter,
    Request,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    HTTPException,
    Depends,
    status
)
from fastapi.responses import JSONResponse
from fastapi_limiter.depends import RateLimiter
from pydantic import EmailStr, ValidationError

from ..models import ProcessingRequest
from ..tasks import enqueue_image_processing
from ..config import settings

router = APIRouter(prefix="/process", tags=["process"])

# Use constants from settings if possible, otherwise define clearly
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MiB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_MODELS = set(settings.MODEL_NAMES) if hasattr(settings, "MODEL_NAMES") else {"u2net", "u2netp", "u2net_human"}

@router.post(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[
        Depends(RateLimiter(times=1, seconds=15)),
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
    quality: int = Form(95, ge=1, le=100), # Inline validation
    scale: float = Form(1.0, gt=0, le=2.0), # Prevent extreme CPU usage
):
    # 1) Early validation of file extension (cheap check)
    extension = file.filename.split(".")[-1].lower() if file.filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Supported: {ALLOWED_EXTENSIONS}"
        )

    # 2) Early validation of Model Selection
    if model not in ALLOWED_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model. Choose from: {list(ALLOWED_MODELS)}"
        )

    # 3) Validate File Size without reading it all into memory at once
    # We check the actual size of the spool file created by FastAPI/Starlette
    size = 0
    file.file.seek(0, 2) # Move to end of file
    size = file.file.tell() # Get current position (size)
    file.file.seek(0) # Reset to beginning for reading
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({size} bytes). Maximum size is {MAX_FILE_SIZE} bytes."
        )

    # 4) Build Pydantic model (and catch validation errors early)
    try:
        pr = ProcessingRequest(
            email=email,
            model=model,
            output_format=output_format.lower(),
            quality=quality,
            scale=scale,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    # 5) Read file bytes now that we know it is safe
    file_bytes = await file.read()

    # 6) Generate a secure unique ID and Enqueue
    # Using secrets or uuid4 is better than relying on task internal IDs
    task_id = str(uuid.uuid4())
    
    enqueue_image_processing(
        background_tasks,
        pr, 
        file_bytes,
        file.filename,
        task_id=task_id, # Pass the generated ID
        base_url=str(request.base_url)
    )

    # 7) Build clean response URLs
    # Use request.url_for if your routes are named for better maintainability
    status_url = f"{request.base_url}status/{task_id}"
    
    return {
        "processing_id": task_id,
        "status_url": status_url,
        "message": "Image received and queued for processing.",
        "estimated_wait": "Check your email or status URL in a few moments."
    }



# # app/routers/process.py

# from fastapi import (
#     APIRouter,
#     Request,
#     UploadFile,
#     File,
#     Form,
#     BackgroundTasks,
#     HTTPException,
#     Depends,
# )
# from fastapi.responses import JSONResponse
# from fastapi_limiter.depends import RateLimiter
# from pydantic import EmailStr

# from ..models import ProcessingRequest
# from ..tasks import enqueue_image_processing


# router = APIRouter(prefix="/process", tags=["process"])

# MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MiB

# @router.post(
#     "/",
#     status_code=202,
#     dependencies=[
#         # Burst: max 1 call per 15 seconds
#         Depends(RateLimiter(times=1, seconds=15)),
#         # Steady: max 5 calls per 60 seconds
#         Depends(RateLimiter(times=5, seconds=60)),
#     ],
# )
# async def create_task(
#     request: Request,
#     background_tasks: BackgroundTasks,
#     file: UploadFile = File(...),
#     email: EmailStr = Form(...),
#     model: str = Form("u2net"),
#     output_format: str = Form("png"),
#     quality: int = Form(95),
#     scale: float = Form(1.0),
# ):
#     # 1) Build Pydantic model
#     pr = ProcessingRequest(
#         email=email,
#         model=model,
#         output_format=output_format,
#         quality=quality,
#         scale=scale,
#     )

#     # 2) Read & enforce size limit
#     file_bytes = await file.read()
#     if len(file_bytes) > MAX_FILE_SIZE:
#         raise HTTPException(413, "File too large. Maximum size is 5 MB.")

#     # 3) Enqueue background job
#     task_id = enqueue_image_processing(
#         background_tasks,
#         pr, file_bytes,
#         file.filename,
#         base_url=str(request.base_url)
#     )

#     # 4) Return status URL
#     status_url = str(request.base_url) + f"status/{task_id}"
#     return JSONResponse({
#         "processing_id": str(task_id),
#         "status_url": status_url,
#         "message": "Processing started. Check your email when done.",
#     })

