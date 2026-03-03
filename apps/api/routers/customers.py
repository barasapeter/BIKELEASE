from fastapi import APIRouter, Depends, Request, HTTPException


from data.db import get_db
from data.models import ShopOwner, Employee, Bike, Customer
from core import config
from core.security import (
    get_current_user,
)

from utils import normalize_and_validate_phone_number_ke
from core.errors import InvalidPhoneNumberException

from sqlalchemy.orm import Session

import logging
import traceback


router = APIRouter()

SETTINGS = config.GlobalSettings()
logger = logging.getLogger(SETTINGS.APP_NAME)


@router.post("/create-customer")
async def create_customer(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        payload = await request.json()

        name = (payload.get("name") or "").strip()
        phone = payload.get("phone")

        if not name or not phone:
            raise HTTPException(status_code=422, detail="Missing required fields.")

        try:
            phone = normalize_and_validate_phone_number_ke(phone)
        except InvalidPhoneNumberException:
            raise HTTPException(status_code=400, detail="Invalid phone number.")

        customer = db.query(Customer).filter(Customer.primary_phone == phone).first()
        if customer:
            previous_sessions = [
                {
                    "bike": f"{s.bike.nickname}, {s.bike.id}",
                    "duration_in_minutes": s.checkout.duration_in_minutes,
                    "amount_paid": s.checkout.amount_paid,
                    "datetime": s.start_datetime,
                }
                for s in customer.sessions
            ]
            return {
                "detail": f"Customer exists",
                "id": customer.id,
                "name": customer.name,
                "loyalty_points": "Not Computed",
                "previous_sessions": previous_sessions,
                "registration": {
                    "datetime": customer.datetime_registered,
                    "attendant": dict(customer.metadata_e).get("attendant"),
                },
            }

        customer: Customer = Customer(
            name=name,
            primary_phone=phone,
            metadata_e={
                "attendant": {
                    "name": current_user.name,
                    "username": current_user.username,
                }
            },
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return {"detail": "Customer create successful."}

    except HTTPException:
        raise
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        raise HTTPException(status_code=500, detail="Something went wrong.")


@router.post("/create-session")
async def create_session(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        payload = await request.json()

        customer_id = payload.get("customer_id")
        bike_id = payload.get("bike_id")

        if not customer_id or not bike_id:
            raise HTTPException(status_code=422, detail="Missing required fields.")

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer does not exist")
        bike = db.query(Bike).filter(Bike.id == bike_id).first()
        if not bike:
            raise HTTPException(status_code=404, detail="Bike does not exist")

        bikestate = bike.metadata_e.get("bikestate", "STATE_UNDEFINED")
        if bikestate != "AVAILABLE":
            raise HTTPException(
                status_code=409,
                detail=f"{bike.nickname}, {bike.id} {bikestate}",
            )

        return {"detail": "OK"}

    except HTTPException:
        raise
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        raise HTTPException(status_code=422, detail="Something went wrong.")
