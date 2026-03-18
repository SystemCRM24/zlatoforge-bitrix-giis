import json

from fast_bitrix24 import BitrixAsync

from src.core import settings
from src.schemas.bitrix import ContactSchema, DealSchema, DMDKULSchema


BX = BitrixAsync(webhook=settings.BITRIX_WEBHOOK, verbose=False)


class BitrixRepository:
    """Репозиторий для работы с битриксом"""

    @staticmethod
    async def get_bitrix_contact(contact_id: str) -> ContactSchema:
        """Получить контакт по ID"""
        contact_info: dict = await BX.call("crm.contact.get", {"id": contact_id}, raw=True)
        contact = contact_info.get("result", {})
        return ContactSchema.model_validate(contact)

    @staticmethod
    async def get_deal(deal_id: str) -> DealSchema:
        """Получение сделки по id"""
        result = await BX.call("crm.deal.get", {"id": deal_id}, raw=True)
        deal = result.get("result", {})
        return DealSchema.model_validate(deal)

    @staticmethod
    async def send_notification(message: str, user_id: str | None = None):
        """Отправляет уведомление пользователю"""
        # user_id может прийти в таком формате, поэтому надо его преобразовать
        if isinstance(user_id, str) and user_id.startswith("user"):
            user_id = user_id[5:]
        if not user_id:
            user_id = settings.DEFAULT_USER
        items = {"USER_ID": user_id, "MESSAGE": message}
        return await BX.call("im.notify.personal.add", items)

    @staticmethod
    async def get_dmdk_lists_element_from_deal(deal_id: str) -> list[DMDKULSchema]:
        """Получение дмдк из универсальных списков"""
        _filter = {"=PROPERTY_274": [deal_id]}
        items = {"IBLOCK_TYPE_ID": "lists", "IBLOCK_ID": "64", "FILTER": _filter}
        result = await BX.call("lists.element.get", items, raw=True)
        raw_dmdks: list = result.get("result", [])
        return [DMDKULSchema.model_validate(raw_dmdk) for raw_dmdk in raw_dmdks]

    @staticmethod
    async def update_dmdk_ulist_fields():
        """Обновляет описание полей универсального списка по учету дм"""
        items = {"IBLOCK_TYPE_ID": "lists", "IBLOCK_ID": "64"}
        result = await BX.call("lists.field.get", items, raw=True)
        with open("logs/dmdk_list.json", "w") as f:
            json.dump(result.get("result", {}), f, indent=2, ensure_ascii=False)
        # print(result)
