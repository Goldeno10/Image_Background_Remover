import os
from io import BytesIO
from typing import Dict

import numpy as np
from PIL import Image, ImageOps
from rembg import remove, new_session
from app.config import settings


# 1. Set the model path before the sessions are initialized
os.environ["U2NET_HOME"] = getattr(settings, "U2NET_HOME", os.path.join(os.getcwd(), "models"))

# 2. Lazy Loading: Don't load all models into RAM at startup. 
# Load them only when first requested to save memory.
SESSIONS: Dict = {}

def get_session(model_name: str):
    """Retrieves or initializes a rembg session."""
    if model_name not in SESSIONS:
        # Fallback to u2net if the requested model isn't in your config
        target_model = model_name if model_name in settings.MODEL_NAMES else "u2net"
        SESSIONS[target_model] = new_session(target_model)
    return SESSIONS[target_model] # type: ignore

def process_image_bytes(
    data: bytes,
    model_name: str,
    scale: float,
) -> Image.Image:
    """
    Processes an image to remove background with optimizations for 
    memory and orientation.
    """
    try:
        # Load image and fix orientation (EXIF data often rotates mobile photos)
        input_image = Image.open(BytesIO(data))
        input_image = ImageOps.exif_transpose(input_image)
        
        # Convert to RGB/RGBA if not already to prevent rembg failures
        if input_image.mode not in ("RGB", "RGBA"):
            input_image = input_image.convert("RGB")

        # Optional scaling using Resampling.LANCZOS (modern Pillow syntax)
        if scale != 1.0:
            new_size = (int(input_image.width * scale), int(input_image.height * scale))
            input_image = input_image.resize(new_size, Image.Resampling.LANCZOS)

        # Get the specific session lazily
        session = get_session(model_name)

        # Process: rembg can take the PIL object directly in many versions,
        # but converting to numpy is the most stable approach.
        result_np = remove(np.array(input_image), session=session)
        
        return Image.fromarray(result_np)
        
    except Exception as e:
        # Log the error appropriately in your production logs
        print(f"Error processing image: {e}")
        raise e



# from rembg import remove, new_session
# from PIL import Image
# import numpy as np
# from io import BytesIO
# from app.config import settings

# # Initialize sessions once
# SESSIONS = {
#     name: new_session(name)
#     for name in settings.MODEL_NAMES
# }

# # if settings.GPU_ENABLED:
# #     for sess in SESSIONS.values():
# #         sess = sess.to("cuda")


# def process_image_bytes(
#     data: bytes,
#     model_name: str,
#     scale: float,
# ) -> Image.Image:
#     img = Image.open(BytesIO(data))
#     # optional scaling
#     if scale != 1.0:
#         img = img.resize(
#             (int(img.width * scale), int(img.height * scale)),
#             Image.LANCZOS
#         )

#     session = SESSIONS.get(model_name, SESSIONS["u2net"])
#     # if settings.GPU_ENABLED:
#     #     session = session.to("cuda")

#     result_np = remove(np.array(img), session=session)
#     return Image.fromarray(result_np)