from rembg import remove, new_session
from PIL import Image
import numpy as np
from io import BytesIO
import torch
from app.config import settings

# Initialize sessions once
SESSIONS = {
    name: new_session(name)
    for name in settings.MODEL_NAMES
}

if settings.GPU_ENABLED:
    for sess in SESSIONS.values():
        sess = sess.to("cuda")


def process_image_bytes(
    data: bytes,
    model_name: str,
    scale: float,
) -> Image.Image:
    img = Image.open(BytesIO(data))
    # optional scaling
    if scale != 1.0:
        img = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.LANCZOS
        )

    session = SESSIONS.get(model_name, SESSIONS["u2net"])
    if settings.GPU_ENABLED:
        session = session.to("cuda")

    result_np = remove(np.array(img), session=session)
    return Image.fromarray(result_np)