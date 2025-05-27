
import os
import time
import boto3
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from app.redis_client import redis_client
from app.config import settings


def cleanup_redis_and_files():
    # Clean expired Redis keys
    for key in redis_client.scan_iter():
        if redis_client.ttl(key) < 0:
            redis_client.delete(key)

    # Clean files depending on environment
    if settings.ENV == "production" and settings.AWS_USE_S3:
        # Clean up from S3
        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        # List and optionally delete old S3 objects (example logic: delete if older than TTL)
        response = s3.list_objects_v2(Bucket=settings.AWS_S3_BUCKET, Prefix="processed/")
        if "Contents" in response:
            cutoff_time = datetime.now().timestamp() - settings.REDIS_TTL_SECONDS
            for obj in response["Contents"]:
                last_modified = obj["LastModified"].timestamp()
                if last_modified < cutoff_time:
                    s3.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=obj["Key"])

    else:
        # Local file cleanup
        cutoff = time.time() - settings.REDIS_TTL_SECONDS
        for fname in os.listdir(settings.OUTPUT_DIR):
            path = os.path.join(settings.OUTPUT_DIR, fname)
            try:
                if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except FileNotFoundError:
                continue


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=cleanup_redis_and_files,
        trigger="interval",
        hours=settings.CLEANUP_INTERVAL_HOURS,
        next_run_time=datetime.now() + timedelta(seconds=10),
    )
    scheduler.start()
