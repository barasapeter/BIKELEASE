from pathlib import Path
import traceback

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, Response

from data.models import ShopOwner, Employee, Shop

from core import config

from core.security import get_current_user_optional, clear_auth_cookies

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


@router.get("/login")
async def main(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("login.html", context)


@router.get("/logout")
async def main(response: Response):
    clear_auth_cookies(response)
    return RedirectResponse("/login")


@router.get("/dashboard")
async def main(request: Request, user=Depends(get_current_user_optional)):
    context = {"request": request, "user": user}
    try:
        if user is None:
            return RedirectResponse(url="/login")

        if isinstance(user, ShopOwner):
            context["user"] = user
            context["shops"] = user.shops
        elif isinstance(user, Employee):
            request.session["shop_id"] = user.shop.id
            return RedirectResponse("/shop")

        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        context["status_code"] = 500
        context["error_title"] = "Internal Server Error"
        context["traceback"] = traceback.format_exc()
        return templates.TemplateResponse("error.html", context)
