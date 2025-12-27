import os
from app.config import settings


if settings.ENV != "production" or not settings.AWS_USE_S3:
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)


def build_filename(processing_id: str, ext: str) -> str:
    return f"{processing_id}.{ext}"


def build_filepath(processing_id: str, ext: str) -> str:
    """
    Returns the full file path for saving locally (used in dev mode).
    """
    filename = build_filename(processing_id, ext)
    return os.path.join(settings.OUTPUT_DIR, filename)


def build_s3_key(processing_id: str, ext: str) -> str:
    """
    Returns the S3 key (i.e., object path) where the file should be stored in S3.
    """
    filename = build_filename(processing_id, ext)
    return f"processed/{filename}"


# import os
# from uuid import UUID
# from app.config import settings

# os.makedirs(settings.OUTPUT_DIR, exist_ok=True)


# def build_filepath(processing_id: UUID, ext: str) -> str:
#     filename = f"{processing_id}.{ext}"
#     return os.path.join(settings.OUTPUT_DIR, filename)