from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse


from data.db import get_db
from data.models import (
    MpesaCheckout,
    MpesaTransactionStatus,
)
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


@router.post("/hook")
async def webhook_processor(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        payload = await request.json()

        stk = payload.get("Body", {}).get("stkCallback", {})

        merchant_request_id = stk.get("MerchantRequestID")
        checkout_request_id = stk.get("CheckoutRequestID")
        result_code = stk.get("ResultCode")
        result_desc = stk.get("ResultDesc")

        payment_successful = result_code == 0

        amount = None
        mpesa_receipt_number = None
        transaction_date = None
        phone_number = None

        mpesa_checkout = (
            db.query(MpesaCheckout)
            .filter(MpesaCheckout.mpesa_checkout_request_id == checkout_request_id)
            .first()
        )
        if not mpesa_checkout:
            return JSONResponse(
                status_code=200,
                content={
                    "ResultCode": 1,
                    "ResultDesc": "Request ID not found.",
                },
            )

        session_checkout = mpesa_checkout.session_checkout
        mpesa_checkout.transaction_status_desc = result_desc

        if payment_successful:
            items = stk.get("CallbackMetadata", {}).get("Item", []) or []

            amount = next(
                (i.get("Value") for i in items if i.get("Name") == "Amount"), None
            )
            mpesa_receipt_number = next(
                (
                    i.get("Value")
                    for i in items
                    if i.get("Name") == "MpesaReceiptNumber"
                ),
                None,
            )
            transaction_date = next(
                (i.get("Value") for i in items if i.get("Name") == "TransactionDate"),
                None,
            )
            phone_number = next(
                (i.get("Value") for i in items if i.get("Name") == "PhoneNumber"),
                None,
            )

            mpesa_checkout.transaction_status_enum = MpesaTransactionStatus.SUCCESS
            mpesa_checkout.customer_MSISDN = phone_number

            session_checkout.amount_paid = amount

            session_checkout_metadata = {
                "mpesa_receipt_number": mpesa_receipt_number,
                "transaction_date": transaction_date,
                "merchant_request_id": merchant_request_id,
            }
            session_checkout.metadata_e = session_checkout_metadata
        else:
            mpesa_checkout.transaction_status_enum = MpesaTransactionStatus.FAILED

        db.add(mpesa_checkout)
        db.add(session_checkout)
        db.commit()

        return JSONResponse(
            status_code=200,
            content={"ResultCode": 0, "ResultDesc": "Accepted"},
        )

    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=200,
            content={"ResultCode": 1, "ResultDesc": "Failed"},
        )
