from fastapi import APIRouter


router = APIRouter(prefix="", tags=["Common"])


@router.get("/ping", status_code=200)
async def ping() -> str:
    return "Pong"
