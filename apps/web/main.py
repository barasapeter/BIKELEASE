from pathlib import Path
import traceback
from uuid import UUID


from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, Response

from data.models import ShopOwner, Employee, Shop

from core import config

from core.security import get_current_user_optional, clear_auth_cookies

from sqlalchemy.orm import Session

from data.db import get_db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
SETTINGS = config.GlobalSettings()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/")
async def main(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("lander.html", context)


@router.get("/palette")
async def palette(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("palette.html", context)


@router.get("/login")
async def login(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("login.html", context)


@router.get("/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return RedirectResponse("/login")


@router.get("/dashboard")
async def dashboard(request: Request, user=Depends(get_current_user_optional)):
    context = {"request": request, "user": user}
    try:
        if user is None:
            return RedirectResponse(url="/login")

        if isinstance(user, ShopOwner):
            context["user"] = user
            context["shops"] = user.shops
        elif isinstance(user, Employee):
            return RedirectResponse(f"/shop/{user.shop.id}")

        return templates.TemplateResponse("dashboard.html", context)
    except Exception:
        context["status_code"] = 500
        context["error_title"] = "Internal Server Error"
        context["traceback"] = traceback.format_exc()
        return templates.TemplateResponse("error.html", context)


@router.get("/shop/{shop_id}")
async def shop(
    shop_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    context = {"request": request, "user": user, "shop_id": shop_id}

    try:
        if user is None:
            return RedirectResponse(url="/login")

        def forbid():
            context["status_code"] = 403
            context["error_title"] = "Forbidden"
            error_body = "Please check your access rights, then try again."
            context["error_body"] = error_body
            return templates.TemplateResponse("error.html", context)

        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if isinstance(user, ShopOwner):
            context["role"] = "owner"
            if not shop in user.shops:
                forbid()

        elif isinstance(user, Employee):
            context["role"] = "employee"
            if user.shop != shop:
                forbid()

        context["shop"] = shop
        context["employees"] = shop.employees
        context["bikes"] = shop.bikes

        return templates.TemplateResponse("shop.html", context)

    except Exception:
        context["status_code"] = 500
        context["error_title"] = "Internal Server Error"
        context["error_body"] = "Something went wrong."
        context["traceback"] = traceback.format_exc()
        return templates.TemplateResponse("error.html", context)
