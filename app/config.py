import os
from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "ibrahimmuhammad271@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "nyxb zwua duqm pxgb")

    # App
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "processed_images")
    CLEANUP_INTERVAL_HOURS: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "1"))

    # Model

    GPU_ENABLED: bool = cuda.is_available() and os.getenv("GPU_ENABLED", "false").lower() == "true"
    MODEL_NAMES: list[str] = os.getenv("MODEL_NAMES", "u2net,u2netp,u2net_human_seg").split(",")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "u2net")
    ALLOWED_OUTPUT_FORMATS: list[str] = ["png", "jpg", "jpeg"]
    DEFAULT_OUTPUT_FORMAT: str = os.getenv("DEFAULT_OUTPUT_FORMAT", "png")
    DEFAULT_QUALITY: int = int(os.getenv("DEFAULT_QUALITY", "95"))
    DEFAULT_SCALE: float = float(os.getenv("DEFAULT_SCALE", "1.0"))


    ENV: str = "production" # or "development"
    
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "your-s3-bucket-name")
    AWS_REGION: str = os.getenv("AWS_REGION", "eu-north-1")
    AWS_USE_S3: bool = os.getenv("AWS_USE_S3", "false").lower() == "true"

    AWS_S3_USER: str = os.getenv("AWS_S3_USER", "your-s3-user")
    AWS_ACCESS_KEY: str = os.getenv("AWS_ACCESS_KEY", "your-access-key-id")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "your-secret-access-key")



    # Add these two lines:
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    U2NET_HOME: str = os.getenv("U2NET_HOME", "./models/.u2net")


    class Config:
        env_file = ".env"
        case_sensitive = True
        model_config = SettingsConfigDict(
            env_file=".env",
            extra="ignore"
        )


settings = Settings()