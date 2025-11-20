import asyncio

from fastapi import APIRouter, Query

from src.services.check_bitrix_contact import check_bitrix_contact


router = APIRouter(prefix="")


UserIdQuery = Query(default="7780", description="Пользователь по умолчанию Админ Мега")


@router.post("/check_contact")
async def check_contact(contact_id: str = Query(), user_id: str = UserIdQuery):
    """Метод для получения сведений о причастности лиа к экстремизму или терорризму."""
    coro = check_bitrix_contact(contact_id, user_id)
    asyncio.create_task(coro)
    return "Task created"
