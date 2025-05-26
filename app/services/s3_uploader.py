import boto3
import io
from app.config import settings

s3 = boto3.client("s3", region_name=settings.AWS_REGION)

def upload_to_s3(image, filename, ext, save_kwargs):
    buffer = io.BytesIO()
    image.save(buffer, format=ext.upper(), **save_kwargs)
    buffer.seek(0)
    
    s3.upload_fileobj(buffer, settings.AWS_S3_BUCKET, filename, ExtraArgs={'ContentType': f'image/{ext}'})
