from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse


from data.db import get_db
from data.models import (
    ShopOwner,
    Employee,
    Bike,
    Customer,
    SessionCheckout,
    MpesaCheckout,
)
from data.models import Session as BikeSession

from data.models import PaymentMethod, MpesaTransactionStatus

from core import config
from core.security import (
    get_current_user,
)

from utils import normalize_and_validate_phone_number_ke
from core.errors import InvalidPhoneNumberException

from integrations.mpesa import client

from sqlalchemy.orm import Session
from sqlalchemy import func

import logging
import traceback
from datetime import datetime, timezone


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
                    "duration_in_minutes": (
                        s.checkout.duration_in_minutes if s.checkout else "ongoing"
                    ),
                    "amount_paid": s.checkout.amount_paid if s.checkout else 0,
                    "datetime": s.start_datetime if s.checkout else None,
                }
                for s in customer.sessions
            ]
            return {
                "detail": f"Customer exists",
                "id": customer.id,
                "name": customer.name,
                "points": "Not Computed",
                "sessions": previous_sessions,
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
            raise HTTPException(status_code=409, detail="Bike already leased.")

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

        if bikesession.stop_datetime:
            raise HTTPException(status_code=409, detail="Session was already stopped.")

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


@router.post("/checkout-session")
async def checkout_session(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        payload = await request.json()

        session_id = payload.get("session_id")
        payment_method = payload.get("payment_method")
        commit = payload.get("commit")
        phone = payload.get("phone")

        if not session_id or commit is None or not payment_method in ["CASH", "MPESA"]:
            raise HTTPException(status_code=422, detail="Missing or invalid fields.")

        bikesession = db.query(BikeSession).filter(BikeSession.id == session_id).first()
        if not bikesession:
            raise HTTPException(status_code=400, detail="Invalid session ID")

        if not bikesession.stop_datetime:
            raise HTTPException(
                status_code=400,
                detail="Tis is an ongoing session. You need to stop it first.",
            )

        start = bikesession.start_datetime
        stop = bikesession.stop_datetime

        duration = (stop - start).total_seconds() / 60  # minutes as float
        duration = max(0, duration)  # avoid negatives if clocks/data are weird

        amount = duration * bikesession.rpm_on_allocate

        session_checkout = bikesession.checkout

        if session_checkout and session_checkout.amount_paid:
            return JSONResponse(
                status_code=200,
                content={
                    "detail": f"Session was checked out successfully with {session_checkout.payment_method_enum}."
                },
            )

        async def process_push_request(phone):

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
                raise HTTPException(
                    status_code=409,
                    detail="A push request is ongoing. Please wait until it completes first.",
                )

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
                return JSONResponse(
                    status_code=200,
                    content={
                        "detail": "Session was checked out successfully via MPESA."
                    },
                )

            if not phone:
                phone = session_checkout.session.customer.primary_phone
                if not phone:
                    raise HTTPException(
                        status_code=400, detail="Phone number required."
                    )
            else:
                phone = normalize_and_validate_phone_number_ke(phone)

            url = request.url
            origin = f"{url.scheme}://{url.hostname}"
            if url.port:
                origin += f":{url.port}"

            stk_initiate = await client.initiate_stk_push(
                phone, amount=round(amount), callback_url=f"{origin}/mpesa-endpoint"
            )
            if stk_initiate["success"]:
                response_description = stk_initiate["detail"]["ResponseDescription"]
                mpesa_checkout_request_id = stk_initiate["detail"]["CheckoutRequestID"]

                mpesa_checkout = MpesaCheckout(
                    session_checkout_id=session_checkout.id,
                    customer_MSISDN=phone,
                    mpesa_checkout_request_id=mpesa_checkout_request_id,
                    transaction_status_enum=MpesaTransactionStatus.PENDING,
                )
                db.add(mpesa_checkout)
                db.commit()
                db.refresh(mpesa_checkout)

                return {
                    "detail": f"Toolkit Prompt of KES{round(amount)} sent to {phone}. {response_description}",
                    "payment": payment_method,
                    "duration": duration,
                    "amount": amount,
                }
            else:
                error = stk_initiate["detail"].get("errorMessage")
                raise HTTPException(status_code=422, detail=error)

        if not session_checkout:
            payment_mapping = {"CASH": PaymentMethod.CASH, "MPESA": PaymentMethod.MPESA}
            payment_method = payment_mapping[payment_method]

            session_checkout = SessionCheckout(
                session_id=bikesession.id,
                payment_method_enum=payment_method,
                amount_paid=(
                    0 if payment_method == PaymentMethod.MPESA else round(amount)
                ),
                duration_in_minutes=duration,
                metadata_e={"precise_amount": amount},
            )
            if payment_method == PaymentMethod.MPESA or commit:
                db.add(session_checkout)
                db.commit()
                db.refresh(session_checkout)

            # for initial request
            if payment_method == PaymentMethod.MPESA:
                return await process_push_request(phone)

            return {
                "detail": f"Cash payment{" " if commit else " not "}confirmed.",
                "payment": payment_method,
                "duration": duration,
                "amount": round(amount),
                "precise": amount,
            }

        # for subsequent request
        if payment_method == PaymentMethod.MPESA:
            return await process_push_request(phone)

        return {
            "detail": f"{session_checkout.payment_method_enum} checkout was already created.{f" Status: "+ session_checkout.mpesa.transaction_status_enum if session_checkout.mpesa else " PAID IN CASH"}",
            "duration": duration,
            "amount": amount,
        }

    except HTTPException:
        raise
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        raise HTTPException(status_code=422, detail="Something went wrong.")
