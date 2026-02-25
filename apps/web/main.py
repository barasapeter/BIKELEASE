from pathlib import Path
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent

router.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


@router.get("/")
def main():
    return {"message": "Hello, from Speedy!"}
