from fast_bitrix24 import BitrixAsync

from src.core import settings
from src.schemas.bitrix import BitrixClient


BX = BitrixAsync(webhook=settings.BITRIX_WEBHOOK, verbose=False)


class BitrixRepository:
    """Репозиторий для работы с битриксом"""

    @staticmethod
    async def get_bitrix_contact(contact_id: str) -> BitrixClient:
        """Получить контакт по ID"""
        contact_info: dict = await BX.call("crm.contact.get", {"id": contact_id}, raw=True)
        return BitrixClient.model_validate(contact_info.get("result", {}))

    @staticmethod
    async def send_notification(message: str, user_id: str | None = None):
        """Отправляет уведомление пользователю"""
        if user_id is None:
            user_id = settings.DEFAULT_USER
        items = {"USER_ID": user_id, "MESSAGE": message}
        return await BX.call("im.notify.personal.add", items)
