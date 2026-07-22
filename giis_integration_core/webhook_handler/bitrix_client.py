import os
import aiohttp
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

B24_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK")
if not B24_WEBHOOK_URL:
    raise ValueError("КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения BITRIX_WEBHOOK не задана в файле .env")

class BitrixClient:
    """
    Универсальный клиент для взаимодействия с REST API Битрикс24.
    Использует входящий вебхук для авторизации.
    """
    def __init__(self, webhook_url: str = B24_WEBHOOK_URL):
        self.webhook_url = webhook_url.rstrip('/') + '/'

    async def call_method(self, method: str, params: dict = None):
        """Базовый метод для отправки любого REST-запроса в Битрикс24"""
        url = f"{self.webhook_url}{method}.json"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params or {}) as response:
                result = await response.json()
                if 'error' in result:
                    raise Exception(f"Ошибка Битрикс24: {result.get('error')} - {result.get('error_description')}")
                return result.get('result')

    # ==========================================================
    # БЛОК 1: СДЕЛКИ (CRM Deal)
    # ==========================================================
    async def get_deal(self, deal_id: int):
        """Получает данные Сделки по её ID"""
        return await self.call_method('crm.deal.get', {'id': deal_id})

    async def update_deal(self, deal_id: int, fields: dict):
        """Обновляет поля Сделки"""
        return await self.call_method('crm.deal.update', {
            'id': deal_id,
            'fields': fields
        })

    # ==========================================================
    # БЛОК 2: КОНТАКТЫ (CRM Contact)
    # ==========================================================
    async def get_contact(self, contact_id: int):
        """Получает данные Контакта по его ID"""
        return await self.call_method('crm.contact.get', {'id': contact_id})

    async def update_contact(self, contact_id: int, fields: dict):
        """Обновляет поля Контакта"""
        return await self.call_method('crm.contact.update', {
            'id': contact_id,
            'fields': fields
        })

    # ==========================================================
    # БЛОК 3: СМАРТ-ПРОЦЕССЫ И СПИСКИ (CRM Item)
    # ==========================================================
    async def get_smart_process_item(self, entity_type_id: int, item_id: int):
        """Получает данные карточки Смарт-процесса или Списка по ID"""
        return await self.call_method('crm.item.get', {
            'entityTypeId': entity_type_id,
            'id': item_id
        })

    async def update_smart_process_item(self, entity_type_id: int, item_id: int, fields: dict):
        """Обновляет поля карточки Смарт-процесса или Списка"""
        return await self.call_method('crm.item.update', {
            'entityTypeId': entity_type_id,
            'id': item_id,
            'fields': fields
        })

       # ==========================================================
    # БЛОК 4: КОММЕНТАРИИ И УВЕДОМЛЕНИЯ (Timeline)
    # ==========================================================
    async def add_comment(self, entity_type_id: int, item_id: int, comment: str):
        """Добавляет комментарий в ленту карточки Смарт-процесса"""
        return await self.call_method('crm.item.comment.add', {
            'entityTypeId': entity_type_id,
            'itemId': item_id,
            'comment': comment
        })  # ← ЭТА СКОБКА ВАЖНА! Закрывает словарь параметров

    async def add_comment_to_deal(self, deal_id: int, comment: str):
        """Добавляет комментарий в ленту Сделки"""
        return await self.call_method('crm.timeline.comment.add', {
            'entityType': 'deal',
            'entityId': deal_id,
            'comment': comment
        })