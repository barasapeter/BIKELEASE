from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse


from data.db import get_db
from data.models import ShopOwner, Employee, Customer
from core import config
from core.security import hash_pin, verify_pin, set_auth_cookies, get_current_user


from sqlalchemy.orm import Session

import logging
import traceback


router = APIRouter()

SETTINGS = config.GlobalSettings()
logger = logging.getLogger(SETTINGS.APP_NAME)


@router.post("/create-shop-owner")
async def create_shop_owner(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        shop_owner: ShopOwner = ShopOwner(
            name=payload["name"],
            username=payload["username"],
            pin_hash=hash_pin(payload["pin"]),
        )
        db.add(shop_owner)
        db.commit()
        db.refresh(shop_owner)
        return {"detail": "Register successful."}
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=422, content={"detail": "Something went wrong."}
        )


@router.post("/create-employee")
async def create_employee(
    request: Request,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    try:
        payload = await request.json()
        return {"current_user": user_id}
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=422, content={"detail": "Something went wrong."}
        )


@router.post("/login")
async def create_employee(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        username = payload["username"]
        pin = payload["pin"]
        category = payload["category"]

        map = {"owner": ShopOwner, "employee": Employee}
        constructor = map[category]

        user = db.query(constructor).filter(constructor.username == username).first()
        if user and verify_pin(plain_pin=pin, hashed_pin=user.pin_hash):
            response = JSONResponse(content={"detail": "Login successful."})
            set_auth_cookies(response, str(user.id))
            return response
        return JSONResponse(
            status_code=401, content={"detail": "The sign in details are incorrect."}
        )
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=422, content={"detail": "Something went wrong."}
        )
