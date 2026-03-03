from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse


from data.db import get_db
from data.models import ShopOwner, Shop
from core import config
from core.security import get_current_user


from sqlalchemy.orm import Session

import logging
import traceback


router = APIRouter()

SETTINGS = config.GlobalSettings()
logger = logging.getLogger(SETTINGS.APP_NAME)


@router.post("/create-shop")
async def create_shop_owner(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:

        if not isinstance(current_user, ShopOwner):
            return JSONResponse(
                status_code=400, content={"detail": "Failed to create shop."}
            )

        payload = await request.json()
        exists = (
            db.query(Shop)
            .filter(
                Shop.owner_id == current_user.id,
                Shop.name == payload["name"].strip(),
                Shop.metadata_e == {"location": payload["location"].strip()},
            )
            .first()
        )
        if exists:
            return JSONResponse(
                status_code=409, content={"detail": "Shop already exists."}
            )
        shop: Shop = Shop(
            name=payload["name"].strip(),
            owner_id=current_user.id,
            metadata_e={"location": payload["location"].strip()},
        )
        db.add(shop)
        db.commit()
        db.refresh(shop)
        return {"detail": "Shop create successful."}
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=422, content={"detail": "Something went wrong."}
        )
