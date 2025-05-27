import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

def upload_file(local_file_path: str, s3_folder: str, filename: str) -> str:
    """
    Uploads a file to S3 and returns the full S3 key.
    """
    s3_key = f"{s3_folder.rstrip('/')}/{filename}"
    s3_client.upload_file(local_file_path, S3_BUCKET, s3_key)
    return s3_key

def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """
    Generates a pre-signed URL for accessing the object.
    """
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=expires_in,
        )
        return url
    except ClientError as e:
        print(f"Error generating URL: {e}")
        return None
