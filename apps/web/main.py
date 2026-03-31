from pathlib import Path
import traceback
from uuid import UUID
from datetime import datetime

from utils import format_duration_progressive

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, Response

from sqlalchemy import func

from data.models import (
    ShopOwner,
    Employee,
    Shop,
    Bike,
    Session as BikeSession,
    SessionCheckout,
    MpesaCheckout,
    MpesaTransactionStatus,
)

from core import config

from core.security import get_current_user_optional, clear_auth_cookies

from sqlalchemy.orm import Session
from sqlalchemy.orm import Session, joinedload

from data.db import get_db

from core.errors import ShopNotFoundError

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
SETTINGS = config.GlobalSettings()

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["strftime"] = lambda dt, fmt: dt.strftime(fmt) if dt else "—"


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
        if not shop:
            raise ShopNotFoundError

        if isinstance(user, ShopOwner):
            context["role"] = "owner"
            if not shop in user.shops:
                forbid()

        elif isinstance(user, Employee):
            context["role"] = "employee"
            if user.shop != shop:
                forbid()

        context["shop"] = shop

        # counts
        context["bikes"] = (
            db.query(func.count(Bike.id)).filter(Bike.shop_id == shop_id).scalar()
        )
        context["active"] = (
            db.query(func.count(BikeSession.id))
            .join(Bike, BikeSession.bike_id == Bike.id)
            .filter(Bike.shop_id == shop_id)
            .filter(BikeSession.stop_datetime.is_(None))
            .scalar()
        )

        context["past"] = (
            db.query(func.count(BikeSession.id))
            .join(Bike, BikeSession.bike_id == Bike.id)
            .join(SessionCheckout, SessionCheckout.session_id == BikeSession.id)
            .filter(Bike.shop_id == shop_id)
            .filter(SessionCheckout.amount_paid != 0)
            .scalar()
        )

        return templates.TemplateResponse("shop.html", context)

    except Exception as e:
        context["status_code"] = 400
        context["error_title"] = "Internal Server Error"
        context["error_body"] = "Something went wrong."
        context["traceback"] = str(e)
        return templates.TemplateResponse("error.html", context)


