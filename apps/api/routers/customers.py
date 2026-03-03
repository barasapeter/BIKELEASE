from fastapi import APIRouter, Depends, Request, HTTPException


from data.db import get_db
from data.models import ShopOwner, Employee, Bike, Customer
from data.models import Session as BikeSession
from core import config
from core.security import (
    get_current_user,
)

from utils import normalize_and_validate_phone_number_ke
from core.errors import InvalidPhoneNumberException

from sqlalchemy.orm import Session
from sqlalchemy import func

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


@router.post("/start-session")
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
                detail=f"{bike.nickname}, {bike.id} is unavailable: {bikestate}",
            )

        bikesession = (
            db.query(BikeSession).filter(BikeSession.customer_id == customer.id).first()
        )
        if bikesession and bike.metadata_e.get("leasedto") == customer_id:
            raise HTTPException(status_code=419, detail="Bike already leased.")

        bikesession: BikeSession = BikeSession(
            customer_id=customer.id,
            bike_id=bike.id,
            rpm_on_allocate=bike.rate_per_minute,
            start_datetime=func.now(),
        )
        new_meta = dict(bike.metadata_e or {})
        new_meta["leasedto"] = customer_id
        new_meta["bikestate"] = "LEASED"
        bike.metadata_e = new_meta

        db.add(bike)
        db.add(bikesession)
        db.commit()
        db.refresh(bike)
        db.refresh(bikesession)
        return {"detail": "Session started successfully."}

    except HTTPException:
        raise
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        raise HTTPException(status_code=422, detail="Something went wrong.")


@router.patch("/stop-session")
async def stop_session(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        payload = await request.json()

        session_id = payload.get("session_id")

        if not session_id:
            raise HTTPException(status_code=422, detail="Missing session ID.")

        bikesession = db.query(BikeSession).filter(BikeSession.id == session_id).first()
        if not bikesession:
            raise HTTPException(status_code=400, detail="Invalid session ID")

        bike = bikesession.bike

        bikesession.stop_datetime = func.now()

        new_meta = dict(bike.metadata_e or {})
        del new_meta["leasedto"]
        new_meta["bikestate"] = "AVAILABLE"
        bike.metadata_e = new_meta

        db.add(bike)
        db.add(bikesession)
        db.commit()
        db.refresh(bike)
        db.refresh(bikesession)
        return {"detail": "Session stopped successfully."}

    except HTTPException:
        raise
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        raise HTTPException(status_code=422, detail="Something went wrong.")
