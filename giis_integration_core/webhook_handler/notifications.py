import os
from datetime import datetime
import httpx

# Получаем URL вебхука из переменных окружения (загружается из .env)
B24_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK", "")

async def notify_success(deal_id: int, receipt_id: str, service_type: str):
    """Асинхронно записывает успешный результат в сделку Битрикс24"""
    if not B24_WEBHOOK_URL:
        print("⚠️ BITRIX_WEBHOOK не задан в .env, обновление пропущено")
        return
        
    url = f"{B24_WEBHOOK_URL}crm.deal.update.json"
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    payload = {
        "id": deal_id,
        "fields": {
            "UF_CRM_1784644065": "✅ Успешно",
            "UF_CRM_1784644084": receipt_id,
            "UF_CRM_1784644417": now,
            "UF_CRM_1784644639": ""
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            res_json = response.json()
            if res_json.get("result"):
                print(f"✅ Поля сделки {deal_id} успешно обновлены.")
                await add_comment(deal_id, f"✅ <b>ГИИС ДМДК ({service_type})</b><br>Квитанция: <b>{receipt_id}</b><br>Время: {now}")
            else:
                print(f"❌ Ошибка Битрикс24 при обновлении: {res_json.get('error_description')}")
    except Exception as e:
        print(f"⚠️ Исключение при обновлении Битрикс24: {e}")

async def notify_error(deal_id: int, error_msg: str, service_type: str):
    """Асинхронно записывает ошибку в сделку Битрикс24"""
    if not B24_WEBHOOK_URL:
        print("⚠️ BITRIX_WEBHOOK не задан в .env, обновление пропущено")
        return
        
    url = f"{B24_WEBHOOK_URL}crm.deal.update.json"
    
    payload = {
        "id": deal_id,
        "fields": {
            "UF_CRM_1784644065": "❌ Ошибка",
            "UF_CRM_1784644639": error_msg[:250]
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=10.0)
            await add_comment(deal_id, f"❌ <b>ГИИС ДМДК ({service_type})</b><br>Ошибка: {error_msg}")
    except Exception as e:
        print(f"⚠️ Исключение при записи ошибки в Битрикс24: {e}")

async def add_comment(deal_id: int, message: str):
    """Асинхронно добавляет комментарий в ленту сделки"""
    try:
        url = f"{B24_WEBHOOK_URL}crm.timeline.comment.add.json"
        payload = {
            "fields": {
                "ENTITY_TYPE": "deal",
                "ENTITY_ID": deal_id,
                "COMMENT": message
            }
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            res_json = response.json()
            if res_json.get("result"):
                print(f"💬 Комментарий успешно добавлен в ленту сделки {deal_id}.")
            else:
                print(f"⚠️ Не удалось добавить комментарий: {res_json.get('error_description')}")
    except Exception as e:
        print(f"️ Исключение при добавлении комментария: {e}")