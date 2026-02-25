from fastapi import FastAPI

from fastapi.staticfiles import StaticFiles

from apps.api.middleware.cors import setup_cors


import apps.web.main as web_main


def create_app() -> FastAPI:
    app = FastAPI(title="BIKELEASE Server")

    app.mount("/static", StaticFiles(directory="static"), name="static")

    setup_cors(app)

    app.include_router(web_main.router, prefix="", tags=["web"])

    return app


app = create_app()
