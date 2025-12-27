import logging
import redis.asyncio as aioredis
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi_limiter import FastAPILimiter
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routers import process, download, status as status_router, ui
from app.services.scheduler import start_scheduler  # Ensure path matches your file
from app.routers.ui import templates

# 1. Structured Logging Configuration
# Use a standardized format for better traceability in production logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 2. Modern Lifespan Management (Replaces @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events logic.
    """
    # --- Startup Logic ---
    logger.info("Initializing MIBTech Background Removal Service...")

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
        # In production, you might want to raise this to prevent a half-broken start
    
    # Start the Background Maintenance Scheduler
    start_scheduler()
    logger.info("✅ Background cleanup scheduler active.")

    yield  # The application runs here

    # --- Shutdown Logic ---
    logger.info("Shutting down... Cleaning up resources.")
    await redis_connection.close() # type: ignore


# 3. FastAPI Application Definition
app = FastAPI(
    title="MIBTech Image Background Removal Service",
    description="Professional-grade AI background removal API.",
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENV != "production" else None,
    redoc_url=None
)

# 4. Static Files and Routers
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(process.router)
app.include_router(status_router.router) # Renamed to avoid collision with 'status' module
app.include_router(download.router)
app.include_router(ui.router)


# 5. Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Unified exception handler for UI and API contexts.
    """
    # Check if the request is asking for HTML (Browser) or JSON (API)
    is_browser = "text/html" in request.headers.get("accept", "")

    if exc.status_code == status.HTTP_404_NOT_FOUND and is_browser:
        return templates.TemplateResponse(
            "404.html",
            {"request": request, "title": "Page Not Found"},
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Return clean JSON for API clients, or basic HTML for others
    if not is_browser:
        return {"detail": exc.detail, "status": exc.status_code}

    return HTMLResponse(
        content=f"<html><body><h1>Error {exc.status_code}</h1><p>{exc.detail}</p></body></html>",
        status_code=exc.status_code
    )


if __name__ == "__main__":
    import uvicorn
    # Using 'app' object directly for local execution
    uvicorn.run(app, host="0.0.0.0", port=8000)







# import logging
# from fastapi import FastAPI, Request
# from fastapi.staticfiles import StaticFiles
# from fastapi_limiter import FastAPILimiter
# import redis.asyncio as aioredis
# from fastapi.responses import HTMLResponse
# from starlette.exceptions import HTTPException as StarletteHTTPException
# from app.routers.ui import templates

# from .config import settings
# from .routers import process, status, download, ui
# from .services.cleanup import start_scheduler

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(
#     title="MIBTech Image Background Removal Service",
#     version="1.0.0",
# )

# # mount /static → app/static
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# # Include routers
# app.include_router(process.router)
# app.include_router(status.router)
# app.include_router(download.router)
# app.include_router(ui.router)


# @app.on_event("startup")
# async def on_startup():
#     # init cleanup scheduler
#     start_scheduler()
#     logger.info("Cleanup scheduler started")

#     # initialize fastapi-limiter
#     redis = aioredis.from_url(
#         settings.REDIS_URL,
#         encoding="utf-8",
#         decode_responses=True,
#     )

#     await FastAPILimiter.init(redis)
#     logger.info("Rate limiter initialized")


# # 404 handler
# @app.exception_handler(StarletteHTTPException)
# async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
#     if exc.status_code == 404:
#         # render your custom 404 page
#         return templates.TemplateResponse(
#             "404.html",
#             {"request": request},
#             status_code=404
#         )
#     # fallback to default for other HTTP errors
#     return HTMLResponse(
#         content=f"<h1>{exc.status_code} Error</h1><p>{exc.detail}</p>",
#         status_code=exc.status_code
#     )


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
