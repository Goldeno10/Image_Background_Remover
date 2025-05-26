import os
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from torch import cuda

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_TTL_SECONDS: int = 86400

    # SMTP
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = os.getenv("SMTP_PORT", 587)
    SMTP_USER: str = os.getenv("SMTP_USER", "ibrahimmuhammad271@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "nyxb zwua duqm pxgb")

    # App
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "processed_images")
    CLEANUP_INTERVAL_HOURS: int = os.getenv("CLEANUP_INTERVAL_HOURS", 1)

    # Model

    GPU_ENABLED: bool = cuda.is_available() and os.getenv("GPU_ENABLED", "true").lower() == "true"
    MODEL_NAMES: list[str] = ["u2net", "u2netp", "u2net_human_seg"]
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "u2net")
    ALLOWED_OUTPUT_FORMATS: list[str] = ["png", "jpg", "jpeg"]
    DEFAULT_OUTPUT_FORMAT: str = os.getenv("DEFAULT_OUTPUT_FORMAT", "png")
    DEFAULT_QUALITY: int = os.getenv("DEFAULT_QUALITY", 95)
    DEFAULT_SCALE: float = os.getenv("DEFAULT_SCALE", 1.0)


    ENV: str = "development"  # or "production"
    OUTPUT_DIR: str = "./output"
    
    AWS_S3_BUCKET: str = "your-bucket-name"
    AWS_REGION: str = "eu-north-1"
    USE_S3: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()