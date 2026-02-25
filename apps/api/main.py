from fastapi import FastAPI


from apps.api.middleware.cors import setup_cors


import apps.web.main as web_main


def create_app() -> FastAPI:
    app = FastAPI(title="BIKELEASE Server")

    setup_cors(app)

    app.include_router(web_main.router, prefix="", tags=["web"])

    return app


app = create_app()
