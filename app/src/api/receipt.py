import asyncio

from fastapi import APIRouter

from src.services.create_scrap_receipt import create_scrap_receipt as _create_scrap_receipt


router = APIRouter(prefix="")


@router.post("/create_scrap_receipt", status_code=201)
async def create_scrap_receipt() -> str:
    """Создание квитанции на скупку лома на основе данных битрикса клиента."""
    coro = _create_scrap_receipt()
    asyncio.create_task(coro)
    return "Task created"
