from io import BytesIO
from PIL import Image
import boto3
from app.config import settings

def upload_to_s3(img: Image.Image, filename: str, ext: str, save_kwargs: dict) -> str | None:
    """
    Uploads an image to S3 and returns the public URL if in production.
    If not in production, returns None.
    """
    if settings.ENV != "production":
        print("Skipping S3 upload because environment is not production.")
        return None

    # Save image to in-memory buffer
    buffer = BytesIO()
    img.save(buffer, format=ext.upper(), **save_kwargs)
    buffer.seek(0)

    # Create S3 client
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name="eu-north-1"
    )

    # Upload file
    s3.upload_fileobj(
        buffer,
        settings.AWS_S3_BUCKET,
        filename,
        ExtraArgs={"ContentType": f"image/{ext}"}
    )

    # Return public URL if file is in a public folder like 'processed/'
    public_url = f"https://{settings.AWS_S3_BUCKET}.s3.eu-north-1.amazonaws.com/{filename}"
    return public_url

