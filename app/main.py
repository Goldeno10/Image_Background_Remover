import logging
from fastapi import FastAPI
from .config import settings
from .routers import process, status, download
from .services.cleanup import start_scheduler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Background Removal Service",
    version="1.0.0",
)

# Include routers
app.include_router(process.router)
app.include_router(status.router)
app.include_router(download.router)


@app.on_event("startup")
async def on_startup():
    # kick off cleanup scheduler
    start_scheduler()
    logger.info("Cleanup scheduler started")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)