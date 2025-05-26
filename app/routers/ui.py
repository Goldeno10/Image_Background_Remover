import datetime
from fastapi import (
    APIRouter, Request,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# create templates and register `now()`
templates.env.globals["now"] = datetime.datetime.utcnow


@router.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/api-docs", response_class=HTMLResponse)
def api_docs(request: Request):
    return templates.TemplateResponse(
        "docs.html",
        {"request": request}
    )

@router.get("/about")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

