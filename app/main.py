import os
import logging
import redis.asyncio as aioredis
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi_limiter import FastAPILimiter
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routers import process, download, status as status_router, ui
from app.services.scheduler import start_scheduler
from app.routers.ui import templates

# 1. Structured Logging Configuration
# Standardized format for 2025 traceability in production logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 2. Modern Lifespan Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown lifecycle.
    Ensures directories and connections are ready before the first request.
    """
    # --- Startup Logic ---
    logger.info("🚀 Initializing MIBTech Background Removal Service...")

    # Ensure the output directory exists to prevent StaticFiles mounting errors
    if not os.path.exists(settings.OUTPUT_DIR):
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        logger.info(f"📁 Created output directory at: {settings.OUTPUT_DIR}")

    # Initialize Redis for Rate Limiting
    try:
        redis_connection = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await FastAPILimiter.init(redis_connection)
        logger.info("✅ Rate limiter (Redis) initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Rate Limiter: {e}")
    
    # Start the Background Maintenance Scheduler
    start_scheduler()
    logger.info("✅ Background cleanup scheduler active.")

    yield  # Application runs here

    # --- Shutdown Logic ---
    logger.info("🛑 Shutting down... Cleaning up resources.")
    if 'redis_connection' in locals():
        await redis_connection.close() # type: ignore


# 3. FastAPI Application Definition
app = FastAPI(
    title="MIBTech Image Background Removal Service",
    description="Professional-grade AI background removal API powered by U2-Net.",
    version="1.1.0",
    lifespan=lifespan,
    # 2025 Security Best Practice: Hide interactive docs in production
    docs_url="/api/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
    openapi_url="/openapi.json" if settings.ENV != "production" else None,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
)

# 4. CORS Configuration
# Essential to fix the 'Network Error' and 'CORS Blocked' issues in the browser
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Replace with your actual 2025 domain for deployment: "https://mibtech.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Static Files Mounting
# These are mounted AFTER the middleware but BEFORE the routers
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CRITICAL: This allows the frontend to access http://localhost:8000/processed_images/filename.png
app.mount("/processed_images", StaticFiles(directory=settings.OUTPUT_DIR), name="processed_images")


# 6. Include Routers
app.include_router(process.router)
app.include_router(status_router.router)
app.include_router(download.router)
app.include_router(ui.router)


# 7. Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Context-aware exception handler for both Browser (HTML) and API (JSON) requests.
    """
    is_browser = "text/html" in request.headers.get("accept", "")

    if exc.status_code == status.HTTP_404_NOT_FOUND and is_browser:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "title": "Page Not Found"},
            status_code=status.HTTP_404_NOT_FOUND
        )

    if not is_browser:
        return {"detail": exc.detail, "status": exc.status_code}

    return HTMLResponse(
        content=f"<html><body style='font-family:sans-serif;'><h1>Error {exc.status_code}</h1><p>{exc.detail}</p></body></html>",
        status_code=exc.status_code
    )


if __name__ == "__main__":
    import uvicorn
    # Launching the server with live-reload for developer efficiency
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
