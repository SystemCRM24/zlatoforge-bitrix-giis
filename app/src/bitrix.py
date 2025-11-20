from fast_bitrix24 import BitrixAsync

from src.core import settings
from src.schemas.bitrix import ContactSchema, DealSchema, DMDKSmartProcessSchema


BX = BitrixAsync(webhook=settings.BITRIX_WEBHOOK, verbose=False)


class BitrixRepository:
    """Репозиторий для работы с битриксом"""

    @staticmethod
    async def get_bitrix_contact(contact_id: str) -> ContactSchema:
        """Получить контакт по ID"""
        contact_info: dict = await BX.call("crm.contact.get", {"id": contact_id}, raw=True)
        return ContactSchema.model_validate(contact_info.get("result", {}))

    @staticmethod
    async def get_deal(deal_id: str) -> DealSchema:
        """Получение сделки по id"""
        result = await BX.call("crm.deal.get", {"id": deal_id}, raw=True)
        deal = result.get("result", {})
        return DealSchema.model_validate(deal)

    @staticmethod
    async def get_dmdks_from_deal(deal_id: str) -> list[DMDKSmartProcessSchema]:
        """Получение связанных со сделкой смарт-процессов ДМДК."""
        _filter = {"PARENT_ID_2": deal_id}
        # 157 - ид смарт процесса ДМДК
        items = {"entityTypeId": 157, "select": ["*"], "filter": _filter, "useOriginalUfNames": "Y"}
        result = await BX.call("crm.item.list", items, raw=True)
        raw_sps: list[dict] = result.get("result", {}).get("items", [])
        return [DMDKSmartProcessSchema.model_validate(raw_sp) for raw_sp in raw_sps]

    @staticmethod
    async def send_notification(message: str, user_id: str | None = None):
        """Отправляет уведомление пользователю"""
        if user_id is None:
            user_id = settings.DEFAULT_USER
        # user_id может прийти в таком формате, поэтому надо его преобразовать
        if user_id.startswith("user"):
            user_id = user_id[5:]
        items = {"USER_ID": user_id, "MESSAGE": message}
        return await BX.call("im.notify.personal.add", items)