@router.get("/bikes/{shop_id}")
async def bikes(
    shop_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    context = {"request": request, "shop": shop_id}
    try:
        if user is None:
            return RedirectResponse(url="/login")

        context["shop_id"] = shop_id
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        context["bikes"] = shop.bikes

        return templates.TemplateResponse("bikes.html", context)
    except Exception:
        context["status_code"] = 500
        context["error_title"] = "Internal Server Error"
        context["traceback"] = traceback.format_exc()
        return templates.TemplateResponse("error.html", context)


@router.get("/bike/{shop_id}")
async def bike(
    shop_id: UUID,
    request: Request,
    user=Depends(get_current_user_optional),
):
    context = {"request": request, "shop": shop_id}
    try:
        if user is None:
            return RedirectResponse(url="/login")

        context["shop_id"] = shop_id
        return templates.TemplateResponse("bike.html", context)
    except Exception:
        context["status_code"] = 500
        context["error_title"] = "Internal Server Error"
        context["traceback"] = traceback.format_exc()
        return templates.TemplateResponse("error.html", context)


@router.get("/start-session/{shop_id}")
async def sart_session(
    shop_id: UUID,
    request: Request,
    user=Depends(get_current_user_optional),
):
    context = {"request": request, "shop": shop_id}
    try:
        if user is None:
            return RedirectResponse(url="/login")

        context["shop_id"] = shop_id
        return templates.TemplateResponse("start.html", context)
    except Exception:
        context["status_code"] = 500
        context["error_title"] = "Internal Server Error"
        context["traceback"] = traceback.format_exc()
        return templates.TemplateResponse("error.html", context)


@router.get("/sessions/{shop_id}")
async def sessions(
    shop_id: UUID,
    request: Request,
    user=Depends(get_current_user_optional),
):
    context = {"request": request, "shop": shop_id}
    try:
        if user is None:
            return RedirectResponse(url="/login")

        return templates.TemplateResponse("sessions.html", context)
    except Exception:
        context["status_code"] = 500
        context["error_title"] = "Internal Server Error"
        context["traceback"] = traceback.format_exc()
        return templates.TemplateResponse("error.html", context)


@router.get("/session/{session_id}")
async def session_view(
    session_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    context = {"request": request}

    def render_error(status_code: int, error_title: str, error_body: str):
        context["status_code"] = status_code
        context["error_title"] = error_title
        context["error_body"] = error_body
        return templates.TemplateResponse(
            "error.html", context, status_code=status_code
        )

    def forbid():
        return render_error(
            403,
            "Forbidden",
            "Please check your access rights, then try again.",
        )

    def not_found():
        return render_error(
            404,
            "Session Not Found",
            "The requested session could not be found.",
        )

    def internal_error():
        context["status_code"] = 500
        context["error_title"] = "Internal Server Error"
        context["error_body"] = "Something went wrong while loading the session."
        context["traceback"] = traceback.format_exc()
        return templates.TemplateResponse("error.html", context, status_code=500)

    try:
        if user is None:
            return RedirectResponse(url="/login")

        query = (
            db.query(BikeSession)
            .join(BikeSession.bike)
            .join(Bike.shop)
            .options(
                joinedload(BikeSession.customer),
                joinedload(BikeSession.bike).joinedload(Bike.shop),
                joinedload(BikeSession.checkout),
            )
            .filter(BikeSession.id == session_id)
        )

        if isinstance(user, ShopOwner):
            query = query.filter(Shop.owner_id == user.id)
        elif isinstance(user, Employee):
            query = query.filter(Shop.id == user.shop_id)
        else:
            return forbid()

        bike_session = query.first()

        if bike_session is None:
            return not_found()

        start = bike_session.start_datetime
        stop = bike_session.stop_datetime

        duration = (
            (stop - start).total_seconds() / 60 if stop else "ongoing"
        )  # minutes as float
        duration = (
            max(0, duration) if stop else "ongoing"
        )  # toavoid negatives if clocks/data are weird

        amount = round(duration * bike_session.rpm_on_allocate) if stop else None

        context["session"] = bike_session
        context["str"] = str
        context["duration"] = duration
        context["amount"] = amount
        context["shop"] = bike_session.bike.shop
        context["user"] = user
        context["fmt"] = format_duration_progressive
        context["mpesastatus"] = None

        session_checkout = bike_session.checkout
        if session_checkout:
            session_checkout = bike_session.checkout
            pending = (
                db.query(MpesaCheckout)
                .filter(
                    MpesaCheckout.session_checkout_id == session_checkout.id,
                    MpesaCheckout.transaction_status_enum
                    == MpesaTransactionStatus.PENDING,
                )
                .first()
            )
            if pending:
                context["mpesastatus"] = "pending"

            success = (
                db.query(MpesaCheckout)
                .filter(
                    MpesaCheckout.session_checkout_id == session_checkout.id,
                    MpesaCheckout.transaction_status_enum
                    == MpesaTransactionStatus.SUCCESS,
                )
                .first()
            )
            if success:
                context["mpesastatus"] = "success"

            failed = (
                db.query(MpesaCheckout)
                .filter(
                    MpesaCheckout.session_checkout_id == session_checkout.id,
                    MpesaCheckout.transaction_status_enum
                    == MpesaTransactionStatus.FAILED,
                )
                .first()
            )
            if failed:
                context["mpesastatus"] = "failed"

        return templates.TemplateResponse("session.html", context)

    except Exception:
        return internal_error()


@router.get("/reports/{shop_id}")
async def session_view(
    shop_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional),
):
    context = {"request": request, "shop_id": shop_id}
    return templates.TemplateResponse("reports.html", context)
