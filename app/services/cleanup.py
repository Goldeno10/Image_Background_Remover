# app/services/cleanup.py

import os
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.redis_client import redis_client
from app.config import settings


def cleanup_redis_and_files():
    # Redis keys
    for key in redis_client.scan_iter():
        if redis_client.ttl(key) < 0:
            redis_client.delete(key)

    # Files
    cutoff = time.time() - settings.REDIS_TTL_SECONDS
    for fname in os.listdir(settings.OUTPUT_DIR):
        path = os.path.join(settings.OUTPUT_DIR, fname)
        if os.path.getmtime(path) < cutoff:
            os.remove(path)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=cleanup_redis_and_files,
        trigger="interval",
        hours=settings.CLEANUP_INTERVAL_HOURS,
        # fire first run 10 seconds from now
        next_run_time=datetime.now() + timedelta(seconds=10),
    )
    scheduler.start()