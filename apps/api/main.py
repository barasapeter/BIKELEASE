import logging
import os

from pathlib import Path

from fastapi import FastAPI


from apps.api.middleware.cors import setup_cors
from fastapi.staticfiles import StaticFiles


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
    queries,
)

from data.models import Base
from data.db import engine
from core import config

SETTINGS = config.GlobalSettings()
BASE_DIR = Path(__file__).resolve().parent

WEB_DIR = BASE_DIR.parent / "web"
STATIC_DIR = WEB_DIR / "static"

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
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    setup_cors(app)

    app.include_router(web_main.router, prefix="", tags=["web"])
    app.include_router(auth.router, prefix="/auth/v1", tags=["auth"])
    app.include_router(shop.router, prefix="/shop/v1", tags=["shop"])
    app.include_router(bikes.router, prefix="/bikes/v1", tags=["bikes"])
    app.include_router(customers.router, prefix="/customers/v1", tags=["customers"])
    app.include_router(payments.router, prefix="/payments/v1", tags=["payments"])
    app.include_router(queries.router, prefix="/queries/v1", tags=["queries"])
    app.include_router(reports.router, prefix="/reports/v1", tags=["reports"])

    init_db()

    return app


app = create_app()
