from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse


from data.db import get_db
from data.models import ShopOwner, Employee, Customer
from core import config


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
        return {"status": "ok", "payload": payload}
    except:
        logger.error(f"{request.url.path}\n{traceback.format_exc()}\n\n")
        return JSONResponse(
            status_code=500, content={"detail": "Something went wrong."}
        )
