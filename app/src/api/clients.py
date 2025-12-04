import asyncio

from fastapi import APIRouter, Query

from src.schemas.queries import ContactQuerySchema
from src.services.check_bitrix_contact import check_bitrix_contact


router = APIRouter(prefix="")


@router.post("/check_contact")
async def check_contact(q: ContactQuerySchema = Query()):
    """Метод для получения сведений о причастности лиа к экстремизму или терорризму."""
    coro = check_bitrix_contact(q.contact_id, q.user_id)
    asyncio.create_task(coro)
    return "Task created"
