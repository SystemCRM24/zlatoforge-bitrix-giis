import asyncio

from fastapi import APIRouter

from src.services.check_bitrix_contact import check_bitrix_contact


router = APIRouter(prefix="")


@router.get("/check_contact")
async def check_contact(clinet_id: str, user_id: str | None = None):
    """Метод для получения сведений о причастности лиа к экстремизму или терорризму."""
    coro = check_bitrix_contact(clinet_id, user_id)
    asyncio.create_task(coro)
