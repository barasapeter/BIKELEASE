from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse


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

        bike_id = payload.get("bike_id")
        nickname = (payload.get("nickname") or "").strip()
        rpm_raw = payload.get("rpm")
        shop_id = payload.get("shop_id")

        missing_fields = []

        if not bike_id:
            missing_fields.append("id")

        if not nickname:
            missing_fields.append("nickname")

        if shop_id is None:
            missing_fields.append("shop_id")

        if rpm_raw is None:
            missing_fields.append("rpm")

        if missing_fields:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Missing required fields.",
                    "missing_fields": missing_fields,
                },
            )

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

        return {"detail": "Bike added successfully.", "bike_code": bike.id}

    except HTTPException:
        raise
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        raise HTTPException(status_code=500, detail="Something went wrong.")


@router.patch("/update")
async def patch_bike(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        payload = await request.json()

        shop_id = payload.get("shop_id")
        bike_id = payload.get("bike_id").strip()
        nickname = (payload.get("nickname") or "").strip()
        rpm_raw = payload.get("rpm")
        metadata = payload.get("metadata")

        if not bike_id:
            raise HTTPException(status_code=422, detail="Bike ID missing.")

        if rpm_raw:
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

        bike = (
            db.query(Bike).filter(Bike.id == bike_id, Bike.shop_id == shop.id).first()
        )
        if not bike:
            raise HTTPException(status_code=400, detail="Bike does not exist.")

        if (
            nickname == bike.nickname
            and int(rate_per_minute) == int(bike.rate_per_minute)
            and metadata == dict(bike.metadata_e)
        ):
            return JSONResponse(
                status_code=200, content={"detail": "No changes detected."}
            )

        if nickname:
            bike.nickname = nickname
        if rpm_raw:
            bike.rate_per_minute = rate_per_minute
        if metadata:
            bike.metadata_e = metadata

        db.add(bike)
        db.commit()
        db.refresh(bike)

        return {"detail": "Update successful"}

    except HTTPException:
        raise
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        raise HTTPException(status_code=422, detail="Something went wrong.")
