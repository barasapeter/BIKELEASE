from fastapi import APIRouter

router: APIRouter = APIRouter()


@router.get("/")
def main():
    return {"message": "Hello, from BIKELEASE!"}
