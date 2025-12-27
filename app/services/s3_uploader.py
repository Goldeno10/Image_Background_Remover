import logging
from io import BytesIO
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from PIL import Image
from app.config import settings

# Initialize the logger
logger = logging.getLogger("uvicorn.error")

# 1. Persistent Client: Create the client at the module level (Global)
# This reuses the underlying connection pool across multiple uploads.
S3_CLIENT = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=getattr(settings, "AWS_REGION", "eu-north-1")
)

def upload_to_s3(
    img: Image.Image, 
    filename: str, 
    ext: str, 
    save_kwargs: dict
) -> Optional[str]:
    """
    Uploads a PIL Image to Amazon S3 with optimized buffering and error handling.
    """
    
    # 1. Early Environment Gate
    if not settings.AWS_USE_S3 or settings.ENV != "production":
        logger.info("S3 Upload bypassed: Local storage mode active.")
        return None

    # 2. Preparation of the Buffer
    buffer = BytesIO()
    try:
        # Standardize format naming (e.g., 'jpg' becomes 'JPEG')
        pil_format = "JPEG" if ext.lower() in ["jpg", "jpeg"] else ext.upper()
        img.save(buffer, format=pil_format, **save_kwargs)
        buffer.seek(0)
    except Exception as e:
        logger.error(f"Failed to serialize image for S3: {str(e)}")
        raise RuntimeError(f"Image serialization error: {e}")

    # 3. Dynamic Content Type Mapping
    # 'jpg' is technically 'image/jpeg' in MIME standards
    content_type = f"image/{'jpeg' if ext.lower() in ['jpg', 'jpeg'] else ext.lower()}"

    # 4. Perform the Upload
    try:
        S3_CLIENT.upload_fileobj(
            buffer,
            settings.AWS_S3_BUCKET,
            filename,
            ExtraArgs={
                "ContentType": content_type,
                # Optional: Uncomment if you want the file to be immediately 
                # downloadable via a browser link without signed URLs
                # "ACL": "public-read" 
            }
        )
    except ClientError as e:
        logger.error(f"Boto3 Client Error during upload of {filename}: {e.response['Error']['Message']}")
        return None
    except Exception as e:
        logger.error(f"Unexpected S3 failure for {filename}: {str(e)}")
        return None

    # 5. Build the Public URL
    # Using the standardized format for S3 URLs in 2025
    region = getattr(settings, "AWS_REGION", "eu-north-1")

    # public_url = f"https://{settings.AWS_S3_BUCKET}.s3.{region}.amazonaws.com/{filename}"

    # Optional: Generate a 1-hour secure link instead of a static URL
    public_url = S3_CLIENT.generate_presigned_url(
        'get_object',
        Params={'Bucket': settings.AWS_S3_BUCKET, 'Key': filename},
        ExpiresIn=3600 # 1 hour expiration
    )

    
    logger.info(f"Successfully uploaded {filename} to S3.")
    return public_url









# from io import BytesIO
# from PIL import Image
# import boto3
# from app.config import settings

# def upload_to_s3(img: Image.Image, filename: str, ext: str, save_kwargs: dict) -> str | None:
#     """
#     Uploads an image to S3 and returns the public URL if in production.
#     If not in production, returns None.
#     """
#     if settings.ENV != "production":
#         print("Skipping S3 upload because environment is not production.")
#         return None

#     # Save image to in-memory buffer
#     buffer = BytesIO()
#     img.save(buffer, format=ext.upper(), **save_kwargs)
#     buffer.seek(0)

#     # Create S3 client
#     s3 = boto3.client(
#         "s3",
#         aws_access_key_id=settings.AWS_ACCESS_KEY,
#         aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#         region_name="eu-north-1"
#     )

#     # Upload file
#     s3.upload_fileobj(
#         buffer,
#         settings.AWS_S3_BUCKET,
#         filename,
#         ExtraArgs={"ContentType": f"image/{ext}"}
#     )

#     # Return public URL if file is in a public folder like 'processed/'
#     public_url = f"https://{settings.AWS_S3_BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
#     return public_url

