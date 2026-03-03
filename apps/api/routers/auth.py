from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse


from data.db import get_db
from data.models import ShopOwner, Employee
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
            name=payload["name"].strip(),
            username=payload["username"].strip().lower(),
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
    current_user: dict = Depends(get_current_user),
):
    try:
        if not isinstance(current_user, ShopOwner):
            return JSONResponse(
                status_code=400, content={"detail": "Failed to create employee."}
            )

        payload = await request.json()
        username = payload["username"].strip().lower()
        exists = db.query(Employee).filter(Employee.username == username).first()
        if exists:
            return JSONResponse(
                status_code=409, content={"detail": "Employee already exists."}
            )
        employee: Employee = Employee(
            shop_id=payload["shop_id"],
            name=payload["name"],
            username=username,
            pin_hash=hash_pin(payload["pin"]),
            metadata_e={
                "require_reset_pin": True,
            },
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)
        return {"detail": "Employee create successful."}
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=422, content={"detail": "Something went wrong."}
        )


@router.post("/login")
async def create_employee(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        username = payload["username"].strip().lower()
        pin = payload["pin"]
        category = payload["category"]

        map_ = {"owner": ShopOwner, "employee": Employee}
        if category not in map_:
            return JSONResponse(status_code=400, content={"detail": "Invalid category"})

        constructor = map_[category]

        user = db.query(constructor).filter(constructor.username == username).first()
        if user and verify_pin(plain_pin=pin, hashed_pin=user.pin_hash):
            response = JSONResponse(content={"detail": "Login successful."})
            set_auth_cookies(response, str(user.id), category)
            return response

        return JSONResponse(
            status_code=401, content={"detail": "The sign in details are incorrect."}
        )
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=422, content={"detail": "Something went wrong."}
        )
