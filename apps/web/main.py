from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from core import config

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
SETTINGS = config.GlobalSettings()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/")
async def main(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("lander.html", context)


@router.get("/palette")
async def main(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("palette.html", context)
