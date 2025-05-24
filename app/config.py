import os
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL_SECONDS: int = 86400

    # SMTP
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "ibrahimmuhammad271@gmail.com"
    SMTP_PASSWORD: str = "nyxb zwua duqm pxgb"

    # App
    BASE_URL: AnyHttpUrl = "http://localhost:8000"
    OUTPUT_DIR: str = "processed_images"
    CLEANUP_INTERVAL_HOURS: int = 1

    # Model
    GPU_ENABLED: bool = False
    MODEL_NAMES: list[str] = ["u2net", "u2netp", "u2net_human_seg"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()