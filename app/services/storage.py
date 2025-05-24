import os
from uuid import UUID
from app.config import settings

os.makedirs(settings.OUTPUT_DIR, exist_ok=True)


def build_filepath(processing_id: UUID, ext: str) -> str:
    filename = f"{processing_id}.{ext}"
    return os.path.join(settings.OUTPUT_DIR, filename)