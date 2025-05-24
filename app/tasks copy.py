import json
import uuid
from fastapi import BackgroundTasks, UploadFile
from .redis_client import redis_client
from .models import ProcessingRequest, ProcessingStatus
from app.services.image_processor import process_image_bytes
from app.services.storage import build_filepath
from app.services.email_notifier import send_notification
from PIL import Image
import os
from app.config import settings


def enqueue_image_processing(
    bg: BackgroundTasks,
    request: ProcessingRequest,
    file_bytes: bytes,
    filename: str = None
):
    processing_id = uuid.uuid4()
    bg.add_task(_background_task, processing_id, request, file_bytes, filename)
    return processing_id


def _background_task(processing_id, request: ProcessingRequest, file_bytes: bytes, filename: str):
    # generate a uuid if not provided
    if processing_id is None:
        processing_id = uuid.uuid4()

    # 1) mark “processing”
    state = {"status": "processing", "email": request.email}
    redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))

    try:
        # 2) do the removal
        result_img = process_image_bytes(file_bytes, request.model, request.scale)

        # 3) save
        ext = request.output_format.lower()
        filepath = build_filepath(processing_id, ext)

        save_kwargs = {}
        if ext in ("jpg", "jpeg"):
            result_img = result_img.convert("RGB")
            save_kwargs["quality"] = request.quality

        result_img.save(filepath, **save_kwargs)

        # 4) mark “completed”
        state.update({
            "status": "completed",
            "filename": os.path.basename(filepath)
        })
        redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))

        # 5) send email
        # ok = send_notification(str(processing_id), request.email)
        # if not ok:
        #     # optional: update Redis with a "warning" field
        #     state = json.loads(redis_client.get(str(processing_id)))
        #     state["email_status"] = "failed"
        #     redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))

    except Exception as exc:
        # mark “failed”
        state.update({"status": "failed", "error": str(exc)})
        redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(state))
        raise


# def _background_task(
#     processing_id,
#     request: ProcessingRequest,
#     file: UploadFile
# ):
#     # mark as processing
#     status = {"status": "processing", "email": request.email}
#     redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(status))

#     try:
#         data = file.file.read()  # sync read
#         result_img = process_image_bytes(data, request.model, request.scale)

#         # prepare save args
#         save_kwargs = {}
#         if request.output_format.lower() in ("jpg", "jpeg"):
#             result_img = result_img.convert("RGB")
#             save_kwargs["quality"] = request.quality

#         path = build_filepath(str(processing_id), request.output_format)
#         result_img.save(path, **save_kwargs)

#         # mark success
#         status.update({"status": "completed", "filename": os.path.basename(path)})
#         redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(status))

#         # notify
#         send_notification(str(processing_id), request.email)

#     except Exception as ex:
#         status.update({"status": "failed", "error": str(ex)})
#         redis_client.setex(str(processing_id), settings.REDIS_TTL_SECONDS, json.dumps(status))
#         raise

