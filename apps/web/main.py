from pathlib import Path


from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from core import config
from integrations.mpesa import client as mpesa_client

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
SETTINGS = config.GlobalSettings()

router.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


@router.get("/")
async def main():
    phone_number = "2541140684259"
    amount_to_pay = "50"
    response = await mpesa_client.initiate_stk_push(
        phone=phone_number,
        amount=amount_to_pay,
        callback_url="htps://mucra.pythonanywhere.com",
    )
    return {"initiate": response.get("detail")}


@router.get("/hi")
async def main():
    return {"greetings": "hi!"}
