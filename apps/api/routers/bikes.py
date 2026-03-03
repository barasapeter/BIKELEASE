from fastapi import APIRouter, Depends, Request, HTTPException


from data.db import get_db
from data.models import ShopOwner, Employee, Bike, Shop
from core import config
from core.security import (
    get_current_user,
)


from sqlalchemy.orm import Session

import logging
import traceback


router = APIRouter()

SETTINGS = config.GlobalSettings()
logger = logging.getLogger(SETTINGS.APP_NAME)


@router.post("/create-bike")
async def create_bike(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        payload = await request.json()

        bike_id = payload.get("id")
        nickname = (payload.get("nickname") or "").strip()
        rpm_raw = payload.get("rpm")
        shop_id = payload.get("shop_id")

        if not bike_id or not nickname or shop_id is None or rpm_raw is None:
            raise HTTPException(status_code=422, detail="Missing required fields.")

        try:
            rate_per_minute = int(rpm_raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="rpm must be an integer.")

        shop = None
        if isinstance(current_user, ShopOwner):
            shop = (
                db.query(Shop)
                .filter(Shop.owner_id == current_user.id, Shop.id == shop_id)
                .first()
            )
        elif isinstance(current_user, Employee):
            employee = db.query(Employee).filter(Employee.id == current_user.id).first()
            shop = employee.shop if employee else None

        if not shop:
            raise HTTPException(status_code=422, detail="Shop does not exist.")

        bike_exists = (
            db.query(Bike)
            .filter(
                Bike.id == bike_id,
                Bike.nickname == nickname,
                Bike.rate_per_minute == rate_per_minute,
                Bike.shop_id == shop.id,
            )
            .first()
        )
        if bike_exists:
            raise HTTPException(status_code=409, detail="Bike already exists.")

        bike = Bike(
            id=bike_id,
            nickname=nickname,
            rate_per_minute=rate_per_minute,
            shop_id=shop.id,
        )
        db.add(bike)
        db.commit()
        db.refresh(bike)

        return {"detail": "Bike added successfully.", "bike_id": bike.id}

    except HTTPException:
        raise
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        raise HTTPException(status_code=500, detail="Something went wrong.")
