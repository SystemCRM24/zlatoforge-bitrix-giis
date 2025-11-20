import asyncio

from fastapi import APIRouter, Query

from src.services.check_bitrix_contact import check_bitrix_contact


router = APIRouter(prefix="")


@router.post("/check_contact")
async def check_contact(client_id: str = Query(), user_id: str = Query()):
    """Метод для получения сведений о причастности лиа к экстремизму или терорризму."""
    coro = check_bitrix_contact(client_id, user_id)
    asyncio.create_task(coro)
    return "Task created"
