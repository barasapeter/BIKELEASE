from fastapi import FastAPI


from apps.api.middleware.cors import setup_cors


import apps.web.main as web_main

from data.models import Base
from data.db import engine


def init_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    Base.metadata.drop_all(bind=engine)


def create_app() -> FastAPI:
    app = FastAPI(title="BIKELEASE Server")

    setup_cors(app)

    app.include_router(web_main.router, prefix="", tags=["web"])

    init_db()

    return app


app = create_app()
