import os
import json
import uuid
import logging
from fastapi import BackgroundTasks
from .redis_client import redis_client
from .models import ProcessingRequest
from app.services.image_processor import process_image_bytes
from app.services.storage import build_filepath
from app.services.email_notifier import send_notification
from app.services.s3_uploader import upload_to_s3
from app.config import settings

# Setup logging to track background failures
logger = logging.getLogger("uvicorn.error")

def enqueue_image_processing(
    bg: BackgroundTasks,
    request: ProcessingRequest,
    file_bytes: bytes,
    filename: str,
    task_id: str, # Received from router
    base_url: str,
):
    """
    Enqueues the task. task_id is now generated in the router 
    to ensure the user gets a valid URL immediately.
    """
    processing_id = task_id or str(uuid.uuid4())
    
    # Pass the task to the background worker
    bg.add_task(
        _background_task, 
        processing_id, 
        request, 
        file_bytes, 
        filename, 
        base_url
    )
    return processing_id


def _background_task(
    processing_id: str, 
    request: ProcessingRequest, 
    file_bytes: bytes, 
    filename: str, 
    base_url: str
):
    """
    The heavy lifter. Runs in a separate thread/process managed by FastAPI.
    """
    public_url = None
    
    # 1) Initialize State in Redis
    state = {
        "status": "processing", 
        "email": request.email,
        "model": request.model,
        "original_name": filename
    }
    redis_client.setex(
        str(processing_id), 
        settings.REDIS_TTL_SECONDS, 
        json.dumps(state)
    )

    try:
        # 2) Process Image (AI logic)
        # result_img is a PIL Image object returned by our improved processor
        result_img = process_image_bytes(file_bytes, request.model, request.scale)

        # 3) Determine Save Format and Filepath
        ext = request.output_format.lower().strip(".")
        filepath = build_filepath(processing_id, ext)

        save_kwargs = {}
        
        # Handle Format-specific requirements
        if ext in ("jpg", "jpeg"):
            # JPEG doesn't support Alpha channel; convert to RGB
            if result_img.mode in ("RGBA", "LA"):
                result_img = result_img.convert("RGB")
            save_kwargs["quality"] = request.quality
            save_kwargs["optimize"] = True # 2025 optimization
        elif ext == "webp":
            save_kwargs["quality"] = request.quality
            save_kwargs["lossless"] = False if request.quality < 100 else True

        # 4) Storage Logic (S3 vs Local)
        if settings.ENV == "production" and settings.AWS_USE_S3:
            s3_filename = f"processed/{processing_id}.{ext}"
            try:
                public_url = upload_to_s3(result_img, s3_filename, ext, save_kwargs)
                state.update({
                    "status": "completed",
                    "file_url": public_url,
                    "storage": "s3"
                })
            except Exception as e:
                logger.error(f"S3 Upload failed for {processing_id}: {str(e)}")
                raise RuntimeError(f"S3 upload failed: {str(e)}")
        else:
            # Local Storage
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            result_img.save(filepath, **save_kwargs)
            
            # Ensure base_url doesn't have a trailing slash for clean URLs
            clean_url = base_url.rstrip("/")
            public_url = f"{clean_url}/download/{processing_id}"
            
            state.update({
                "status": "completed",
                "file_url": public_url,
                "storage": "local"
            })

        # 5) Update Redis with success
        redis_client.setex(
            str(processing_id), 
            settings.REDIS_TTL_SECONDS, 
            json.dumps(state)
        )

        # 6) Notification (Non-blocking check)
        try:
            email_ok = send_notification(request.email, public_url)
            if not email_ok:
                logger.warning(f"Email failed to send to {request.email}")
                state["email_status"] = "failed"
                redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))
        except Exception as e:
            logger.error(f"Email service error: {str(e)}")

    except Exception as exc:
        # 7) Error Handling & Logging
        logger.error(f"Task {processing_id} failed: {str(exc)}")
        state.update({
            "status": "failed", 
            "error": "Internal processing error. Please try a different image."
        })
        redis_client.setex(
            str(processing_id), 
            settings.REDIS_TTL_SECONDS, 
            json.dumps(state)
        )


# import os
# import json
# import uuid
# from fastapi import BackgroundTasks
# from .redis_client import redis_client
# from .models import ProcessingRequest
# from app.services.image_processor import process_image_bytes
# from app.services.storage import build_filepath
# from app.services.email_notifier import send_notification
# from app.services.s3_uploader import upload_to_s3
# from app.config import settings


# def enqueue_image_processing(
#     bg: BackgroundTasks,
#     request: ProcessingRequest,
#     file_bytes: bytes,
#     filename: str = None,
#     base_url: str = None,
# ):
#     processing_id = uuid.uuid4()
#     bg.add_task(_background_task, processing_id, request, file_bytes, filename, base_url)
#     return processing_id


# def _background_task(processing_id, request: ProcessingRequest, file_bytes: bytes, filename: str, base_url: str = None):
#     if processing_id is None:
#         processing_id = uuid.uuid4()

#     public_url = None

#     # 1) mark as "processing"
#     state = {"status": "processing", "email": request.email}
#     redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))

#     try:
#         # 2) process image
#         result_img = process_image_bytes(file_bytes, request.model, request.scale)

#         # 3) save image
#         ext = request.output_format.lower()
#         filepath = build_filepath(processing_id, ext)

#         save_kwargs = {}
#         if ext in ("jpg", "jpeg"):
#             result_img = result_img.convert("RGB")
#             save_kwargs["quality"] = request.quality

#         if settings.ENV == "production" and settings.AWS_USE_S3:
#             s3_filename = f"processed/{processing_id}.{ext}"
#             try:
#                 public_url = upload_to_s3(result_img, s3_filename, ext, save_kwargs)
#                 state.update({
#                     "status": "completed",
#                     "filename": f"{processing_id}.{ext}",
#                     "file_url": public_url,
#                     "s3": True
#                 })
#             except Exception as e:
#                 state.update({"status": "failed", "error": f"S3 upload failed: {str(e)}"})
#                 redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))
#                 return
#         else:
#             result_img.save(filepath, **save_kwargs)
#             public_url = f"{base_url}/download/{processing_id}"
#             state.update({
#                 "status": "completed",
#                 "filename": os.path.basename(filepath),
#                 "file_url": public_url,
#                 "s3": False
#             })

#         # 4) mark as "completed" in Redis
#         redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))

#         # 5) send email notification
#         ok = send_notification(request.email, public_url)

#         if not ok:
#             state = json.loads(redis_client.get(str(processing_id)))
#             state["email_status"] = "failed"
#             redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))

#     except Exception as exc:
#         # 6) mark as "failed"
#         state.update({"status": "failed", "error": str(exc)})
#         redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))
#         raise
