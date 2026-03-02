import logging
import os

from fastapi import FastAPI


from apps.api.middleware.cors import setup_cors


import apps.web.main as web_main
from apps.api.routers import (
    auth,
    customers,
    bikes,
    health,
    payments,
    rentals,
    reports,
    shop,
)

from data.models import Base
from data.db import engine
from core import config

SETTINGS = config.GlobalSettings()

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(SETTINGS.APP_NAME)


def init_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    Base.metadata.drop_all(bind=engine)


def create_app() -> FastAPI:
    app = FastAPI(
        title="BIKELEASE Server",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    setup_cors(app)

    app.include_router(web_main.router, prefix="", tags=["web"])
    app.include_router(auth.router, prefix="/auth/v1", tags=["auth"])
    app.include_router(shop.router, prefix="/shop/v1", tags=["shop"])

    init_db()

    return app


app = create_app()
