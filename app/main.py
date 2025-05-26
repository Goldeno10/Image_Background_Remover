import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
import redis.asyncio as aioredis
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.routers.ui import templates

from .config import settings
from .routers import process, status, download, ui
from .services.cleanup import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MIBTech Image Background Removal Service",
    version="1.0.0",
)

# mount /static → app/static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(process.router)
app.include_router(status.router)
app.include_router(download.router)
app.include_router(ui.router)


@app.on_event("startup")
async def on_startup():
    # init cleanup scheduler
    start_scheduler()
    logger.info("Cleanup scheduler started")

    # initialize fastapi-limiter
    redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )

    await FastAPILimiter.init(redis)
    logger.info("Rate limiter initialized")


# 404 handler
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        # render your custom 404 page
        return templates.TemplateResponse(
            "404.html",
            {"request": request},
            status_code=404
        )
    # fallback to default for other HTTP errors
    return HTMLResponse(
        content=f"<h1>{exc.status_code} Error</h1><p>{exc.detail}</p>",
        status_code=exc.status_code
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
