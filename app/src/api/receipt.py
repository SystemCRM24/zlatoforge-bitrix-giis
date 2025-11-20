import asyncio

from fastapi import APIRouter, Query

from src.services.create_scrap_receipt import create_scrap_receipt as _create_scrap_receipt


router = APIRouter(prefix="")


UserIdQuery = Query(default="7780", description="Пользователь по умолчанию Админ Мега")


@router.post("/create_scrap_receipt", status_code=201)
async def create_scrap_receipt(deal_id: str = Query(), user_id: str = UserIdQuery) -> str:
    """Создание квитанции на скупку лома на основе данных битрикса клиента."""
    coro = _create_scrap_receipt(deal_id, user_id)
    asyncio.create_task(coro)
    return "Task created"
