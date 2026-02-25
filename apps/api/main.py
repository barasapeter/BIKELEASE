from fastapi import FastAPI

from apps.api.middleware.cors import setup_cors

# from apps.api.middleware.request_id import setup_request_id
# from apps.api.middleware.error_handlers import setup_error_handlers

# from apps.api.routers import health, auth, bikes, customers, rentals, payments, reports

import apps.web.main as web_main


def create_app() -> FastAPI:
    app = FastAPI(title="BIKELEASE Server")

    setup_cors(app)
    # setup_request_id(app)
    # setup_error_handlers(app)

    # app.include_router(health.router)
    # app.include_router(auth.router, prefix="/auth", tags=["auth"])
    # app.include_router(bikes.router, prefix="/bikes", tags=["bikes"])
    # app.include_router(customers.router, prefix="/customers", tags=["customers"])
    # app.include_router(rentals.router, prefix="/rentals", tags=["rentals"])
    # app.include_router(payments.router, prefix="/payments", tags=["payments"])
    # app.include_router(reports.router, prefix="/reports", tags=["reports"])

    app.include_router(web_main.router, prefix="", tags=["web"])

    return app


app = create_app()
