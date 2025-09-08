from fastapi import APIRouter


router = APIRouter(prefix="", tags=["common"])


@router.get('/ping', status_code=200)
async def ping() -> str:
    return 'Pong'
