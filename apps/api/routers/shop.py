from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse


from data.db import get_db
from data.models import ShopOwner, Employee, Customer, Shop
from core import config
from core.security import hash_pin, verify_pin, get_current_user


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
    # user_id: UUID = Depends(get_current_user),
):
    try:
        payload = await request.json()

        return {"detail": "Register successful."}
    except Exception:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=422, content={"detail": "Something went wrong."}
        )
