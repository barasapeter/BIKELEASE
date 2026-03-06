from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse


from data.db import get_db
from data.models import ShopOwner, Shop, Employee, Bike, Session as BikeSession
from core import config
from core.security import get_current_user


from sqlalchemy.orm import Session

import logging
import traceback
from uuid import UUID

from sqlalchemy.orm import Session as DBSession, joinedload


router = APIRouter()

SETTINGS = config.GlobalSettings()
logger = logging.getLogger(SETTINGS.APP_NAME)


from uuid import UUID


@router.get("/sessions/{shop_id}/all")
async def query_all(
    request: Request,
    shop_id: UUID,
    db: DBSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(status_code=400, detail="Shop does not exist.")

        def forbid():
            raise HTTPException(
                status_code=403, detail="You do not have access rights."
            )

        if isinstance(current_user, ShopOwner):
            if shop.owner_id != current_user.id:
                forbid()

        elif isinstance(current_user, Employee):
            if current_user.shop_id != shop_id:
                forbid()

        sessions = (
            db.query(BikeSession)
            .join(Bike, BikeSession.bike_id == Bike.id)
            .filter(Bike.shop_id == shop_id)
            .options(
                joinedload(BikeSession.customer),
                joinedload(BikeSession.bike),
                joinedload(BikeSession.checkout),
            )
            .order_by(BikeSession.start_datetime.desc())
            .all()
        )

        return [
            {
                "customer": s.customer.name,
                "phone": s.customer.primary_phone,
                "bike": f"{s.bike.nickname} {s.bike_id}",
                "start": s.start_datetime,
                "stop": s.stop_datetime,
                "duration": (
                    f"{s.checkout.duration_in_minutes} minute{"s" if s.checkout.duration_in_minutes > 1 else ""}"
                    if s.checkout
                    else "ongoing"
                ),
                "amount": int(s.checkout.amount_paid) if s.checkout else "ongoing",
            }
            for s in sessions
        ]

    except HTTPException:
        raise
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=422, content={"detail": "Something went wrong."}
        )
