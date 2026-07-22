import sys
from datetime import datetime

sys.path.insert(0, '/app')

from giis_integration_core.webhook_handler.bitrix_client import BitrixClient

bitrix = BitrixClient()

# Ваши реальные коды полей из Битрикс24
FIELD_STATUS = "UF_CRM_1784644065"       # Статус интеграции ГИИС
FIELD_RECEIPT_ID = "UF_CRM_1784644084"   # Номер квитанции ГИИС
FIELD_LAST_SYNC = "UF_CRM_1784644417"    # Время последней синхронизации
FIELD_ERROR_MSG = "UF_CRM_1784644639"    # Сообщение об ошибке ГИИС

async def notify_success(entity_type_id: int, item_id: int, receipt_id: str, method_name: str = "Операция"):
    """Уведомляет об успешной отправке данных в ГИИС ДМДК."""
    try:
        if entity_type_id == 0:
            # Работаем со Сделкой
            update_fields = {
                FIELD_STATUS: "✅ Успешно",
                FIELD_RECEIPT_ID: receipt_id,
                FIELD_LAST_SYNC: datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                FIELD_ERROR_MSG: "" # Очищаем поле ошибки
            }
            await bitrix.update_deal(item_id, update_fields)
            
            comment = f"✅ {method_name} успешно выполнена!\nНомер документа в ГИИС ДМДК: **{receipt_id}**"
            await bitrix.add_comment_to_deal(item_id, comment)
        else:
            # Работаем со Смарт-процессом (если понадобится)
            update_fields = {
                FIELD_STATUS: "✅ Успешно",
                FIELD_RECEIPT_ID: receipt_id,
                FIELD_LAST_SYNC: datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                FIELD_ERROR_MSG: ""
            }
            await bitrix.update_smart_process_item(entity_type_id, item_id, update_fields)
            comment = f"✅ {method_name} успешно выполнена!\nНомер документа в ГИИС ДМДК: **{receipt_id}**"
            await bitrix.add_comment(entity_type_id, item_id, comment)
        
        print(f"✅ Уведомление об успехе отправлено для карточки #{item_id}")
        
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления об успехе: {e}")

async def notify_error(entity_type_id: int, item_id: int, error_text: str, method_name: str = "Операция"):
    """Уведомляет об ошибке интеграции."""
    try:
        if entity_type_id == 0:
            update_fields = {
                FIELD_STATUS: " Ошибка",
                FIELD_ERROR_MSG: error_text[:250],
                FIELD_LAST_SYNC: datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            }
            await bitrix.update_deal(item_id, update_fields)
            
            comment = f"❌ Ошибка при выполнении: {method_name}\nПричина: {error_text}"
            await bitrix.add_comment_to_deal(item_id, comment)
        else:
            update_fields = {
                FIELD_STATUS: "❌ Ошибка",
                FIELD_ERROR_MSG: error_text[:250],
                FIELD_LAST_SYNC: datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            }
            await bitrix.update_smart_process_item(entity_type_id, item_id, update_fields)
            comment = f"❌ Ошибка при выполнении: {method_name}\nПричина: {error_text}"
            await bitrix.add_comment(entity_type_id, item_id, comment)
        
        print(f"⚠️ Уведомление об ошибке отправлено для карточки #{item_id}")
        
    except Exception as e:
        print(f"❌ Критическая ошибка при отправке уведомления об ошибке: {e}")